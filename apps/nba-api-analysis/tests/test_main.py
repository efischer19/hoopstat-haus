"""Tests for the NBA API analysis application."""

from unittest.mock import patch

from app.analysis import (
    _format_endpoints,
    _format_list,
    analyze_api_capabilities,
    analyze_pbp_data,
    analyze_video_data,
    assess_feasibility,
    identify_risks,
)
from app.main import main


def test_analyze_api_capabilities():
    """Test API capabilities analysis."""
    result = analyze_api_capabilities()

    assert isinstance(result, dict)
    assert "total_stats_endpoints" in result
    assert "total_live_endpoints" in result
    assert "video_related_endpoints" in result
    assert "pbp_related_endpoints" in result
    assert "analysis_timestamp" in result

    # Should find some endpoints
    assert result["total_stats_endpoints"] > 0
    assert result["total_live_endpoints"] > 0


def test_analyze_video_data():
    """Test video data analysis."""
    result = analyze_video_data()

    assert isinstance(result, dict)
    assert "direct_video_links" in result
    assert "video_metadata_available" in result
    assert "video_formats" in result
    assert "findings" in result

    # Should have findings even if no data
    assert len(result["findings"]) > 0


def test_analyze_pbp_data():
    """Test play-by-play data analysis."""
    result = analyze_pbp_data()

    assert isinstance(result, dict)
    assert "structured_play_types" in result
    assert "defensive_formations" in result
    assert "event_timing" in result
    assert "player_tracking" in result
    assert "findings" in result

    # Should have findings even if no data
    assert len(result["findings"]) > 0


def test_assess_feasibility():
    """Test feasibility assessment."""
    # Mock input data
    api_caps = {"total_stats_endpoints": 100, "video_related_endpoints": []}
    video_analysis = {"direct_video_links": False, "video_metadata_available": False}
    pbp_analysis = {"structured_play_types": False, "event_timing": True}

    result = assess_feasibility(api_caps, video_analysis, pbp_analysis)

    assert isinstance(result, dict)
    assert "overall_feasibility" in result
    assert "key_findings" in result
    assert "requirements" in result
    assert "challenges" in result
    assert "recommendations" in result

    # Should have valid feasibility rating
    valid_ratings = ["HIGH", "MODERATE", "LOW", "MODERATE_WITH_CHALLENGES"]
    assert result["overall_feasibility"] in valid_ratings


def test_identify_risks():
    """Test risk identification."""
    result = identify_risks()

    assert isinstance(result, dict)
    assert "api_limitations" in result
    assert "legal_copyright_issues" in result
    assert "technical_challenges" in result
    assert "open_questions" in result
    assert "mitigation_strategies" in result

    # Should have content in each category
    for category in result.values():
        assert len(category) > 0


def test_format_list():
    """Test list formatting utility."""
    # Empty list
    assert _format_list([]) == "- None"

    # Single item
    assert _format_list(["test"]) == "- test"

    # Multiple items
    result = _format_list(["item1", "item2"])
    assert "- item1" in result
    assert "- item2" in result


def test_format_endpoints():
    """Test endpoint formatting utility."""
    # Empty list
    assert _format_endpoints([]) == "- No video-related endpoints found"

    # Single endpoint
    endpoints = [
        {"name": "TestEndpoint", "module": "stats", "doc": "Test documentation"}
    ]
    result = _format_endpoints(endpoints)
    assert "TestEndpoint" in result
    assert "stats" in result


@patch("app.main.generate_report")
@patch("app.main.identify_risks")
@patch("app.main.assess_feasibility")
@patch("app.main.analyze_pbp_data")
@patch("app.main.analyze_video_data")
@patch("app.main.analyze_api_capabilities")
def test_main_runs_without_error(
    mock_api_caps,
    mock_video,
    mock_pbp,
    mock_feasibility,
    mock_risks,
    mock_report,
    capsys,
):
    """Test that main function runs without error and produces output."""
    # Mock return values
    mock_api_caps.return_value = {"total_stats_endpoints": 100}
    mock_video.return_value = {"direct_video_links": False}
    mock_pbp.return_value = {"structured_play_types": False}
    mock_feasibility.return_value = {"overall_feasibility": "MODERATE"}
    mock_risks.return_value = {"api_limitations": ["test"]}
    mock_report.return_value = "test_report.md"

    main()
    captured = capsys.readouterr()

    assert "🏀 NBA API Analysis for Hoopstat Haus" in captured.out
    assert "Analysis complete!" in captured.out
    assert "test_report.md" in captured.out
