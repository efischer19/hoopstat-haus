"""HTTP client for fetching Hoopstat Haus JSON artifacts from CloudFront."""

import httpx


class ArtifactFetchError(Exception):
    """Raised when an artifact cannot be fetched from the data source."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class HoopstatClient:
    """HTTP client for retrieving NBA statistics artifacts from CloudFront.

    Translates resource URIs into HTTP GET requests against the static
    JSON artifacts served by the Hoopstat Haus CloudFront distribution.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def fetch_index(self) -> str:
        """Fetch the latest.json index listing all available datasets.

        Returns:
            The raw JSON string of the index document.

        Raises:
            ArtifactFetchError: If the index cannot be retrieved.
        """
        url = f"{self.base_url}/index/latest.json"
        return await self._fetch(url, "index")

    async def fetch_artifact(self, resource_uri: str) -> str:
        """Fetch a specific JSON artifact by its resource URI.

        Args:
            resource_uri: Path to the artifact, e.g. "player_daily/2024-11-15/2544".
                The ".json" extension is appended automatically if not present.

        Returns:
            The raw JSON string of the requested artifact.

        Raises:
            ArtifactFetchError: If the artifact cannot be retrieved (e.g. 404).
        """
        path = resource_uri.strip("/")
        if not path.endswith(".json"):
            path = f"{path}.json"
        url = f"{self.base_url}/{path}"
        return await self._fetch(url, resource_uri)

    async def _fetch(self, url: str, resource_label: str) -> str:
        """Perform an HTTP GET and return the response body.

        Args:
            url: The full URL to fetch.
            resource_label: Human-readable label used in error messages.

        Returns:
            The response body as a string.

        Raises:
            ArtifactFetchError: On HTTP errors or connectivity issues.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True)
        except httpx.ConnectError as exc:
            raise ArtifactFetchError(
                f"Could not connect to data source: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ArtifactFetchError(
                f"Request timed out while fetching '{resource_label}': {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ArtifactFetchError(
                f"HTTP error while fetching '{resource_label}': {exc}"
            ) from exc

        if response.status_code == 404:
            raise ArtifactFetchError(
                f"Resource not found: '{resource_label}'",
                status_code=404,
            )
        if response.status_code != 200:
            raise ArtifactFetchError(
                f"Unexpected status {response.status_code} "
                f"while fetching '{resource_label}'",
                status_code=response.status_code,
            )

        return response.text
