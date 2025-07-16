---
title: "ADR-011: Secrets Management and Authentication Strategy"
status: "Accepted"
date: "2025-07-16"
tags:
  - "secrets-management"
  - "github-oidc"
  - "aws-iam"
  - "security"
  - "authentication"
---

## Context

* **Problem:** The Hoopstat Haus project needs a secure method for GitHub Actions workflows to authenticate with AWS services without storing long-lived credentials. Traditional approaches using access keys create security risks through credential storage, rotation complexity, and potential exposure in logs or code.
* **Constraints:** Must eliminate long-lived credentials in GitHub repositories, provide secure authentication for CI/CD workflows, support fine-grained access control, integrate seamlessly with existing GitHub Actions workflows, align with AWS security best practices, and maintain auditability of access patterns.

## Decision

We will use **GitHub's OIDC (OpenID Connect) provider with AWS IAM Roles** to provide secure, keyless authentication for workflows accessing AWS services.

## Considered Options

1. **GitHub OIDC with AWS IAM Roles (The Chosen One):** Token-based authentication using OpenID Connect.
   * *Pros:* No long-lived credentials stored in GitHub, tokens are short-lived and automatically rotated, fine-grained permissions through IAM role policies, full audit trail through AWS CloudTrail, native integration with GitHub Actions, follows AWS security best practices, reduces credential management overhead
   * *Cons:* Initial setup complexity for IAM trust relationships, requires understanding of OIDC concepts, limited to GitHub Actions environment, debugging authentication issues can be more complex than simple access keys

2. **AWS Access Keys stored as GitHub Secrets:** Traditional credential-based approach.
   * *Pros:* Simple to set up and understand, works across all environments, familiar to most developers, direct authentication without token exchange
   * *Cons:* Long-lived credentials create security risks, manual rotation required, potential for accidental exposure in logs, violates principle of least privilege, credentials must be managed and secured in GitHub repository settings

3. **Self-hosted GitHub Runners with IAM Instance Profiles:** EC2-based runners with attached IAM roles.
   * *Pros:* No credential storage required, native AWS authentication, can provide consistent environment, supports complex workflow requirements
   * *Cons:* Significant infrastructure overhead and cost, maintenance burden for EC2 instances, scaling complexity, overkill for current project size, contradicts the simplicity principle

## Consequences

* **Positive:** Eliminates long-lived credential storage and associated security risks, automatic token rotation and expiration reduces credential lifecycle management, fine-grained access control through IAM policies, comprehensive audit logging of all access attempts, aligns with modern security best practices, scales naturally with project growth.
* **Negative:** More complex initial setup compared to simple access keys, requires team understanding of OIDC and AWS IAM trust relationships, debugging authentication failures requires knowledge of token exchange process, limited to GitHub Actions workflows.
* **Future Implications:** All CI/CD workflows will use OIDC-based authentication, IAM roles and policies will define access patterns for different workflow types, security audit processes will focus on IAM role permissions rather than credential management, future automation tools must integrate with OIDC or use similar token-based approaches.