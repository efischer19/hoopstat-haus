"""Tests for the Hoopstat HTTP client."""

import httpx
import pytest
import respx

from app.http_client import ArtifactFetchError, HoopstatClient

BASE_URL = "https://test.example.com"


class TestHoopstatClient:
    """Test suite for HoopstatClient."""

    @pytest.fixture
    def client(self):
        """Create a client with test base URL."""
        return HoopstatClient(BASE_URL)

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_index_success(self, client):
        """Test successful index fetch."""
        index_data = '{"date": "2024-11-15", "datasets": {}}'
        respx.get(f"{BASE_URL}/index/latest.json").mock(
            return_value=httpx.Response(200, text=index_data)
        )

        result = await client.fetch_index()
        assert result == index_data

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_index_404(self, client):
        """Test 404 response for index raises ArtifactFetchError."""
        respx.get(f"{BASE_URL}/index/latest.json").mock(
            return_value=httpx.Response(404)
        )

        with pytest.raises(ArtifactFetchError, match="Resource not found"):
            await client.fetch_index()

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_index_server_error(self, client):
        """Test 500 response raises ArtifactFetchError."""
        respx.get(f"{BASE_URL}/index/latest.json").mock(
            return_value=httpx.Response(500)
        )

        with pytest.raises(ArtifactFetchError, match="Unexpected status 500"):
            await client.fetch_index()

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_artifact_success(self, client):
        """Test successful artifact fetch."""
        player_data = '{"player_id": 2544, "points": 30}'
        respx.get(f"{BASE_URL}/player_daily/2024-11-15/2544.json").mock(
            return_value=httpx.Response(200, text=player_data)
        )

        result = await client.fetch_artifact("player_daily/2024-11-15/2544")
        assert result == player_data

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_artifact_with_json_extension(self, client):
        """Test artifact fetch when URI already includes .json extension."""
        player_data = '{"player_id": 2544}'
        respx.get(f"{BASE_URL}/player_daily/2024-11-15/2544.json").mock(
            return_value=httpx.Response(200, text=player_data)
        )

        result = await client.fetch_artifact("player_daily/2024-11-15/2544.json")
        assert result == player_data

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_artifact_404(self, client):
        """Test 404 when player ID not found."""
        respx.get(f"{BASE_URL}/player_daily/2024-11-15/9999.json").mock(
            return_value=httpx.Response(404)
        )

        with pytest.raises(ArtifactFetchError, match="Resource not found") as exc_info:
            await client.fetch_artifact("player_daily/2024-11-15/9999")
        assert exc_info.value.status_code == 404

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_artifact_strips_slashes(self, client):
        """Test that leading/trailing slashes are stripped from resource URIs."""
        data = '{"team_id": 1610612747}'
        respx.get(f"{BASE_URL}/team_daily/2024-11-15/1610612747.json").mock(
            return_value=httpx.Response(200, text=data)
        )

        result = await client.fetch_artifact("/team_daily/2024-11-15/1610612747/")
        assert result == data

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_connection_error(self, client):
        """Test connection error is wrapped in ArtifactFetchError."""
        respx.get(f"{BASE_URL}/index/latest.json").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(ArtifactFetchError, match="Could not connect"):
            await client.fetch_index()

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_timeout_error(self, client):
        """Test timeout is wrapped in ArtifactFetchError."""
        respx.get(f"{BASE_URL}/index/latest.json").mock(
            side_effect=httpx.ReadTimeout("Read timed out")
        )

        with pytest.raises(ArtifactFetchError, match="Request timed out"):
            await client.fetch_index()

    def test_base_url_trailing_slash_stripped(self):
        """Test that trailing slashes on base URL are stripped."""
        client = HoopstatClient("https://example.com/")
        assert client.base_url == "https://example.com"

    def test_artifact_fetch_error_attributes(self):
        """Test ArtifactFetchError stores status_code."""
        error = ArtifactFetchError("not found", status_code=404)
        assert str(error) == "not found"
        assert error.status_code == 404

    def test_artifact_fetch_error_no_status(self):
        """Test ArtifactFetchError without status_code."""
        error = ArtifactFetchError("connection failed")
        assert error.status_code is None
