# Ticket 1: Route 53 Hosted Zone for hoopstat.haus

> **Epic:** [Route 53 Custom Domain](00-executive-summary.md)
> **Sequence:** 1 of 4 — no dependencies
> **Related ADRs:** [ADR-010](../../adr/ADR-010-terraform_iac.md), [ADR-039](../../adr/ADR-039-custom-domain-management.md) (Proposed)

---

## What do you want to build?

Create a Route 53 public hosted zone for `hoopstat.haus` managed by Terraform. This is
the foundational DNS resource that all subsequent tickets in the epic depend on. The
hosted zone's name servers must be output so they can be manually configured at the
external domain registrar for NS delegation.

## Acceptance Criteria

- [ ] An `aws_route53_zone` resource is defined for `hoopstat.haus` in `infrastructure/main.tf`
- [ ] The resource is tagged consistently with existing infrastructure (project name, environment, managed-by)
- [ ] A new Terraform output named `route53_hosted_zone` exposes the zone ID and name servers
- [ ] The name server output is formatted for easy copy-paste into the external registrar
- [ ] `terraform plan` runs cleanly with no unrelated changes
- [ ] Terraform tests validate the hosted zone resource configuration

## Implementation Notes

### Resource Definition

Add to `infrastructure/main.tf` in a new clearly-commented section:

```hcl
# ============================================================================
# Route 53 Hosted Zone for Custom Domain
# ============================================================================

resource "aws_route53_zone" "main" {
  name    = "hoopstat.haus"
  comment = "Hosted zone for ${var.project_name} custom domain"

  tags = {
    Name    = "${var.project_name}-hosted-zone"
    Purpose = "Custom domain DNS management"
  }
}
```

### Output Definition

Add to `infrastructure/outputs.tf`:

```hcl
output "route53_hosted_zone" {
  description = "Route 53 hosted zone for custom domain"
  value = {
    zone_id      = aws_route53_zone.main.zone_id
    name_servers = aws_route53_zone.main.name_servers
  }
}
```

### Post-Apply Manual Step

After this ticket is merged and applied, the operator must:

1. Copy the four name server values from the Terraform output
2. Log into the external domain registrar for `hoopstat.haus`
3. Replace the existing NS records with the Route 53 name servers
4. Wait up to 48 hours for DNS propagation

> **Note:** Subsequent tickets (ACM validation, DNS records) will not function until
> NS delegation is complete.

### Testing

Add a test in `infrastructure/tests/` that validates:
- The hosted zone resource exists with the correct domain name
- The name server output is defined
- Follow existing test patterns in the `infrastructure/tests/` directory

### Considerations

- The domain name `hoopstat.haus` could be extracted to a variable for reusability, but
  given that this is the only domain and the project philosophy favors simplicity
  (DEVELOPMENT_PHILOSOPHY.md), hardcoding it is acceptable for now.
- No provider alias is needed since the default region is already `us-east-1`.
