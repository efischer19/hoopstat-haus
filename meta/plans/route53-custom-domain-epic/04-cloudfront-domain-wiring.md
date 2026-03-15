# Ticket 4: CloudFront & DNS Routing for hoopstat.haus

> **Epic:** [Route 53 Custom Domain](00-executive-summary.md)
> **Sequence:** 4 of 4 — depends on Tickets 1, 2, and 3
> **Related ADRs:** [ADR-010](../../adr/ADR-010-terraform_iac.md), [ADR-035](../../adr/ADR-035-gold_s3_public_access.md), [ADR-038](../../adr/ADR-038-cloudfront-cache-tuning.md), [ADR-039](../../adr/ADR-039-custom-domain-management.md) (Proposed)

---

## What do you want to build?

Wire the validated ACM certificate and custom domain aliases to the existing CloudFront
distribution, then create Route 53 alias records (A and AAAA) for both the apex domain
(`hoopstat.haus`) and `www` subdomain so that browser traffic reaches the CloudFront
distribution. The existing www-to-apex redirect CloudFront Function will activate
automatically.

## Acceptance Criteria

- [ ] The `cloudfront_aliases` variable is set to `["hoopstat.haus", "www.hoopstat.haus"]` (via `terraform.tfvars` or equivalent)
- [ ] The `cloudfront_acm_certificate_arn` variable is set to the validated ACM certificate ARN
- [ ] Route 53 A records (IPv4 alias) are created for `hoopstat.haus` and `www.hoopstat.haus` pointing to the CloudFront distribution
- [ ] Route 53 AAAA records (IPv6 alias) are created for `hoopstat.haus` and `www.hoopstat.haus` pointing to the CloudFront distribution
- [ ] The existing www-to-apex redirect CloudFront Function activates correctly (no new code needed)
- [ ] `https://hoopstat.haus/index/latest.json` resolves and returns the latest index (manual verification after deploy)
- [ ] `https://www.hoopstat.haus/` redirects to `https://hoopstat.haus/` with a 301 (manual verification after deploy)
- [ ] `terraform plan` runs cleanly with no unrelated changes
- [ ] Terraform tests validate the DNS record configurations

## Implementation Notes

### Setting the Variables

The existing CloudFront distribution already supports aliases and ACM certificates via
variables. These values should be set in the Terraform variable configuration (e.g.,
`terraform.tfvars`, environment variables, or the GitHub Actions workflow):

```hcl
cloudfront_aliases             = ["hoopstat.haus", "www.hoopstat.haus"]
cloudfront_acm_certificate_arn = aws_acm_certificate_validation.main.certificate_arn
```

However, since the certificate ARN is a Terraform-managed resource, the cleanest
approach is to wire it directly using a local reference rather than a variable. Consider
updating `main.tf` to pass the validated certificate ARN directly:

```hcl
locals {
  custom_domain_aliases = ["hoopstat.haus", "www.hoopstat.haus"]
  acm_certificate_arn   = aws_acm_certificate_validation.main.certificate_arn
}
```

And updating the CloudFront distribution to use these locals alongside the existing
variable-based approach. The exact wiring strategy should be decided during
implementation.

### Route 53 Alias Records

Create A and AAAA records for both the apex and www subdomain. Route 53 alias records
are special — they don't incur per-query charges and support apex domains (unlike
CNAMEs):

```hcl
# ============================================================================
# Route 53 DNS Records for CloudFront
# ============================================================================

locals {
  cloudfront_domains = toset(["hoopstat.haus", "www.hoopstat.haus"])
  dns_record_types   = toset(["A", "AAAA"])
}

resource "aws_route53_record" "cloudfront" {
  for_each = {
    for pair in setproduct(local.cloudfront_domains, local.dns_record_types) :
    "${pair[0]}-${pair[1]}" => {
      name = pair[0]
      type = pair[1]
    }
  }

  zone_id = aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type

  alias {
    name                   = aws_cloudfront_distribution.gold_artifacts.domain_name
    zone_id                = aws_cloudfront_distribution.gold_artifacts.hosted_zone_id
    evaluate_target_health = false
  }
}
```

### Key Implementation Details

- **Alias records vs. CNAMEs**: Route 53 alias records are required for the apex domain
  (`hoopstat.haus`) because the DNS specification does not allow CNAME records at the
  zone apex. Alias records also support both IPv4 (A) and IPv6 (AAAA).

- **`evaluate_target_health = false`**: CloudFront distributions don't support Route 53
  health checks, so this must be `false`.

- **IPv6 support**: The CloudFront distribution has `is_ipv6_enabled = true`, so AAAA
  records are needed alongside A records.

- **www-to-apex redirect**: The existing `aws_cloudfront_function.www_to_apex_redirect`
  is conditionally created when `cloudfront_enable_www_redirect = true` (default) and
  both apex and www aliases are present. No new code is needed — it activates
  automatically.

### Updating Outputs

Consider updating `infrastructure/outputs.tf` to include the custom domain URLs:

```hcl
output "custom_domain_urls" {
  description = "Custom domain URLs for accessing the application"
  value = {
    apex_url  = "https://hoopstat.haus"
    index_url = "https://hoopstat.haus/index/latest.json"
  }
}
```

### Frontend and Consumer Updates

After this ticket is deployed, downstream consumers can be updated to use the custom
domain. This is out of scope for this ticket but should be tracked as follow-up work:

- `frontend-app/scripts/app.js` — update the API base URL
- `apps/mcp-local-proxy/app/http_client.py` — update `DEFAULT_BASE_URL`

### Manual Verification Checklist

After deployment and DNS propagation:

1. `dig hoopstat.haus A` returns a CloudFront IP
2. `dig hoopstat.haus AAAA` returns a CloudFront IPv6 address
3. `curl -I https://hoopstat.haus/index/latest.json` returns 200 with correct headers
4. `curl -I https://www.hoopstat.haus/` returns 301 redirect to `https://hoopstat.haus/`
5. Browser navigation to `https://hoopstat.haus` loads the frontend application

### Testing

Add tests that validate:
- Route 53 records reference the correct hosted zone and CloudFront distribution
- Both A and AAAA records are created for apex and www
- The alias configuration points to the CloudFront distribution
- Follow existing test patterns in `infrastructure/tests/`
