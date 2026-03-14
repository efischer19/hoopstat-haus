"""Tests for the CLI commands."""

import json
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from app.cli import cli
from app.http_client import ArtifactFetchError


class TestGetIndexCommand:
    """Tests for the get-index CLI command."""

    def test_get_index_success(self):
        """Test successful index fetch prints pretty-printed JSON."""
        index_data = {"date": "2024-11-15", "datasets": {"players": 30}}
        raw_json = json.dumps(index_data)

        with patch("app.cli.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_index.return_value = raw_json
            mock_get_client.return_value = mock_client

            runner = CliRunner()
            result = runner.invoke(cli, ["get-index"])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output == index_data
            mock_client.fetch_index.assert_called_once()

    def test_get_index_error(self):
        """Test fetch error prints message to stderr and exits non-zero."""
        with patch("app.cli.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_index.side_effect = ArtifactFetchError(
                "Could not connect to data source"
            )
            mock_get_client.return_value = mock_client

            runner = CliRunner()
            result = runner.invoke(cli, ["get-index"])

            assert result.exit_code != 0


class TestGetArtifactCommand:
    """Tests for the get-artifact CLI command."""

    def test_get_artifact_success(self):
        """Test successful artifact fetch prints pretty-printed JSON."""
        player_data = {"player_id": 2544, "points": 30}
        raw_json = json.dumps(player_data)

        with patch("app.cli.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_artifact.return_value = raw_json
            mock_get_client.return_value = mock_client

            runner = CliRunner()
            result = runner.invoke(
                cli, ["get-artifact", "player_daily/2024-11-15/2544"]
            )

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output == player_data
            mock_client.fetch_artifact.assert_called_once_with(
                "player_daily/2024-11-15/2544"
            )

    def test_get_artifact_not_found(self):
        """Test 404 error prints message to stderr and exits non-zero."""
        with patch("app.cli.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.fetch_artifact.side_effect = ArtifactFetchError(
                "Resource not found: 'player_daily/2024-11-15/9999'",
                status_code=404,
            )
            mock_get_client.return_value = mock_client

            runner = CliRunner()
            result = runner.invoke(
                cli, ["get-artifact", "player_daily/2024-11-15/9999"]
            )

            assert result.exit_code != 0

    def test_get_artifact_missing_uri(self):
        """Test missing resource_uri argument shows usage error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["get-artifact"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output


class TestCliHelp:
    """Tests for CLI help output."""

    def test_top_level_help(self):
        """Test top-level --help lists available commands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "get-index" in result.output
        assert "get-artifact" in result.output

    def test_get_index_help(self):
        """Test get-index --help shows description."""
        runner = CliRunner()
        result = runner.invoke(cli, ["get-index", "--help"])

        assert result.exit_code == 0
        assert "data index" in result.output

    def test_get_artifact_help(self):
        """Test get-artifact --help shows description and examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["get-artifact", "--help"])

        assert result.exit_code == 0
        assert "RESOURCE_URI" in result.output
        assert "player_daily" in result.output


class TestMainEntryPoint:
    """Tests for the main() dispatcher."""

    def test_cli_mode_default(self):
        """Test that main() invokes the CLI by default."""
        with patch("app.cli.cli") as mock_cli:
            from app.main import main

            main()
            mock_cli.assert_called_once()

    def test_mcp_mode_flag(self):
        """Test that --mcp flag starts the MCP server."""
        with (
            patch("sys.argv", ["hoopstat-mcp", "--mcp"]),
            patch("app.server.mcp") as mock_mcp,
        ):
            from app.main import main

            main()
            mock_mcp.run.assert_called_once_with(transport="stdio")
