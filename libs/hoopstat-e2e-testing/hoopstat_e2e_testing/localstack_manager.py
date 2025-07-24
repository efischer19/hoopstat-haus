"""
Localstack lifecycle management for testing.

Manages Localstack container lifecycle and health checks for integration testing.
"""

import logging
import time

import docker
import requests
from docker.errors import APIError, NotFound

logger = logging.getLogger(__name__)


class LocalstackManager:
    """Manages Localstack container for testing."""

    def __init__(
        self,
        container_name: str = "localstack-test",
        image: str = "localstack/localstack:3.8",
        ports: dict | None = None,
        environment: dict | None = None,
    ):
        """
        Initialize Localstack manager.

        Args:
            container_name: Name of the Localstack container
            image: Docker image to use for Localstack
            ports: Port mappings for the container
            environment: Environment variables for the container
        """
        self.container_name = container_name
        self.image = image
        self.ports = ports or {"4566/tcp": 4566}
        self.environment = environment or {
            "SERVICES": "s3",
            "DEBUG": "1",
            "PERSISTENCE": "0",
            "DISABLE_CORS_CHECKS": "1",
            "DISABLE_CUSTOM_CORS_S3": "1",
            "S3_SKIP_SIGNATURE_VALIDATION": "1",
            "EAGER_SERVICE_LOADING": "1",
        }

        self.docker_client = docker.from_env()
        self.container = None

    def start(self, timeout: int = 60) -> bool:
        """
        Start Localstack container.

        Args:
            timeout: Maximum time to wait for container to be ready

        Returns:
            True if container started successfully, False otherwise
        """
        try:
            # Check if container already exists
            try:
                existing_container = self.docker_client.containers.get(
                    self.container_name
                )
                if existing_container.status == "running":
                    logger.info(
                        f"Localstack container already running: {self.container_name}"
                    )
                    self.container = existing_container
                    return True
                else:
                    logger.info(f"Removing stopped container: {self.container_name}")
                    existing_container.remove()
            except NotFound:
                pass

            # Start new container
            logger.info(f"Starting Localstack container: {self.container_name}")
            self.container = self.docker_client.containers.run(
                self.image,
                name=self.container_name,
                ports=self.ports,
                environment=self.environment,
                detach=True,
                remove=False,
            )

            # Wait for container to be ready
            if self.wait_for_ready(timeout):
                logger.info(f"Localstack container ready: {self.container_name}")
                return True
            else:
                logger.error(
                    f"Localstack container failed to start: {self.container_name}"
                )
                return False

        except APIError as e:
            logger.error(f"Docker API error starting Localstack: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop and remove Localstack container.

        Returns:
            True if container stopped successfully, False otherwise
        """
        try:
            if self.container:
                logger.info(f"Stopping Localstack container: {self.container_name}")
                self.container.stop()
                self.container.remove()
                self.container = None
                return True
            else:
                logger.info("No Localstack container to stop")
                return True
        except APIError as e:
            logger.error(f"Error stopping Localstack container: {e}")
            return False

    def wait_for_ready(self, timeout: int = 60) -> bool:
        """
        Wait for Localstack to be ready to accept requests.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if Localstack is ready, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:4566/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    s3_status = health_data.get("services", {}).get("s3", "")
                    if s3_status.lower() == "running":
                        logger.info("Localstack S3 service is ready")
                        return True
                    else:
                        logger.debug(f"S3 service not ready yet: {health_data}")
            except requests.exceptions.RequestException as e:
                logger.debug(f"Health check failed: {e}")

            time.sleep(2)

        logger.error("Localstack failed to become ready within timeout")
        return False

    def is_running(self) -> bool:
        """
        Check if Localstack container is running.

        Returns:
            True if container is running, False otherwise
        """
        try:
            if self.container:
                self.container.reload()
                return self.container.status == "running"
            else:
                # Try to find existing container
                try:
                    container = self.docker_client.containers.get(self.container_name)
                    return container.status == "running"
                except NotFound:
                    return False
        except APIError:
            return False

    def get_logs(self) -> str:
        """
        Get logs from Localstack container.

        Returns:
            Container logs as string
        """
        try:
            if self.container:
                return self.container.logs().decode("utf-8")
            else:
                return "No container available"
        except APIError as e:
            logger.error(f"Error getting container logs: {e}")
            return f"Error getting logs: {e}"

    def __enter__(self):
        """Context manager entry."""
        if self.start():
            return self
        else:
            raise RuntimeError("Failed to start Localstack container")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
