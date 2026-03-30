# feat: Route53 DNS cutover to new infrastructure (human-run)

## What do you want to build?

Update Route53 DNS records to point `hoopstat.haus` to the new CloudFront distribution served from the hoopstat-app deployment. This is a **human-run** task that requires careful timing and verification.

## Acceptance Criteria

- [ ] The new CloudFront distribution is verified working via its `.cloudfront.net` domain (ticket 34)
- [ ] The new data pipeline is verified working and producing data (ticket 36)
- [ ] Route53 A record (or ALIAS) for `hoopstat.haus` is updated to point to the new CloudFront distribution
- [ ] Route53 AAAA record (if exists) is updated similarly
- [ ] Any `www.hoopstat.haus` records are updated to match
- [ ] DNS propagation is verified (check from multiple locations/tools)
- [ ] The site is accessible at `https://hoopstat.haus` with the new deployment
- [ ] SSL/TLS certificate is valid and covers the custom domain
- [ ] No mixed content warnings in the browser

## Implementation Notes (Optional)

**This is explicitly a human-run task.** DNS changes should not be automated due to the risk of downtime.

**Pre-cutover checklist:**
1. ✅ New CloudFront distribution serves the frontend correctly (ticket 34)
2. ✅ Data pipeline is running and gold layer data is fresh (ticket 36)
3. ✅ SSL certificate is associated with the new CloudFront distribution
4. ✅ Old infrastructure is still running (fallback)

**TTL planning:**
Before the cutover:
- Lower the DNS record TTL to 60 seconds (if not already low) at least 24 hours before the cutover
- This ensures fast rollback if something goes wrong

**Cutover procedure:**
1. Verify the new deployment one final time
2. Update the Route53 record
3. Wait for propagation (check with `dig hoopstat.haus`, https://www.whatsmydns.net/, etc.)
4. Verify the site works at the custom domain
5. Monitor for errors for at least 1 hour
6. If issues arise: revert the DNS record to point to the old CloudFront distribution

**Rollback plan:**
- Keep the old Route53 record value documented
- Keep the old infrastructure running (don't tear down until ticket 29)
- If rollback is needed: update the Route53 record back to the old value
- DNS propagation will take up to TTL seconds

**SSL certificate:**
The ACM certificate for `hoopstat.haus` may need to be:
- Reused if it's in the same AWS account and region (us-east-1 for CloudFront)
- Re-created if the new distribution is in a different context
- Verified that the certificate covers both `hoopstat.haus` and `*.hoopstat.haus` (if subdomains are used)
