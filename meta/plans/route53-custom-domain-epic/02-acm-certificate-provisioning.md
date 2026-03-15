# Ticket 2: ACM Certificate Provisioning

> **Epic:** [Route 53 Custom Domain](00-executive-summary.md)
> **Sequence:** 2 of 4 — depends on Ticket 1 (Route 53 Hosted Zone)
> **Related ADRs:** [ADR-010](../../adr/ADR-010-terraform_iac.md), [ADR-039](../../adr/ADR-039-custom-domain-management.md) (Proposed)

---

## What do you want to build?

Provision an ACM (AWS Certificate Manager) certificate for `hoopstat.haus` with a
wildcard SAN (`*.hoopstat.haus`) using DNS validation. This certificate will be used by
the CloudFront distribution to serve HTTPS traffic on the custom domain.

## Acceptance Criteria

- [ ] An `aws_acm_certificate` resource is defined for `hoopstat.haus` in `infrastructure/main.tf`
- [ ] The certificate includes `*.hoopstat.haus` as a Subject Alternative Name (SAN)
- [ ] The validation method is set to `"DNS"`
- [ ] The resource uses the default AWS provider (which targets `us-east-1`, as required by CloudFront)
- [ ] A `lifecycle { create_before_destroy = true }` block is included for zero-downtime certificate rotation
- [ ] The resource is tagged consistently with existing infrastructure
- [ ] `terraform plan` runs cleanly with no unrelated changes
- [ ] Terraform tests validate the certificate resource configuration

## Implementation Notes

### Resource Definition

Add to `infrastructure/main.tf` in the Route 53 / custom domain section:

```hcl
# ============================================================================
# ACM Certificate for Custom Domain
# ============================================================================

resource "aws_acm_certificate" "main" {
  domain_name               = "hoopstat.haus"
  subject_alternative_names = ["*.hoopstat.haus"]
  validation_method         = "DNS"

  tags = {
    Name    = "${var.project_name}-certificate"
    Purpose = "SSL/TLS certificate for custom domain"
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

### Why No Provider Alias Is Needed

The epic description mentions ensuring an `us-east-1` provider alias. However, the
default region in `variables.tf` is already `us-east-1`:

```hcl
variable "aws_region" {
  default = "us-east-1"
}
```

Since CloudFront requires ACM certificates in `us-east-1` and our default provider
already targets that region, no alias is required. If the default region ever changes,
a provider alias should be introduced at that time.

### Why DNS Validation Over Email

- DNS validation enables automatic certificate renewal (ACM renews DNS-validated
  certificates automatically before expiration)
- The Route 53 hosted zone from Ticket 1 provides the DNS authority needed for
  automated validation record creation (Ticket 3)
- Email validation would require manual intervention on every renewal cycle

### Wildcard SAN Strategy

The `*.hoopstat.haus` SAN covers all potential subdomains (e.g., `www.hoopstat.haus`,
`api.hoopstat.haus`) with a single certificate. This avoids needing separate certificates
for future subdomains.

### Dependencies

- **Ticket 1 must be completed and applied first.** While the ACM certificate itself
  doesn't require the hosted zone, DNS validation (Ticket 3) needs the zone to be
  authoritative for the domain.
- The certificate will remain in `PENDING_VALIDATION` status until Ticket 3 creates
  the validation records.

### Testing

Add tests that validate:
- The certificate resource exists with the correct domain name
- The SAN includes `*.hoopstat.haus`
- The validation method is `DNS`
- Follow existing test patterns in `infrastructure/tests/`
