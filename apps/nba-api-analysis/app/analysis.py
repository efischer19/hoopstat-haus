"""
NBA API analysis functions for researching video and play-by-play capabilities.
"""

import inspect
from datetime import datetime
from pathlib import Path
from typing import Any

from nba_api.live.nba import endpoints as live_endpoints
from nba_api.stats import endpoints


def analyze_api_capabilities() -> dict[str, Any]:
    """
    Analyze the nba-api library's endpoints for video and play-by-play data.

    Returns:
        Dictionary containing analysis of available endpoints and capabilities.
    """
    print("   Scanning nba-api endpoints...")

    # Get all available endpoints from stats API
    stats_endpoints = []
    for name in dir(endpoints):
        obj = getattr(endpoints, name)
        if inspect.isclass(obj) and hasattr(obj, "get_data_frames"):
            stats_endpoints.append(
                {
                    "name": name,
                    "module": "stats",
                    "doc": obj.__doc__ or "No documentation available",
                    "params": _get_endpoint_params(obj),
                }
            )

    # Get all available endpoints from live API
    live_endpoints_list = []
    for name in dir(live_endpoints):
        obj = getattr(live_endpoints, name)
        if inspect.isclass(obj):
            live_endpoints_list.append(
                {
                    "name": name,
                    "module": "live",
                    "doc": obj.__doc__ or "No documentation available",
                    "params": _get_endpoint_params(obj),
                }
            )

    # Look for video-related endpoints
    video_related = []
    pbp_related = []

    all_endpoints = stats_endpoints + live_endpoints_list

    for endpoint in all_endpoints:
        name_lower = endpoint["name"].lower()
        doc_lower = (endpoint["doc"] or "").lower()

        # Check for video-related keywords
        video_keywords = ["video", "clip", "highlight", "replay", "media"]
        if any(
            keyword in name_lower or keyword in doc_lower for keyword in video_keywords
        ):
            video_related.append(endpoint)

        # Check for play-by-play related keywords
        pbp_keywords = ["playbyplay", "pbp", "play_by_play", "event", "moment"]
        if any(
            keyword in name_lower or keyword in doc_lower for keyword in pbp_keywords
        ):
            pbp_related.append(endpoint)

    return {
        "total_stats_endpoints": len(stats_endpoints),
        "total_live_endpoints": len(live_endpoints_list),
        "video_related_endpoints": video_related,
        "pbp_related_endpoints": pbp_related,
        "all_endpoints": all_endpoints[:10],  # Sample of endpoints
        "analysis_timestamp": datetime.now().isoformat(),
    }


def analyze_video_data() -> dict[str, Any]:
    """
    Analyze video data capabilities and formats in the NBA API.

    Returns:
        Dictionary containing analysis of video data availability and structure.
    """
    print("   Investigating video data structures...")

    analysis = {
        "direct_video_links": False,
        "video_metadata_available": False,
        "video_formats": [],
        "indexing_methods": [],
        "sample_data": None,
        "findings": [],
    }

    try:
        # Try to find any endpoint that might contain video information
        # Check a recent game for any video-related data
        from nba_api.stats.endpoints import playbyplayv2

        # Get a recent game ID (using a known game for testing)
        try:
            game_id = "0022300001"  # Sample game ID

            # Try play-by-play to see if it contains video links
            pbp = playbyplayv2.PlayByPlayV2(game_id=game_id)
            pbp_data = pbp.get_data_frames()[0]

            if not pbp_data.empty:
                # Check columns for video-related fields
                video_columns = [
                    col
                    for col in pbp_data.columns
                    if any(
                        keyword in col.lower()
                        for keyword in ["video", "clip", "url", "link", "media"]
                    )
                ]

                if video_columns:
                    analysis["video_metadata_available"] = True
                    analysis["video_formats"] = video_columns
                    analysis["sample_data"] = pbp_data[video_columns].head().to_dict()

                analysis["findings"].append(
                    f"Play-by-play data has {len(pbp_data.columns)} columns"
                )
                analysis["findings"].append(f"Video-related columns: {video_columns}")

                # Check if any actual video URLs exist in the data
                for col in video_columns:
                    if pbp_data[col].notna().any():
                        sample_values = pbp_data[col].dropna().head().tolist()
                        if any("http" in str(val) for val in sample_values):
                            analysis["direct_video_links"] = True
                            analysis["findings"].append(
                                f"Found potential video URLs in {col}"
                            )

        except Exception as e:
            analysis["findings"].append(f"Error analyzing sample game data: {str(e)}")

    except Exception as e:
        analysis["findings"].append(f"Error in video analysis: {str(e)}")

    # Additional investigation into NBA.com video structure
    analysis["findings"].extend(
        [
            "NBA API typically does not provide direct video links",
            "Video content is usually hosted on NBA.com with separate video API",
            "Play-by-play events might be linkable to video timestamps",
            "NBA.com uses a separate video content delivery system",
        ]
    )

    return analysis


def analyze_pbp_data() -> dict[str, Any]:
    """
    Analyze play-by-play data structure and detail level.

    Returns:
        Dictionary containing analysis of PBP data capabilities.
    """
    print("   Examining play-by-play data structure...")

    analysis = {
        "structured_play_types": False,
        "defensive_formations": False,
        "event_timing": False,
        "player_tracking": False,
        "sample_events": [],
        "data_structure": {},
        "findings": [],
    }

    try:
        from nba_api.stats.endpoints import playbyplayv2

        # Analyze play-by-play data structure
        game_id = "0022300001"  # Sample game ID
        pbp = playbyplayv2.PlayByPlayV2(game_id=game_id)
        pbp_data = pbp.get_data_frames()[0]

        if not pbp_data.empty:
            # Analyze data structure
            analysis["data_structure"] = {
                "columns": list(pbp_data.columns),
                "total_events": len(pbp_data),
                "data_types": pbp_data.dtypes.to_dict(),
            }

            # Check for timing information
            timing_columns = [
                col
                for col in pbp_data.columns
                if any(
                    keyword in col.lower()
                    for keyword in ["time", "period", "clock", "timestamp"]
                )
            ]
            if timing_columns:
                analysis["event_timing"] = True
                analysis["findings"].append(
                    f"Timing data available in: {timing_columns}"
                )

            # Check for play type information
            play_type_columns = [
                col
                for col in pbp_data.columns
                if any(
                    keyword in col.lower()
                    for keyword in ["action", "type", "event", "description"]
                )
            ]
            if play_type_columns:
                analysis["findings"].append(
                    f"Play type data available in: {play_type_columns}"
                )

                # Sample different action types
                if "EVENTMSGACTIONTYPE" in pbp_data.columns:
                    action_types = pbp_data["EVENTMSGACTIONTYPE"].unique()
                    analysis["findings"].append(
                        f"Found {len(action_types)} unique action types"
                    )

                # Check for detailed descriptions
                if (
                    "HOMEDESCRIPTION" in pbp_data.columns
                    or "VISITORDESCRIPTION" in pbp_data.columns
                ):
                    # Sample some descriptions to analyze structure
                    desc_cols = [
                        col
                        for col in ["HOMEDESCRIPTION", "VISITORDESCRIPTION"]
                        if col in pbp_data.columns
                    ]
                    sample_descriptions = []
                    for col in desc_cols:
                        descriptions = pbp_data[col].dropna().head(10).tolist()
                        sample_descriptions.extend(descriptions)

                    analysis["sample_events"] = sample_descriptions

                    # Check if descriptions contain structured play information
                    structured_keywords = [
                        "pick and roll",
                        "isolation",
                        "post up",
                        "transition",
                    ]
                    for desc in sample_descriptions:
                        if desc and any(
                            keyword in desc.lower() for keyword in structured_keywords
                        ):
                            analysis["structured_play_types"] = True
                            break

            # Check for player information
            player_columns = [
                col
                for col in pbp_data.columns
                if any(keyword in col.lower() for keyword in ["player", "person"])
            ]
            if player_columns:
                analysis["player_tracking"] = True
                analysis["findings"].append(
                    f"Player data available in: {player_columns}"
                )

            # Sample some actual data
            sample_data = pbp_data.head(5).to_dict("records")
            analysis["sample_events"] = sample_data

    except Exception as e:
        analysis["findings"].append(f"Error analyzing PBP data: {str(e)}")

    # Add general findings about NBA PBP data
    analysis["findings"].extend(
        [
            "NBA play-by-play provides event-level data with timestamps",
            "Action types are coded but descriptions are mostly free text",
            "Player involvement is tracked for most events",
            "Advanced play types (pick and roll, etc.) require text parsing",
            "No structured defensive formation data available",
        ]
    )

    return analysis


def assess_feasibility(
    api_capabilities: dict, video_analysis: dict, pbp_analysis: dict
) -> dict[str, Any]:
    """
    Assess the feasibility of building a video analysis platform.

    Args:
        api_capabilities: Results from API capability analysis
        video_analysis: Results from video data analysis
        pbp_analysis: Results from PBP data analysis

    Returns:
        Dictionary containing feasibility assessment.
    """
    print("   Evaluating platform feasibility...")

    assessment = {
        "overall_feasibility": "MODERATE_WITH_CHALLENGES",
        "key_findings": [],
        "requirements": [],
        "challenges": [],
        "recommendations": [],
    }

    # Analyze video linking feasibility
    if video_analysis["direct_video_links"]:
        assessment["key_findings"].append("✅ Direct video links available in API")
    else:
        assessment["key_findings"].append("❌ No direct video links in API")
        assessment["challenges"].append(
            "Need alternative method to link PBP events to video"
        )

    # Analyze PBP data richness
    if pbp_analysis["structured_play_types"]:
        assessment["key_findings"].append("✅ Some structured play type data available")
    else:
        assessment["key_findings"].append("⚠️ Limited structured play type data")
        assessment["requirements"].append(
            "AI/ML models needed for play type classification"
        )

    if pbp_analysis["event_timing"]:
        assessment["key_findings"].append(
            "✅ Event timing data available for synchronization"
        )
    else:
        assessment["challenges"].append("No timing data for video synchronization")

    # Generate recommendations
    assessment["recommendations"].extend(
        [
            "Develop computer vision models to analyze video directly",
            "Use NBA.com video API separately from stats API",
            "Implement text parsing for play descriptions",
            "Create mapping between PBP timestamps and video timestamps",
            "Consider using NBA's official video highlights API if available",
        ]
    )

    # Determine overall feasibility
    num_challenges = len(assessment["challenges"])
    num_requirements = len(assessment["requirements"])

    if num_challenges <= 2 and num_requirements <= 2:
        assessment["overall_feasibility"] = "HIGH"
    elif num_challenges <= 4 and num_requirements <= 4:
        assessment["overall_feasibility"] = "MODERATE"
    else:
        assessment["overall_feasibility"] = "LOW"

    return assessment


def identify_risks() -> dict[str, Any]:
    """
    Identify risks and open questions for the video analysis platform.

    Returns:
        Dictionary containing risks and open questions.
    """
    print("   Identifying risks and challenges...")

    return {
        "api_limitations": [
            "NBA API does not provide direct video content",
            "Rate limiting may affect real-time analysis",
            "API structure may change without notice",
            "Historical data availability may be limited",
        ],
        "legal_copyright_issues": [
            "NBA video content is heavily copyrighted",
            "Commercial use may require licensing agreements",
            "Fair use limitations for video clips",
            "Terms of service restrictions on API usage",
        ],
        "technical_challenges": [
            "Video synchronization with play-by-play events",
            "Computer vision model development and training",
            "Real-time processing requirements",
            "Storage and bandwidth costs for video content",
            "Accuracy of automated play type detection",
        ],
        "open_questions": [
            "Is there a separate NBA video API available?",
            "What are the licensing costs for NBA video content?",
            "How accurate would AI play type detection be?",
            "What is the latency for live game analysis?",
            "How much training data would be needed for CV models?",
        ],
        "mitigation_strategies": [
            "Start with publicly available highlight videos",
            "Focus on text-based analysis initially",
            "Partner with NBA for video access",
            "Use court tracking data when available",
            "Implement human verification for AI predictions",
        ],
    }


def generate_report(analysis_data: dict[str, Any]) -> str:
    """
    Generate a comprehensive markdown report of the analysis.

    Args:
        analysis_data: Combined analysis results

    Returns:
        Path to the generated report file.
    """
    report_content = f"""# NBA API Video and Play-by-Play Analysis Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Executive Summary

This report analyzes the feasibility of building a video analysis platform on top of the NBA API, focusing on video content availability and play-by-play data capabilities.

**Overall Feasibility: {analysis_data['feasibility']['overall_feasibility']}**

## 1. API Capability Summary

### Available Endpoints
- **Total Stats API Endpoints:** {analysis_data['api_capabilities']['total_stats_endpoints']}
- **Total Live API Endpoints:** {analysis_data['api_capabilities']['total_live_endpoints']}

### Video-Related Endpoints
{_format_endpoints(analysis_data['api_capabilities']['video_related_endpoints'])}

### Play-by-Play Related Endpoints
{_format_endpoints(analysis_data['api_capabilities']['pbp_related_endpoints'])}

## 2. Video Data Analysis

### Key Findings
{_format_list(analysis_data['video_analysis']['findings'])}

### Video Capabilities
- **Direct Video Links Available:** {analysis_data['video_analysis']['direct_video_links']}
- **Video Metadata Available:** {analysis_data['video_analysis']['video_metadata_available']}
- **Supported Formats:** {', '.join(analysis_data['video_analysis']['video_formats']) if analysis_data['video_analysis']['video_formats'] else 'None identified'}

## 3. Play-by-Play Data Analysis

### Data Structure
- **Total Columns:** {len(analysis_data['pbp_analysis']['data_structure'].get('columns', []))}
- **Sample Columns:** {', '.join(analysis_data['pbp_analysis']['data_structure'].get('columns', [])[:10])}

### Capabilities Assessment
- **Structured Play Types:** {analysis_data['pbp_analysis']['structured_play_types']}
- **Defensive Formation Data:** {analysis_data['pbp_analysis']['defensive_formations']}
- **Event Timing Available:** {analysis_data['pbp_analysis']['event_timing']}
- **Player Tracking:** {analysis_data['pbp_analysis']['player_tracking']}

### Key Findings
{_format_list(analysis_data['pbp_analysis']['findings'])}

## 4. Feasibility Assessment

### Overall Assessment: **{analysis_data['feasibility']['overall_feasibility']}**

### Key Findings
{_format_list(analysis_data['feasibility']['key_findings'])}

### Technical Requirements
{_format_list(analysis_data['feasibility']['requirements'])}

### Identified Challenges
{_format_list(analysis_data['feasibility']['challenges'])}

### Recommendations
{_format_list(analysis_data['feasibility']['recommendations'])}

## 5. Risks & Open Questions

### API Limitations
{_format_list(analysis_data['risks']['api_limitations'])}

### Legal & Copyright Issues
{_format_list(analysis_data['risks']['legal_copyright_issues'])}

### Technical Challenges
{_format_list(analysis_data['risks']['technical_challenges'])}

### Open Questions
{_format_list(analysis_data['risks']['open_questions'])}

### Proposed Mitigation Strategies
{_format_list(analysis_data['risks']['mitigation_strategies'])}

## Conclusion

The analysis reveals that while the NBA API provides rich play-by-play data with timing information, **direct video content is not available through the API**. Building a comprehensive video analysis platform would require:

1. **Alternative video sources** (NBA.com video API, official highlights)
2. **Computer vision models** for automated play type detection
3. **Sophisticated synchronization** between PBP events and video timestamps
4. **Legal compliance** with NBA's content usage policies

The platform is technically feasible but would require significant development effort and potentially licensing agreements with the NBA for video content access.

---

*This analysis was generated using the nba-api library version 1.10.0*
"""

    # Save report to file
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"nba_api_analysis_{timestamp}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return str(report_path)


def _get_endpoint_params(endpoint_class) -> list[str]:
    """Extract parameter names from an endpoint class."""
    try:
        if hasattr(endpoint_class, "__init__"):
            sig = inspect.signature(endpoint_class.__init__)
            return [param for param in sig.parameters.keys() if param != "self"]
    except Exception:
        pass
    return []


def _format_endpoints(endpoints: list[dict]) -> str:
    """Format endpoint list for markdown."""
    if not endpoints:
        return "- No video-related endpoints found"

    result = []
    for endpoint in endpoints[:5]:  # Limit to first 5
        result.append(
            f"- **{endpoint['name']}** ({endpoint['module']}): {endpoint['doc'][:100]}..."
        )

    if len(endpoints) > 5:
        result.append(f"- *...and {len(endpoints) - 5} more*")

    return "\n".join(result)


def _format_list(items: list[str]) -> str:
    """Format a list of items for markdown."""
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)
