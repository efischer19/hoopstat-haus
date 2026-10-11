# feat: End-to-end smoke test and v1 sign-off

## What do you want to build?

A comprehensive end-to-end validation that the entire hoopstat.haus v1 system is working correctly from the new repositories. This is the final gate before archiving the old repository.

## Acceptance Criteria

- [ ] **Data pipeline:** Bronze ingestion runs on schedule and produces data
- [ ] **Data pipeline:** Silver processing transforms bronze data correctly
- [ ] **Data pipeline:** Gold analytics produces served artifacts
- [ ] **Data pipeline:** Health aggregator produces fresh `pipeline_health.json`
- [ ] **Data pipeline:** DB compiler produces DuckDB and SQLite artifacts
- [ ] **Frontend:** `https://hoopstat.haus` loads the main dashboard with fresh data
- [ ] **Frontend:** Charts render correctly with real NBA statistics
- [ ] **Frontend:** Health dashboard shows healthy pipeline status
- [ ] **Frontend:** All pages pass Lighthouse performance/accessibility audits
- [ ] **Infrastructure:** All AWS resources are healthy (no CloudWatch alarms firing)
- [ ] **Infrastructure:** CloudFront cache is working (check hit/miss headers)
- [ ] **CI/CD:** hoopstat-data CI pipeline passes on main branch
- [ ] **CI/CD:** hoopstat-app CI pipeline passes on main branch
- [ ] **CI/CD:** A test PR to hoopstat-data triggers CI and passes
- [ ] **CI/CD:** A test PR to hoopstat-app triggers CI and passes
- [ ] **MCP proxy:** Package is installable from PyPI and functional
- [ ] **DNS:** `hoopstat.haus` resolves to the new CloudFront distribution
- [ ] **SSL:** Certificate is valid and no mixed content warnings
- [ ] **Monitoring:** CloudWatch metrics show healthy patterns over 24+ hours

## Implementation Notes (Optional)

**This is the sign-off ticket.** It doesn't create anything new — it validates everything that's been built across all previous epics.

**Validation timeline:**
This ticket should remain open for at least **48 hours** after the DNS cutover to ensure stability across multiple pipeline runs and varying traffic patterns.

**Validation checklist execution:**
Walk through each acceptance criterion manually. For automated checks, use:
- `curl -s -o /dev/null -w "%{http_code}" https://hoopstat.haus` — Verify site is up
- Browser DevTools — Check for errors, verify data loading
- AWS Console — Check CloudWatch, S3, Lambda, CloudFront metrics
- GitHub — Check workflow run history for both repos

**Known acceptable differences from old system:**
Document any intentional differences between the old hoopstat-haus system and the new v1 deployment. For example:
- Different S3 bucket names
- Different CloudFront distribution ID
- Different OIDC role ARNs
- New repository structure

**Sign-off process:**
1. Complete all acceptance criteria checks
2. Document results in a PR or issue comment
3. Get human sign-off that v1 is ready
4. Proceed to Epic 8 (Archive/Teardown)

**If issues are found:**
- Critical issues: Fix immediately, re-validate
- Non-critical issues: Create follow-up tickets in the appropriate repo
- If a critical issue cannot be fixed: Rollback DNS to old infrastructure and investigate
