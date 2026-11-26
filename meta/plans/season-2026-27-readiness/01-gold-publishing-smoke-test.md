# feat: Smoke-test gold publishing end to end by replaying 2026-03-10

## What do you want to build?

Prove, before the Oct 20 opener, that the full S3-triggered chain publishes public data, and fix whatever breaks.

Gold's JSON-artifact publishing (`served/player_daily`, `team_daily`, `top_lists`, `index/latest.json`; added in #615 on 2026-03-15) has **never run on real data**. The last bronze/silver/gold data is from 2026-03-10, five days before that code merged. The first real exercise would otherwise be the morning of Oct 21.

Replay a single known-good date through silver (which writes a `silver-ready` marker, which triggers gold, which writes `served/index/latest.json`, which triggers the health aggregator), then run Build Database, and verify each public output.

## Acceptance Criteria

- [ ] Silver replay for `2026-03-10` succeeds (`gh workflow run silver-processing.yml -f date=2026-03-10`)
- [ ] Gold Lambda logs for that invocation show no errors, and `served/player_daily/2026-03-10/`, `served/team_daily/2026-03-10/` and `served/top_lists/2026-03-10/` exist in the gold bucket
- [ ] `https://hoopstat.haus/index/latest.json` returns 200 with `"latest_date": "2026-03-10"`, and a sample `player_daily` artifact is fetchable through CloudFront
- [ ] The health aggregator ran (CloudWatch logs) and its output under `served/health/` is fetchable
- [ ] A manually dispatched Build Database run compiles and uploads `served/db/nba_current_season.duckdb` and `.sqlite`; both download from `https://hoopstat.haus/db/` and `SELECT count(*) FROM player_season_summary` (or the equivalent daily table) works in DuckDB
- [ ] Any bugs found are fixed in this PR, or filed as separate issues if they're large

## Implementation Notes (Optional)

- Needs AWS access for log and S3 inspection (`aws login`); triggering is via GitHub Actions (OIDC).
- Replaying 2026-03-10 leaves `latest.json` pointing at March 10 until real data arrives Oct 21. That's harmless and expected.
- The gold Lambda was last deployed by #963 (or earlier); confirm the deployed image includes #615+ (`aws lambda get-function --function-name hoopstat-haus-gold-analytics`, compare `LastModified`).
- Watch the 5-minute gold Lambda timeout and the CloudFront 403-for-missing-object behavior (OAC returns 403, not 404, for keys that don't exist).
- If gold fails, ticket 04 (season summaries) and the Oct 21 go/no-go both depend on this, so prioritize accordingly.
