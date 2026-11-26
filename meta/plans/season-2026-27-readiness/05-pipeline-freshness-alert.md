# feat: Alert when the pipeline stops producing fresh data

## What do you want to build?

Bronze ingestion on the Pi failed every day from 2026-03-10 until 2026-10-10, and nothing noticed. The daily Build Database job stayed green the whole time. During the season, a stale pipeline should be loud.

Add a scheduled GitHub Actions workflow that checks data freshness and **fails** (GitHub emails the workflow owner on scheduled-run failures) when the pipeline is stale.

## Acceptance Criteria

- [ ] New workflow runs daily after the pipeline and Build Database (e.g. 13:00 UTC) and supports `workflow_dispatch`
- [ ] Fails if bronze `_metadata/summary.json` `last_successful_run` is older than ~30 hours
- [ ] Fails if `https://hoopstat.haus/index/latest.json` `latest_date` lags the most recent date with completed NBA games by more than 1 day; dates with no games (All-Star break, off days) must not cause false alarms
- [ ] Off-season (between the Finals and the next opener) the game-based check is skipped and only the bronze heartbeat is enforced
- [ ] The job summary prints the bronze last-run time, `latest_date`, and the expected date
- [ ] Verified once by dispatching it against current state (should fail today and pass after ticket 01 / Oct 21)

## Implementation Notes (Optional)

- "Most recent date with completed games" can come from `cdn.nba.com`'s static schedule JSON, or from `nba_api`'s `ScheduleLeagueV2` (current headers required; GitHub-hosted IPs may be blocked by stats.nba.com, so prefer the CDN or treat API failure as "unknown, don't fail"). Count only regular-season and postseason game IDs (`002`, `004`, `005`, `006`).
- Bronze writes `_metadata/summary.json` even on no-game days, so its heartbeat stays fresh in the off-season as long as the Pi is alive.
- Reading the bronze bucket needs AWS credentials (OIDC, like `build-database.yml`); `latest.json` is public.
- Keep it simple. No Slack or SNS; a failed scheduled run plus GitHub's email is enough.
