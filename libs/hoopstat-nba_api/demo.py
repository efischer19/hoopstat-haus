#!/usr/bin/env python3
"""
Demo script showing usage of the hoopstat-nba_api library.

This script demonstrates how to use the NBA API client with rate limiting
to fetch NBA data in a respectful manner.
"""

from hoopstat_nba_api import NBAClient, RateLimiter


def main():
    """Demonstrate NBA API client usage."""
    print("🏀 NBA API Client Demo")
    print("=" * 40)

    # Initialize client with default rate limiter
    print("1. Creating NBA client with default rate limiter...")
    client = NBAClient()
    print("   ✅ Client created successfully")

    # Create client with custom rate limiter
    print("\n2. Creating NBA client with custom rate limiter...")
    custom_limiter = RateLimiter(
        min_delay=2.0,  # 2 seconds minimum between requests
        max_delay=120.0,  # 2 minutes maximum delay
        max_retries=3,  # Fewer retries for demo
    )
    NBAClient(rate_limiter=custom_limiter)
    print("   ✅ Custom client created successfully")

    # Demonstrate rate limiting
    print("\n3. Rate limiter configuration:")
    limiter = client.rate_limiter
    print(f"   • Min delay: {limiter.min_delay}s")
    print(f"   • Max delay: {limiter.max_delay}s")
    print(f"   • Max retries: {limiter.max_retries}")
    print(f"   • Backoff factor: {limiter.backoff_factor}")

    print("\n📝 Example usage:")
    print("   # Fetch games for a specific date")
    print("   games = client.get_games_for_date(date(2024, 1, 15))")
    print()
    print("   # Get player information")
    print('   player = client.get_player_info("2544")  # LeBron James')
    print()
    print("   # Get league standings")
    print('   standings = client.get_league_standings("2023-24")')

    print("\n🚀 Ready to use! The client will automatically:")
    print("   • Respect API rate limits")
    print("   • Retry failed requests with exponential backoff")
    print("   • Log detailed information for debugging")


if __name__ == "__main__":
    main()
