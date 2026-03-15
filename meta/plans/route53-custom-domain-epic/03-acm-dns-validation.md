# Ticket 3: ACM DNS Validation Automation

> **Epic:** [Route 53 Custom Domain](00-executive-summary.md)
> **Sequence:** 3 of 4 — depends on Tickets 1 and 2
> **Related ADRs:** [ADR-010](../../adr/ADR-010-terraform_iac.md), [ADR-039](../../adr/ADR-039-custom-domain-management.md) (Proposed)

---

## What do you want to build?

Automate ACM certificate DNS validation by creating the required CNAME records in the
Route 53 hosted zone, and define a validation resource that waits for the certificate to
reach the `ISSUED` state. This eliminates any manual DNS record creation and ensures
certificate renewals are fully automatic.

## Acceptance Criteria

- [ ] An `aws_route53_record` resource is defined that iterates over the ACM certificate's `domain_validation_options`
- [ ] The record creates CNAME entries in the Route 53 hosted zone from Ticket 1
- [ ] An `aws_acm_certificate_validation` resource is defined that references both the certificate and the validation records
- [ ] The validation resource blocks `terraform apply` until the certificate reaches `ISSUED` status
- [ ] The validated certificate ARN is available as output or local value for use in Ticket 4
- [ ] `terraform plan` runs cleanly with no unrelated changes
- [ ] Terraform tests validate the validation resource configuration

## Implementation Notes

### Validation Records

Use the `for_each` pattern to iterate over the certificate's domain validation options.
This handles both the apex domain and the wildcard SAN:

```hcl
# ============================================================================
# ACM Certificate DNS Validation
# ============================================================================

resource "aws_route53_record" "acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main.zone_id
}
```

### Validation Waiter

```hcl
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.acm_validation : record.fqdn]
}
```

### Key Implementation Details

- **`allow_overwrite = true`**: ACM may return the same validation record for both the
  apex and wildcard domains (since `*.hoopstat.haus` validation uses the same CNAME as
  `hoopstat.haus`). The `for_each` keyed by `domain_name` and `allow_overwrite` handles
  this deduplication.

- **TTL of 60 seconds**: Validation records are low-volume, infrastructure-only records.
  A short TTL ensures fast propagation during initial validation. ACM manages renewal
  automatically after the initial validation.

- **Blocking behavior**: The `aws_acm_certificate_validation` resource will cause
  `terraform apply` to wait (with a timeout) until ACM confirms the certificate is
  valid. This ensures downstream resources (Ticket 4) receive a valid certificate ARN.

### Prerequisites

- **Ticket 1** must be applied and NS delegation must be complete at the external
  registrar. Without authoritative DNS, the validation records won't resolve and ACM
  will not issue the certificate.
- **Ticket 2** must be applied so the `aws_acm_certificate.main` resource exists.

### Potential Issues

- If NS delegation is not yet complete, `terraform apply` will hang waiting for
  validation. This is expected behavior — the apply should be retried after delegation
  propagates.
- The validation timeout defaults to 75 minutes in the AWS provider. If delegation is
  slow, the apply may need to be re-run.

### Testing

Add tests that validate:
- The validation records reference the correct hosted zone
- The validation resource references the correct certificate
- Follow existing test patterns in `infrastructure/tests/`
