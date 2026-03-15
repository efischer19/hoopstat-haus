---
title: "ADR-039: Custom Domain Management for hoopstat.haus"
status: "Proposed"
date: "2026-03-15"
tags: ["infrastructure", "dns", "route53", "acm", "cloudfront", "custom-domain"]
---

# ADR-039: Custom Domain Management for hoopstat.haus

## Context

The project currently serves gold-layer JSON artifacts via CloudFront using the default
`*.cloudfront.net` domain (ADR-035, ADR-038). To provide a branded, memorable URL for
consumers — including the frontend app (ADR-019) and the MCP local proxy (ADR-033) —
we need to route traffic through the custom domain `hoopstat.haus`.

**Key constraints:**

- The domain `hoopstat.haus` is registered with an external registrar (not AWS Route 53),
  so NS delegation must be performed manually outside of Terraform.
- CloudFront requires ACM certificates to be provisioned in `us-east-1` specifically.
  Our default region is already `us-east-1` (see `variables.tf`), so no provider alias
  is needed.
- The existing CloudFront distribution already supports custom aliases and ACM
  certificates via the `cloudfront_aliases` and `cloudfront_acm_certificate_arn`
  variables, including a precondition that enforces their co-dependency.
- A `www.hoopstat.haus` → `hoopstat.haus` redirect CloudFront Function already exists
  and is conditionally enabled when both aliases are present.
- All infrastructure is managed declaratively via Terraform (ADR-010) and deployed
  through the GitHub Actions infrastructure workflow (ADR-017).

**Decisions to make:**

1. How to manage DNS for `hoopstat.haus` within AWS.
2. How to provision and validate the SSL certificate.
3. How to wire the custom domain to the existing CloudFront distribution.

## Decision

We will manage the custom domain infrastructure entirely through Terraform, with only
NS delegation performed manually at the external registrar.

### 1. Route 53 Hosted Zone

Create an `aws_route53_zone` for `hoopstat.haus` and output its name servers. The
human operator will then configure NS records at the external registrar to delegate
DNS to Route 53. This is the only manual step.

### 2. ACM Certificate with DNS Validation

Provision a single `aws_acm_certificate` for `hoopstat.haus` with a Subject Alternative
Name (SAN) of `*.hoopstat.haus`, using DNS validation. Since the default provider region
is `us-east-1`, no provider alias is needed.

Automate validation by creating `aws_route53_record` resources that iterate over the
certificate's `domain_validation_options`, and use `aws_acm_certificate_validation` to
wait for the certificate to reach the `ISSUED` state.

### 3. CloudFront and DNS Routing

Pass the validated certificate ARN and domain aliases to the existing CloudFront
distribution via variables. Create Route 53 alias records (A and AAAA) for both the
apex domain and `www` subdomain, pointing to the CloudFront distribution. The existing
www-to-apex redirect function will handle the redirect at the edge.

## Considered Options

### Option 1: Fully Terraform-Managed DNS (Chosen)

Route 53 hosted zone, ACM certificate, validation records, and CloudFront alias records
are all defined in Terraform. NS delegation is the only manual step.

**Pros:**
- Fully reproducible and version-controlled infrastructure
- Certificate renewal is automatic (ACM handles this for DNS-validated certs)
- Consistent with ADR-010 (Infrastructure as Code)
- Single `terraform apply` provisions everything after initial NS delegation

**Cons:**
- Initial setup requires manual NS delegation at the registrar
- Route 53 hosted zone costs $0.50/month

### Option 2: External DNS Management

Keep DNS at the external registrar and only manage ACM certificate in AWS, using
email validation or manual DNS record creation.

**Pros:**
- No Route 53 cost
- Simpler initial setup

**Cons:**
- Certificate validation requires manual DNS record creation
- Certificate renewals may require manual intervention
- DNS records for CloudFront routing must be managed outside Terraform
- Violates the IaC principle (ADR-010)

### Option 3: Transfer Domain to Route 53

Transfer the domain registration to Route 53 to eliminate the manual NS delegation step.

**Pros:**
- Eliminates manual NS delegation entirely
- Consolidated billing

**Cons:**
- Domain transfer process adds complexity and delay
- Transfer may have lock periods
- Not all TLDs are supported by Route 53 for registration
- Out of scope for current infrastructure needs

## Consequences

### Positive

- All DNS and certificate infrastructure is version-controlled and reproducible
- ACM certificate renewal is fully automatic with DNS validation
- The existing CloudFront variable-based architecture requires no structural changes
- The www-to-apex redirect CloudFront Function works automatically once aliases are set
- Future subdomains (e.g., `api.hoopstat.haus`) can be added easily

### Negative

- Route 53 hosted zone incurs a $0.50/month fixed cost
- Initial NS delegation is manual and requires coordination with the registrar
- DNS propagation after NS delegation may take up to 48 hours

### Future Implications

- If the domain is ever transferred to Route 53, the hosted zone resource can remain
  unchanged — only the registration would move
- Additional subdomains or services can reuse the wildcard certificate
- The pattern established here can be replicated for any future custom domains
