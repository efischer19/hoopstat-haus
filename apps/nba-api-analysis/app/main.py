"""
NBA API Analysis Application for Hoopstat Haus.

This application analyzes the NBA API's video and play-by-play capabilities
to determine the feasibility of building a video analysis platform.
"""

from .analysis import (
    analyze_api_capabilities,
    analyze_pbp_data,
    analyze_video_data,
    assess_feasibility,
    generate_report,
    identify_risks,
)


def main() -> None:
    """Main entry point for the NBA API analysis application."""
    print("🏀 NBA API Analysis for Hoopstat Haus")
    print("=" * 50)

    print("\n1. Analyzing API capabilities...")
    api_capabilities = analyze_api_capabilities()

    print("\n2. Analyzing video data...")
    video_analysis = analyze_video_data()

    print("\n3. Analyzing play-by-play data...")
    pbp_analysis = analyze_pbp_data()

    print("\n4. Assessing feasibility...")
    feasibility = assess_feasibility(api_capabilities, video_analysis, pbp_analysis)

    print("\n5. Identifying risks and open questions...")
    risks = identify_risks()

    print("\n6. Generating comprehensive report...")
    report_path = generate_report(
        {
            "api_capabilities": api_capabilities,
            "video_analysis": video_analysis,
            "pbp_analysis": pbp_analysis,
            "feasibility": feasibility,
            "risks": risks,
        }
    )

    print(f"\n✅ Analysis complete! Report generated at: {report_path}")


if __name__ == "__main__":
    main()
