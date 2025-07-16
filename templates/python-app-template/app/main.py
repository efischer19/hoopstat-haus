"""
Hello World Python Application Template for Hoopstat Haus.

This is a simple template application that demonstrates the standard
project structure and tooling setup for Python applications in the
Hoopstat Haus project.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any

from app.config import settings


def setup_logging() -> None:
    """Set up structured logging based on configuration."""
    log_level = getattr(logging, settings.log_level.upper())
    
    if settings.log_format == "json":
        # Configure JSON logging
        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        
        # Replace the default formatter with JSON formatter
        for handler in logging.getLogger().handlers:
            handler.setFormatter(JSONFormatter())
    else:
        # Configure text logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add any extra fields from the record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage"
            }:
                log_entry[key] = value
                
        return json.dumps(log_entry)


def get_health_status() -> Dict[str, Any]:
    """
    Get application health status.
    
    Returns:
        Health status information including app info and status.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.app_environment,
        "debug": settings.debug,
    }


def greet(name: str = "World") -> str:
    """
    Generate a greeting message.

    Args:
        name: The name to greet. Defaults to "World".

    Returns:
        A greeting message string.
    """
    return f"Hello, {name}! Welcome to Hoopstat Haus!"


def main() -> None:
    """Main entry point for the application."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(
        "Application starting",
        app_name=settings.app_name,
        app_version=settings.app_version,
        environment=settings.app_environment
    )
    
    try:
        # Display greeting
        message = greet()
        print(message)
        print("This is a template Python application.")
        print("It demonstrates the standard project structure and tooling.")
        
        # Log some example structured data
        logger.info("Application demonstration completed successfully")
        
        # Show health status
        health = get_health_status()
        print(f"\nApplication Health Status:")
        print(json.dumps(health, indent=2))
        
        logger.info("Application completed successfully")
        
    except Exception as e:
        logger.error("Application failed", exception=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
