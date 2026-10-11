# 2026-27 Season Readiness: Executive Summary

**Goal:** by the 2026-27 regular-season opener on **Tue Oct 20, 2026**, the backend publishes fresh NBA data every day with no manual steps, independent of the frontend and of the multi-repo migration (#693):

- `https://hoopstat.haus/index/latest.json` and the daily `player_daily/`, `team_daily/`, `top_lists/` JSON artifacts
- `https://hoopstat.haus/db/nba_current_season.duckdb` and `.sqlite`
- season-to-date player and team summaries, regular season only

The first real game data arrives on the morning of **Wed Oct 21** (Pi bronze run at 4:30am ET for Oct 20 games).

## Where things stand (2026-10-10)

| Stage | State |
|---|---|
| Bronze (Raspberry Pi, cron 4:30am ET) | Failed every day since **2026-03-10**: `nba_api` 1.7 headers are silently dropped by stats.nba.com. Fixed in #947 (merged, armv7 image build in progress). |
| Bronze → Silver → Gold (S3-triggered Lambdas) | Worked through 2026-03-10; bronze, silver and gold buckets all have data up to that date. |
| Gold public artifacts (`served/`) | **Never produced.** The JSON-artifact code (#615) merged 2026-03-15, after the last data arrived, so it has never run on real data. |
| Build Database (GitHub Actions, daily) | Green but a no-op: finds no `served/index/latest.json`. Scheduled at 06:00 UTC, *before* the Pi runs. |
| Season summaries | Only produced by gold's CLI (`season-players` / `season-teams`); nothing runs them automatically. |
| Game-type handling | Preseason/playoff games would have been counted as regular season. Fixed in #963 (open). |
| Public data URL | Code and docs say `data.hoopstat.haus`, which doesn't exist. Everything is served from `hoopstat.haus` (single CloudFront distribution, origin `gold/served`). |
| Dependabot / CI | Fixed tonight: `CI OK` is now a required check (#949), piwheels registry declared (#948, follow-up #960). |

## Plan

### Already done or in flight (no issues needed)

- [x] #947: `nba_api` 1.11.4 for bronze (Pi failures)
- [x] #948, #949: Dependabot piwheels registry; required `CI OK` status check
- [ ] #960: Dependabot `insecure-external-code-execution` for bronze, plus a grouped `/libs/*` entry
- [ ] #963: preseason/All-Star excluded in bronze; season totals count only regular season

### Before tip-off: one issue per ticket in this folder

| # | Ticket | Why it matters before Oct 20 | Target |
|---|---|---|---|
| 01 | Gold publishing smoke test (replay 2026-03-10) | Gold's publishing path has never run; find breakage now, not on opening night | Oct 11–12 |
| 02 | `latest.json` never moves backwards | Replays or retries of older dates would repoint the public index at stale data | Oct 12 |
| 02b | Player/team lists in `latest.json` | The frontend (and `hoopstat-app`) builds its selectors from `players`/`teams` in the index, which gold never writes; without them no client can find a player's artifact | Oct 12 |
| 03 | Bronze: one box-score fetch per game | `LeagueGameFinder` returns a row per team, so every box score is fetched twice: double the API load on an endpoint that already blocks clients | Oct 13 |
| 04 | Daily build: season summaries + schedule after the pipeline | Season-to-date stats are never generated; DB builds ~22h stale | Oct 14–15 |
| 05 | Pipeline freshness alert | Bronze failed silently for 7 months; a stale pipeline must notify | Oct 16 |
| 06 | Correct the public data URL everywhere | MCP proxy and docs point at a domain that doesn't exist | Oct 17 |

Order: **01 first**. It may surface bugs that reshape 02–04. 02 and 02b touch the same writer; do them together. 03 is independent and small. 04 depends on 01 (needs working `served/` output). 05 and 06 can be done anytime.

### Manual checklist (not issues)

- [ ] Merge #963 within ~3h of the Pi's 4:30am ET run (armv7 builds take ~2.5h). After merging, cancel #947's push CI run so it can't overwrite `bronze-ingestion-latest` with the unfiltered image.
- [ ] Oct 11 morning on the Pi: `docker images | grep bronze` shows a fresh image; today's log shows `Skipping exhibition schedule rows` (Oct 10 was preseason-only) and no `NBAAPIError`.
- [ ] Merge #960; confirm the next bronze Dependabot job succeeds.
- [ ] `aws login` available for ticket 01 (S3 / Lambda log inspection).
- [ ] Oct 19: dry-run on the Pi: `~/bronze-ingestion-local/run-daily.sh --date 2025-04-13 --dry-run`.
- [ ] **Oct 21 morning (go/no-go):** bronze log for 2026-10-20, silver and gold Lambda logs clean, `https://hoopstat.haus/index/latest.json` shows `"latest_date": "2026-10-20"`, Build Database publishes the DuckDB/SQLite files.
- [ ] After Oct 21: update the README "Project status" table to match reality; delete the stray `handoff_readme_status.md`.

### After tip-off: `../season-2026-27-followups/`

Separate folder so its issues can be created later:

- 07: MCP proxy on `mcp` 2.x, renamed package, published to PyPI (unblocks #959)
- 08: MCP tools a model can actually use (search, leaders, season stats, SQL)
- 09: Backfill 2025-26 public artifacts from existing silver data
- 10: Dependabot merges trigger push CI (GitHub App token)

## Out of scope

- **Frontend** (`frontend-app/`, `hoopstat-app`): its `GOLD_BASE_URL` is still `CLOUDFRONT_DOMAIN_PLACEHOLDER`, a one-line fix whenever frontend work resumes. `hoopstat-app` does not need `hoopstat-data` to go live: it can deploy against this backend (migration tickets 27–28 only need the existing gold bucket and CloudFront distribution IDs) once 02b lands.
- **Multi-repo migration (#693)** and the **uv migration**: "the big refactor". Nothing here should block or be blocked by it.
- **WNBA**, semantic search / GenAI features.

## Risks to watch

- **stats.nba.com client blocking.** It already broke us once. Ticket 05 makes it loud; ticket 03 halves our request volume. Long-term mitigation: keep `nba_api` current (Dependabot now works for bronze).
- **Gold Lambda 5-minute timeout.** The daily path is per-date, so it's fine; season aggregation is kept out of the Lambda (ticket 04).
- **Build Database cost growth.** db-compiler downloads every daily JSON artifact each run; by season's end that's tens of thousands of objects. Fine for October; revisit if the job exceeds ~15 minutes.
- **Single point of failure: the Pi.** If it dies, bronze stops; ticket 05 is what will tell you.
