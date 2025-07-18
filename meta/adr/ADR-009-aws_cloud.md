---
title: "ADR-009: Cloud Provider Selection"
status: "Accepted"
date: "2025-07-16"
tags:
  - "cloud-infrastructure"
  - "aws"
  - "storage"
  - "container-registry"
---

## Context

* **Problem:** The Hoopstat Haus project needs a cloud infrastructure foundation to support deployment, storage, and container management for current and future applications. A clear cloud provider decision is essential for establishing consistent tooling, security practices, and cost management across all project components.
* **Constraints:** Must provide reliable storage for application data and artifacts, container registry for Docker images, strong security model, reasonable pricing for a growing project, and integration capabilities with existing development workflows and tools.

## Decision

We will use **Amazon Web Services (AWS) as our primary cloud provider**, with initial services including **Amazon S3 for storage** and **Amazon Elastic Container Registry (ECR) for container management**.

## Considered Options

1. **Amazon Web Services (AWS) (The Chosen One):** Comprehensive cloud platform with mature services.
   * *Pros:* Industry-leading reliability and availability, extensive service catalog for future growth, strong security and compliance features, excellent integration with GitHub Actions, competitive pricing with free tier benefits, comprehensive documentation and community support
   * *Cons:* Can be complex to navigate for beginners, potential for vendor lock-in, pricing complexity for advanced usage patterns

2. **Google Cloud Platform (GCP):** Google's cloud infrastructure platform.
   * *Pros:* Excellent data analytics and machine learning services, competitive pricing for compute and storage, strong Kubernetes integration, simplified billing structure
   * *Cons:* Smaller ecosystem compared to AWS, less GitHub Actions integration, fewer third-party integrations, less mature documentation for some services

3. **Microsoft Azure:** Microsoft's cloud computing platform.
   * *Pros:* Excellent integration with Microsoft toolchain, strong enterprise features, competitive pricing, good GitHub integration (Microsoft-owned)
   * *Cons:* Less popular in the open-source community, steeper learning curve for non-Microsoft environments, fewer community resources and tutorials

## Consequences

* **Positive:** Established and reliable foundation for cloud infrastructure, S3 provides scalable and durable storage for application data and static assets, ECR offers secure and integrated container image management, strong integration with GitHub Actions for CI/CD workflows, access to extensive AWS service catalog for future expansion, well-documented APIs and tooling for automation.
* **Negative:** Introduces dependency on AWS ecosystem, requires team to learn AWS-specific concepts and interfaces, potential for gradual vendor lock-in as usage grows, cost management complexity as services scale.
* **Future Implications:** All cloud infrastructure will be built on AWS services, future application architectures should consider AWS-native solutions where appropriate, team knowledge and tooling will be AWS-focused, migration to other cloud providers would require significant effort if needed in the future.