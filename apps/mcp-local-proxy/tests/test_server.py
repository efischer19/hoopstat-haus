"""Tests for the MCP server tools."""

from unittest.mock import AsyncMock, patch

import pytest

from app.http_client import DEFAULT_BASE_URL, get_client
from app.server import get_artifact, get_index


class TestGetClient:
    """Tests for the get_client helper."""

    def test_default_base_url(self):
        """Test that default base URL is used when env var is not set."""
        with patch.dict("os.environ", {}, clear=True):
            client = get_client()
            assert client.base_url == DEFAULT_BASE_URL

    def test_custom_base_url_from_env(self):
        """Test that HOOPSTAT_BASE_URL env var overrides the default."""
        custom_url = "https://custom.example.com"
        with patch.dict("os.environ", {"HOOPSTAT_BASE_URL": custom_url}):
            client = get_client()
            assert client.base_url == custom_url


class TestGetIndexTool:
    """Tests for the get_index MCP tool."""

    @pytest.mark.asyncio
    async def test_get_index_success(self):
        """Test successful index retrieval returns JSON content."""
        index_json = '{"date": "2024-11-15", "datasets": {}}'
        with patch("app.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_index.return_value = index_json
            mock_get_client.return_value = mock_client

            result = await get_index()
            assert result == index_json
            mock_client.fetch_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_index_error(self):
        """Test index fetch error returns formatted error message."""
        from app.http_client import ArtifactFetchError

        with patch("app.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_index.side_effect = ArtifactFetchError(
                "Could not connect to data source"
            )
            mock_get_client.return_value = mock_client

            result = await get_index()
            assert result.startswith("Error:")
            assert "Could not connect" in result


class TestGetArtifactTool:
    """Tests for the get_artifact MCP tool."""

    @pytest.mark.asyncio
    async def test_get_artifact_success(self):
        """Test successful artifact retrieval."""
        player_json = '{"player_id": 2544, "points": 30}'
        with patch("app.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_artifact.return_value = player_json
            mock_get_client.return_value = mock_client

            result = await get_artifact("player_daily/2024-11-15/2544")
            assert result == player_json
            mock_client.fetch_artifact.assert_called_once_with(
                "player_daily/2024-11-15/2544"
            )

    @pytest.mark.asyncio
    async def test_get_artifact_not_found(self):
        """Test 404 error returns formatted error message."""
        from app.http_client import ArtifactFetchError

        with patch("app.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_artifact.side_effect = ArtifactFetchError(
                "Resource not found: 'player_daily/2024-11-15/9999'",
                status_code=404,
            )
            mock_get_client.return_value = mock_client

            result = await get_artifact("player_daily/2024-11-15/9999")
            assert result.startswith("Error:")
            assert "not found" in result

    @pytest.mark.asyncio
    async def test_get_artifact_connection_error(self):
        """Test connection error returns formatted error message."""
        from app.http_client import ArtifactFetchError

        with patch("app.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_artifact.side_effect = ArtifactFetchError(
                "Could not connect to data source"
            )
            mock_get_client.return_value = mock_client

            result = await get_artifact("player_daily/2024-11-15/2544")
            assert "Error:" in result
