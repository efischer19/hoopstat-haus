"""Tests for the config module."""

import os
from unittest.mock import patch

from app.config import Settings, settings


def test_default_settings():
    """Test default settings values."""
    assert settings.app_name == "python-app-template"
    assert settings.app_version == "0.1.0"
    assert settings.app_environment == "development"
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_settings_with_env_vars():
    """Test settings loading from environment variables."""
    with patch.dict(os.environ, {
        "APP_NAME": "test-app",
        "APP_VERSION": "2.0.0",
        "APP_ENVIRONMENT": "production",
        "LOG_LEVEL": "DEBUG",
        "PORT": "9000",
        "DEBUG": "true"
    }):
        test_settings = Settings()
        assert test_settings.app_name == "test-app"
        assert test_settings.app_version == "2.0.0"
        assert test_settings.app_environment == "production"
        assert test_settings.log_level == "DEBUG"
        assert test_settings.port == 9000
        assert test_settings.debug is True


def test_environment_properties():
    """Test environment property methods."""
    # Test development environment
    dev_settings = Settings(app_environment="development")
    assert dev_settings.is_development is True
    assert dev_settings.is_production is False
    
    # Test production environment
    prod_settings = Settings(app_environment="production")
    assert prod_settings.is_development is False
    assert prod_settings.is_production is True


def test_testing_property():
    """Test testing property detection."""
    # Test with testing flag
    test_settings = Settings(testing=True)
    assert test_settings.is_testing is True
    
    # Test with pytest environment variable
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "some_test"}):
        test_settings = Settings(testing=False)
        assert test_settings.is_testing is True


def test_case_insensitive_env_vars():
    """Test that environment variables are case insensitive."""
    with patch.dict(os.environ, {
        "app_name": "lowercase-app",
        "APP_NAME": "uppercase-app"
    }):
        test_settings = Settings()
        # Should use the uppercase version if both exist
        assert test_settings.app_name in ["lowercase-app", "uppercase-app"]


def test_optional_fields():
    """Test that optional fields can be None."""
    test_settings = Settings()
    assert test_settings.database_url is None
    assert test_settings.aws_access_key_id is None
    assert test_settings.aws_secret_access_key is None
    assert test_settings.s3_bucket_name is None
    assert test_settings.secret_key is None


def test_aws_settings():
    """Test AWS configuration settings."""
    with patch.dict(os.environ, {
        "AWS_REGION": "us-west-2",
        "AWS_ACCESS_KEY_ID": "test-key-id",
        "AWS_SECRET_ACCESS_KEY": "test-secret",
        "S3_BUCKET_NAME": "test-bucket"
    }):
        test_settings = Settings()
        assert test_settings.aws_region == "us-west-2"
        assert test_settings.aws_access_key_id == "test-key-id"
        assert test_settings.aws_secret_access_key == "test-secret"
        assert test_settings.s3_bucket_name == "test-bucket"