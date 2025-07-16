---
title: "ADR-010: Infrastructure as Code Tool Selection"
status: "Accepted"
date: "2025-07-16"
tags:
  - "infrastructure-as-code"
  - "terraform"
  - "aws"
  - "automation"
---

## Context

* **Problem:** With AWS selected as our cloud provider, we need a reliable and maintainable way to define, provision, and manage cloud resources. Manual infrastructure management leads to configuration drift, inconsistent environments, and difficulty in reproducing setups across different stages of development and deployment.
* **Constraints:** Must work well with AWS services, support version control and code review workflows, enable reproducible infrastructure deployments, provide clear documentation and error reporting, integrate with existing development tools, and align with the project's preference for simplicity and static solutions.

## Decision

We will use **Terraform as our Infrastructure as Code (IaC) tool** to define and manage all cloud resources in the Hoopstat Haus project.

## Considered Options

1. **Terraform (The Chosen One):** HashiCorp's declarative infrastructure provisioning tool.
   * *Pros:* Cloud-agnostic declarative syntax, excellent AWS provider with comprehensive resource coverage, strong state management for tracking infrastructure changes, mature ecosystem with extensive community modules, integrates well with version control and CI/CD workflows, human-readable HCL configuration language
   * *Cons:* Learning curve for team members new to IaC concepts, state file management complexity in team environments, potential for resource drift if manual changes are made outside Terraform

2. **AWS CloudFormation:** AWS-native infrastructure as code service.
   * *Pros:* Native AWS integration with immediate support for new services, no additional tool installation required, integrated with AWS console and CLI, automatic rollback capabilities, no separate state management needed
   * *Cons:* AWS vendor lock-in, verbose YAML/JSON syntax, limited reusability across different cloud providers, slower adoption of new AWS features compared to Terraform, less flexible than Terraform for complex scenarios

3. **AWS CDK (Cloud Development Kit):** Infrastructure definition using familiar programming languages.
   * *Pros:* Use familiar programming languages (Python, TypeScript, etc.), powerful abstractions and reusable components, strong IDE support with autocomplete and type checking, good for developers comfortable with programming
   * *Cons:* More complex than declarative approaches, requires compilation step, larger learning curve for infrastructure-focused team members, can become overly complex for simple infrastructure needs

## Consequences

* **Positive:** Infrastructure changes are version-controlled and code-reviewed like application code, reproducible environments across development, staging, and production, clear documentation of infrastructure state and changes, ability to preview infrastructure changes before applying them, supports the project's automation and reliability goals.
* **Negative:** Team must learn Terraform-specific concepts and HCL syntax, state file management adds operational complexity, potential for infrastructure changes to break if Terraform state becomes corrupted, requires discipline to avoid manual infrastructure changes outside of Terraform.
* **Future Implications:** All AWS resources will be defined and managed through Terraform configurations, infrastructure changes will follow the same review process as code changes, team expertise will center around Terraform and infrastructure automation, future cloud provider migrations would be simplified by Terraform's cloud-agnostic approach.