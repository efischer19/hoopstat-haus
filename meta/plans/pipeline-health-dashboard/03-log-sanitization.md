# Ticket 3: Implement Log Sanitization & Security Hardening

**Title:** `feat: Implement log sanitization and security hardening for health aggregator`

**Labels:** `enhancement`

---

## What do you want to build?

Implement the security-critical sanitization layer in the health aggregator Lambda (Ticket 2) that ensures zero internal AWS metadata, secrets, stack traces, or infrastructure details leak into the public `pipeline_health.json` artifact.

This is the most security-sensitive component of the health dashboard epic. The sanitizer acts as a strict allowlist filter between raw AWS telemetry and the public JSON output, enforcing the "No Stack Trace Rule" and all other security constraints defined in ADR-040.

### Sanitization Strategy: Allowlist, Not Denylist

The sanitizer uses an **allowlist approach** — only explicitly permitted fields and values are included in the output. This is fundamentally safer than a denylist approach (trying to strip known-bad patterns) because new types of sensitive data are excluded by default.

### Sanitization Rules

1. **Status Fields** — Only permitted enum values (`success`, `failed`, `skipped`, `no_data`, `operational`, `degraded`, `outage`). Any other string is replaced with `failed`.

2. **Timestamps** — Only ISO 8601 UTC strings. Internal timezone information or non-standard formats are rejected.

3. **Numeric Fields** — Only non-negative integers (counts) and floats in [0.0, 1.0] (quality scores). Any value outside the expected range is clamped or zeroed.

4. **Secret Detection** — Scan the serialized JSON output for patterns matching:
   - AWS access key IDs (`AKIA...`)
   - AWS secret keys (40-character base64 strings adjacent to key identifiers)
   - AWS session tokens (`FwoGZX...`)
   - ARN patterns (`arn:aws:...`)
   - Internal IP addresses (RFC 1918 ranges: `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x`)
   - Common secret patterns (Bearer tokens, API keys with known prefixes)

   If any pattern is detected, the **entire payload is rejected** and a minimal fallback JSON is written instead:
   ```json
   {
     "schema_version": "1.0.0",
     "generated_at": "2026-03-26T06:00:00Z",
     "overall_status": "degraded",
     "stages": {},
     "daily_summaries": [],
     "_sanitization_note": "Payload rejected by security filter"
   }
   ```

5. **Stack Trace Filtering** — CloudWatch query results are parsed for status outcomes only. Raw log messages, exception text, and traceback strings are never included in the compiled output.

6. **Infrastructure Metadata Stripping** — Lambda request IDs, log stream names, container IDs, memory usage, and billed duration are never included.

7. **Execution Window Obfuscation** — Only completion timestamps are retained. Start times, durations, and inter-stage timing gaps are discarded.

---

## Acceptance Criteria

- [ ] A `sanitizer.py` module is added to `apps/health-aggregator/app/` implementing the allowlist sanitization logic
- [ ] The sanitizer validates all output fields against strict type and range constraints before JSON serialization
- [ ] A secret-detection scan runs on the final serialized JSON string before writing to S3
- [ ] If secrets or disallowed patterns are detected, the entire payload is rejected and a safe fallback JSON is written
- [ ] No stack traces, error messages, or raw log lines appear in any valid `pipeline_health.json` output
- [ ] No internal AWS metadata (ARNs, internal IPs, Lambda request IDs, log stream names, bucket names) appears in the output
- [ ] No start times or durations are included — only completion timestamps
- [ ] Unit tests cover: clean payloads pass through, payloads with injected AWS keys are rejected, payloads with ARNs are rejected, payloads with internal IPs are rejected, payloads with out-of-range values are clamped, enum fields reject unknown values
- [ ] A dedicated security-focused test file (`tests/test_sanitizer.py`) validates all sanitization rules with adversarial test cases
- [ ] The sanitizer logs a warning (to CloudWatch, not to the public JSON) when it rejects a payload, for operational debugging

---

## Implementation Notes (Optional)

- The allowlist approach means the sanitizer constructs the output from scratch using only validated fields, rather than trying to strip bad content from a pre-built object. This is a key architectural decision — the Pydantic model validation (Ticket 1) provides the first layer, and the sanitizer provides the second.
- Use `re` (regex) for secret pattern detection. Compile patterns once at module level for performance.
- The fallback JSON must itself be a valid `PipelineHealthReport` per the Pydantic schema (Ticket 1), so the sanitizer must also validate the fallback before writing.
- Reference ADR-040 security constraints section for the authoritative list of security requirements.
- **Dependency on Ticket 2:** This ticket modifies the aggregator Lambda created in Ticket 2 by replacing the placeholder sanitization step with the full implementation.
- Consider adding a `--dry-run` mode to the sanitizer that outputs the sanitization decisions (what was kept, what was stripped) to CloudWatch logs for debugging, without writing to S3.
