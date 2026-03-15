# Epic: Route 53 Custom Domain for hoopstat.haus

## Executive Summary

This epic fully automates the infrastructure for routing the custom domain
`hoopstat.haus` to the existing CloudFront distribution that serves gold-layer JSON
artifacts. The domain is registered externally, so NS delegation is the only manual
step — everything else is managed through Terraform.

### Related ADRs

| ADR | Title | Relevance |
|-----|-------|-----------|
| [ADR-010](../../adr/ADR-010-terraform_iac.md) | Terraform IaC | All resources managed via Terraform |
| [ADR-017](../../adr/ADR-017-infrastructure_deployment_workflow.md) | Infrastructure Deployment Workflow | Plan on PR, apply on merge |
| [ADR-035](../../adr/ADR-035-gold_s3_public_access.md) | Gold S3 Public Access | CloudFront distribution architecture |
| [ADR-038](../../adr/ADR-038-cloudfront-cache-tuning.md) | CloudFront Cache Tuning | Existing cache policies remain unchanged |
| [ADR-039](../../adr/ADR-039-custom-domain-management.md) | Custom Domain Management | **Proposed** — documents the decisions in this epic |

### Existing Infrastructure Leverage

The current CloudFront distribution already supports custom domains through variables:

- `cloudfront_aliases` — accepts a list of custom domain names (currently `[]`)
- `cloudfront_acm_certificate_arn` — accepts an ACM certificate ARN (currently `""`)
- A `www-to-apex` redirect CloudFront Function is conditionally created when both aliases
  are present
- A lifecycle precondition enforces that aliases require a certificate

This means the CloudFront distribution itself requires **no structural changes** — only
the new Route 53 and ACM resources need to be added, and the existing variables need to
be populated.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       External Registrar                        │
│  NS records → Route 53 name servers (manual, one-time)          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                     Route 53 Hosted Zone                        │
│  hoopstat.haus                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  A     hoopstat.haus     → CloudFront (alias)              │ │
│  │  AAAA  hoopstat.haus     → CloudFront (alias)              │ │
│  │  A     www.hoopstat.haus → CloudFront (alias)              │ │
│  │  AAAA  www.hoopstat.haus → CloudFront (alias)              │ │
│  │  CNAME _acme-challenge   → ACM validation (auto-managed)  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    CloudFront Distribution                       │
│  aliases: ["hoopstat.haus", "www.hoopstat.haus"]                │
│  viewer_certificate: ACM cert (hoopstat.haus + *.hoopstat.haus) │
│  www-to-apex redirect: CloudFront Function (existing)           │
│                               │                                 │
│                    ┌──────────▼──────────┐                      │
│                    │  S3 Gold Bucket     │                      │
│                    │  /served/*          │                      │
│                    └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

### Ticket Sequence

The work is broken into four tickets, each building on the previous:

| # | Ticket | Depends On | Description |
|---|--------|------------|-------------|
| 1 | [Route 53 Hosted Zone](01-route53-hosted-zone.md) | — | Create hosted zone, output NS records |
| 2 | [ACM Certificate Provisioning](02-acm-certificate-provisioning.md) | Ticket 1 | Provision SSL cert for `hoopstat.haus` + `*.hoopstat.haus` |
| 3 | [ACM DNS Validation](03-acm-dns-validation.md) | Tickets 1, 2 | Automate certificate validation via Route 53 |
| 4 | [CloudFront & DNS Routing](04-cloudfront-domain-wiring.md) | Tickets 1, 2, 3 | Wire CloudFront aliases and create DNS records |

### Manual Step (Post-Deployment)

After Ticket 1 is applied, the Route 53 hosted zone will output four name server
addresses. These must be manually added as NS records at the external domain registrar.
DNS propagation may take up to 48 hours.

> **Important:** Tickets 2 and 3 (certificate provisioning and validation) will not
> complete until NS delegation is in place, because ACM DNS validation requires the
> Route 53 zone to be authoritative for the domain.

### Cost Impact

| Resource | Monthly Cost |
|----------|-------------|
| Route 53 Hosted Zone | $0.50 |
| Route 53 DNS Queries | ~$0.00 (negligible at current traffic) |
| ACM Certificate | Free |
| **Total** | **~$0.50/month** |
