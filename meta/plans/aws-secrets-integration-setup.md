# AWS/Secrets Integration Setup Plan

## Executive Summary

This plan outlines the technical approach for integrating the Hoopstat Haus repository with AWS to enable automated, secure deployments of Dockerized Python applications. The solution will establish a "software factory" capable of building, testing, and deploying applications to a live production environment with proper secrets management and AWS resource access.

## Epic Breakdown

### Epic 1: AWS Authentication & Identity Management
**Goal:** Establish secure authentication between GitHub Actions and AWS without storing long-lived credentials.

**User Stories:**
1. **As a DevOps engineer, I want GitHub Actions to authenticate to AWS using OIDC** so that we don't store long-lived AWS credentials in GitHub secrets.
2. **As a developer, I want applications to assume IAM roles** so they can access AWS resources securely without embedded credentials.
3. **As a security-conscious maintainer, I want least-privilege IAM policies** so that applications only have access to the specific AWS resources they need.

### Epic 2: Container Registry & Image Management
**Goal:** Set up AWS ECR for storing and managing Docker images built by CI/CD pipeline.

**User Stories:**
1. **As a CI/CD pipeline, I want to push Docker images to ECR** so that they're available for deployment to AWS services.
2. **As a deployment system, I want to pull images from ECR** so that I can deploy the latest application versions.
3. **As a maintainer, I want ECR lifecycle policies** so that old images are automatically cleaned up to control storage costs.

### Epic 3: Secrets Management Integration
**Goal:** Implement AWS Secrets Manager or Parameter Store for application configuration and secrets.

**User Stories:**
1. **As an application, I want to retrieve secrets from AWS Secrets Manager** so that sensitive configuration is not stored in code or environment variables.
2. **As a developer, I want a standardized secrets interface** so that all applications can access secrets consistently.
3. **As a security engineer, I want secrets rotation capabilities** so that credentials can be updated without application downtime.

### Epic 4: S3 Access & Data Management
**Goal:** Enable applications to securely read and modify data in S3 buckets.

**User Stories:**
1. **As a data pipeline application, I want to read raw data from S3** so that I can process basketball statistics.
2. **As a web application, I want to write processed data to S3** so that it's available for other services.
3. **As a data engineer, I want S3 bucket policies** so that access is controlled and auditable.

### Epic 5: Deployment Infrastructure & Orchestration
**Goal:** Set up AWS compute resources for running Dockerized applications with preference for serverless solutions.

**User Stories:**
1. **As a containerized application, I want to run on AWS Lambda** so that I have minimal infrastructure overhead and automatic scaling.
2. **As a CI/CD pipeline, I want to deploy applications automatically** when code is merged to main using GitHub workflow files that update image tags.
3. **As an operations engineer, I want simple deployment strategies** that leverage GitHub Actions and serverless infrastructure.

### Epic 6: Monitoring & Observability Integration
**Goal:** Extend existing structured logging to work with AWS CloudWatch and monitoring services.

**User Stories:**
1. **As an application, I want logs to flow to CloudWatch** so that they're centrally aggregated and searchable.
2. **As an operations engineer, I want CloudWatch alarms** so that I'm notified of application issues or performance degradation.
3. **As a developer, I want distributed tracing** so that I can debug issues across multiple services.

## Required ADRs

The following ADRs need to be proposed to support this AWS integration:

### 1. ADR-XXX: AWS Authentication Strategy for GitHub Actions
- **Decision:** Choose between GitHub OIDC, stored access keys, or AWS assume role approaches
- **Context:** Need secure, auditable authentication from CI/CD to AWS
- **Impact:** Affects security posture and operational complexity

### 2. ADR-XXX: Container Orchestration Platform Selection
- **Decision:** Choose between AWS Lambda, ECS Fargate, or hybrid approaches for running containers
- **Context:** Need scalable, cost-effective platform for running Python applications with preference for serverless solutions
- **Impact:** Affects operational complexity, cost, and deployment patterns

### 3. ADR-XXX: Secrets Management Strategy
- **Decision:** Choose between AWS Secrets Manager, Systems Manager Parameter Store, or external solutions
- **Context:** Need secure, rotatable secret storage with application integration
- **Impact:** Affects application architecture and security practices

### 4. ADR-XXX: S3 Bucket Organization and Access Patterns
- **Decision:** Define bucket structure, naming conventions, and access control policies
- **Context:** Need organized, secure data storage for basketball statistics
- **Impact:** Affects data architecture and access patterns

### 5. ADR-XXX: Cost Management and Resource Tagging Strategy
- **Decision:** Define tagging standards and cost monitoring approaches
- **Context:** Need to track and control AWS costs as usage grows
- **Impact:** Affects operational visibility and cost optimization

## High-Level Implementation Strategy

### Phase 1: Foundation (Weeks 1-2)
1. **Set up AWS OIDC authentication** between GitHub Actions and AWS
2. **Create base Terraform modules** for ECR, IAM roles, and basic networking
3. **Extend CI/CD pipeline** to build and push Docker images to ECR
4. **Establish S3 buckets** with proper IAM policies for data storage

### Phase 2: Application Deployment (Weeks 3-4)
1. **Deploy Lambda functions or simple compute resources** using Terraform
2. **Implement secrets management** integration in application templates
3. **Create deployment workflows** using GitHub Actions to update and deploy applications
4. **Set up CloudWatch logging** integration for structured logs

### Phase 3: Operationalization (Weeks 5-6)
1. **Implement monitoring and alerting** with CloudWatch alarms
2. **Set up deployment pipelines** with simple GitHub Actions-based deployment strategies
3. **Create operational runbooks** for common maintenance tasks
4. **Implement backup procedures** for S3 data

### Technical Architecture Overview

```
GitHub Actions (OIDC) → AWS IAM Role → ECR + Lambda + S3 + Secrets Manager
                                    ↓
                              Application Functions
                                    ↓
                              CloudWatch Logs + Metrics
```

### Key Implementation Principles

1. **Infrastructure as Code First:** All AWS resources defined in Terraform before manual creation
2. **Least Privilege Access:** IAM policies grant minimum necessary permissions
3. **Immutable Deployments:** Applications deployed as immutable container images
4. **Observability by Default:** All services integrate with CloudWatch for logs and metrics
5. **Cost Consciousness:** Resources sized appropriately and cleaned up automatically

## Risks & Open Questions

### High-Risk Items

1. **AWS Cost Management**
   - *Risk:* Uncontrolled AWS spending due to misconfigured resources or runaway processes
   - *Mitigation:* Implement billing alerts, resource tagging, and automatic cleanup policies

2. **Secret Sprawl and Management**
   - *Risk:* Secrets stored in multiple locations or accessed insecurely
   - *Mitigation:* Standardize on single secrets management service with automated rotation

3. **Deployment Pipeline Complexity**
   - *Risk:* Over-engineered deployment process that's difficult to maintain
   - *Mitigation:* Start with simple GitHub Actions workflows, add complexity incrementally

4. **Environment Consistency**
   - *Risk:* Development and production environments become inconsistent
   - *Mitigation:* Use same Terraform modules with parameterization, leverage existing single-environment strategy from ADR-012

### Medium-Risk Items

1. **Container Security**
   - *Risk:* Vulnerable base images or insecure container configurations
   - *Mitigation:* Implement container scanning in CI/CD pipeline

2. **Backup and Recovery**
   - *Risk:* Data loss without proper backup strategies
   - *Mitigation:* Implement automated S3 backups and versioning

### Open Questions

1. **Integration Testing:** How do we test application integration with AWS services in CI/CD - specific approach needed for GitHub Actions runners to `tf apply` and access ECR repo?

### Dependencies and Blockers

1. **AWS Account Setup:** Need AWS account with appropriate organization structure
2. **Domain and DNS:** May need Route 53 setup for application domains
3. **Budget Approval:** Need budget allocation for AWS resource consumption
4. **Security Review:** AWS integration approach should be reviewed by security team
5. **Terraform State Backend:** Need S3 bucket and DynamoDB table for Terraform state management

## Success Criteria

This AWS integration is considered successful when:

1. **Automated Deployments:** Applications automatically deploy to AWS when code is merged to main
2. **Secure Access:** Applications can read/write S3 data using IAM roles without embedded credentials
3. **Observability:** All application logs and metrics flow to CloudWatch with appropriate alerting
4. **Cost Transparency:** AWS costs are tracked, tagged, and within expected budget parameters
5. **Operational Readiness:** Team can deploy, monitor, and troubleshoot applications in production
6. **Security Compliance:** All AWS resources follow security best practices with least-privilege access

---

*This plan follows the architectural decision process outlined in ADR-001 and builds upon existing infrastructure decisions in ADR-008 (monorepo structure), ADR-010 (Terraform for IaC), and ADR-012 (single environment strategy).*