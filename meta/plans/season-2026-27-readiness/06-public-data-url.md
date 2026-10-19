# feat: Point code and docs at the real public data URL (hoopstat.haus)

## What do you want to build?

Everything public is served by one CloudFront distribution (`aws_cloudfront_distribution.gold_artifacts`, origin `gold/served`) under `hoopstat.haus` / `www.hoopstat.haus`: `index/*`, `db/*`, `health/*`, the per-date artifact prefixes, and the static site. `data.hoopstat.haus` does not exist (no DNS record, not a CloudFront alias), yet it's the default in code and throughout the docs.

Replace `https://data.hoopstat.haus` with `https://hoopstat.haus` everywhere it refers to the public data endpoint.

## Acceptance Criteria

- [ ] `apps/mcp-local-proxy/app/http_client.py` `DEFAULT_BASE_URL` is `https://hoopstat.haus` (still overridable via `HOOPSTAT_BASE_URL`), with tests updated
- [ ] `apps/db-compiler/app/main.py` references updated
- [ ] Docs updated: `README.md`, `apps/mcp-local-proxy/README.md`, `docs-src/DATABASE_GUIDE.md` (check every `git grep -n "data\.hoopstat\.haus"` hit)
- [ ] `git grep "data\.hoopstat\.haus"` returns nothing outside historical ADRs/plans
- [ ] Example URLs in docs match real paths: `https://hoopstat.haus/index/latest.json`, `https://hoopstat.haus/db/nba_current_season.duckdb`, `https://hoopstat.haus/player_daily/{date}/{player_id}.json` (no `served/` prefix in public URLs)
- [ ] Affected app tests pass and ruff is clean

## Implementation Notes (Optional)

- Alternative considered: add `data.hoopstat.haus` as a CloudFront alias (ACM cert SAN + Route 53 record). Not worth it now; one domain is simpler, and the frontend already lives there.
- Don't touch `frontend-app/scripts/app.js` (`GOLD_BASE_URL` placeholder); frontend is out of scope for this plan.
- Leave README status/"not live yet" warnings alone until the Oct 21 go/no-go confirms data is flowing.
