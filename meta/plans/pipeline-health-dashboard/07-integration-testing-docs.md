# Ticket 7: End-to-End Integration Testing & Documentation

**Title:** `feat: End-to-end integration testing and documentation for health dashboard`

**Labels:** `enhancement`

---

## What do you want to build?

Validate the complete health dashboard pipeline end-to-end and create documentation for ongoing maintenance. This ticket is the final gate before the epic is considered complete — it verifies that all components work together and that the security guarantees hold in a realistic scenario.

### Integration Test Scenarios

#### Scenario 1: Happy Path — All Pipelines Operational
- Simulate a successful Bronze → Silver → Gold pipeline run (mock CloudWatch logs, create quarantine files, update `latest.json`).
- Run the aggregator Lambda.
- Verify the output `pipeline_health.json` matches the expected schema, has `overall_status: "operational"`, and contains correct record counts.
- Load `health.html` in a browser and verify all status indicators are green.

#### Scenario 2: Pipeline Failure — Bronze Fails
- Simulate a Bronze ingestion failure (mock CloudWatch logs with error status).
- Run the aggregator Lambda.
- Verify `overall_status: "outage"`, Bronze status is `failed`, Silver and Gold are `skipped` or `no_data`.
- Load `health.html` and verify the Bronze indicator is red and the overall banner reflects outage.

#### Scenario 3: Degraded State — Silver Quarantines
- Simulate a run where Silver processing quarantines a significant number of records.
- Run the aggregator Lambda.
- Verify `overall_status: "degraded"`, quarantine counts are accurate.
- Load `health.html` and verify the chart shows quarantine volume.

#### Scenario 4: Security — Injected Secrets
- Inject an AWS access key pattern into mock CloudWatch log data.
- Run the aggregator Lambda.
- Verify the sanitizer rejects the payload and writes the safe fallback JSON.
- Verify the fallback JSON contains no traces of the injected secret.

#### Scenario 5: Resilience — CloudWatch Unavailable
- Simulate a CloudWatch Logs Insights query timeout.
- Run the aggregator Lambda.
- Verify the aggregator writes a degraded-status JSON rather than failing entirely.

### Documentation Deliverables

1. **README.md for `apps/health-aggregator/`** — Setup instructions, local development guide, environment variables, and testing commands.

2. **Dashboard section in `frontend-app/README.md`** — Brief description of `health.html`, what it displays, and how to test it locally.

3. **Operational runbook addition** — Add a section to the project's documentation describing:
   - How to manually trigger the aggregator for debugging
   - How to interpret the `pipeline_health.json` output
   - What to do if the sanitizer rejects a payload
   - How to verify CloudFront is serving the correct cached version

4. **ADR-040 reference** — Ensure the ADR is linked from the health aggregator README and any relevant infrastructure documentation.

---

## Acceptance Criteria

- [ ] Integration test script covers all 5 scenarios listed above with mocked AWS services
- [ ] All 5 scenarios pass successfully
- [ ] The security scenario (Scenario 4) confirms that injected secrets do NOT appear in any output
- [ ] `apps/health-aggregator/README.md` includes setup, development, and testing instructions
- [ ] `frontend-app/README.md` is updated with a section about the health dashboard
- [ ] An operational runbook section documents manual trigger, output interpretation, and troubleshooting
- [ ] ADR-040 is referenced from the health aggregator README
- [ ] All documentation follows the existing project documentation style (see `apps/` README files for reference)

---

## Implementation Notes (Optional)

- Use `moto` (AWS mock library) for integration tests that simulate CloudWatch, S3, and Lambda interactions. This is consistent with the existing testing approach in the repository.
- Integration tests should live in `apps/health-aggregator/tests/` alongside the unit tests, possibly in a separate `tests/integration/` subdirectory to distinguish them.
- For the browser verification steps (loading `health.html`), a simple approach is to serve `frontend-app/` locally with Python's `http.server` and use a mock `pipeline_health.json` file. Full browser automation (Selenium/Playwright) is out of scope for this ticket.
- The operational runbook can be added as a new section in the existing project documentation (`docs-src/`) or as a standalone file in `meta/` — follow whichever pattern the team prefers.
- **Dependency:** This ticket depends on all previous tickets (1-6) being complete. It is the final verification gate.
- Consider creating a `scripts/test-health-dashboard.sh` convenience script that runs the aggregator with mock data and opens the dashboard in a browser, similar to `scripts/local-ci-check.sh`.
