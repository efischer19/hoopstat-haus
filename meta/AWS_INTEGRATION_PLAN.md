# AWS/Secrets Integration Setup Plan

## Overview

This document provides a comprehensive plan for integrating the Hoopstat Haus repository with AWS securely, enabling automated deployments of Dockerized Python applications that can read/modify data in S3.

## Epic Breakdown

### Human Maintainer Tasks
These tasks require AWS account access, permissions management, or policy decisions:

1. **AWS Account Setup & OIDC Provider Configuration** 
   - Create/configure AWS IAM Identity Provider for GitHub OIDC
   - Set up initial AWS account structure and billing
   - Create base IAM roles and policies for GitHub Actions

2. **Secret Management & Permissions Review**
   - Review and approve IAM role permissions
   - Configure AWS account-level security settings
   - Approve Terraform state management strategy

3. **Production Deployment Approval**
   - Review and approve initial infrastructure deployment
   - Validate security configurations
   - Approve first production deployment

### AI Assistant (Copilot) Tasks
These tasks involve code, configuration, and automation:

1. **Infrastructure as Code Development**
   - Create Terraform configurations for S3 buckets, ECR repositories
   - Design IAM roles and policies for applications
   - Implement Terraform state management

2. **GitHub Actions Workflow Development**
   - Create workflows for building and pushing to ECR
   - Implement deployment workflows using GitHub OIDC
   - Build verification and testing workflows

3. **Application Configuration Framework**
   - Design configuration system for apps to discover AWS resources
   - Update Python app template with AWS integration examples
   - Create shared configuration utilities

4. **Documentation and Examples**
   - Create deployment guides and runbooks
   - Document configuration patterns
   - Provide troubleshooting guides

## Required ADRs Assessment

### Existing Relevant ADRs
- **ADR-009**: ✅ AWS as cloud provider (S3 + ECR)
- **ADR-010**: ✅ Terraform for Infrastructure as Code  
- **ADR-011**: ✅ GitHub OIDC with AWS IAM roles for secrets management
- **ADR-006**: ✅ Docker containerization
- **ADR-007**: ✅ GitHub Actions for CI/CD
- **ADR-012**: ✅ Single production environment strategy

### New ADRs Needed
1. **ADR-016**: Terraform State Management Strategy
2. **ADR-017**: Application Configuration and AWS Resource Discovery
3. **ADR-018**: Container Image Naming and Tagging Strategy

## Technical Implementation Sequence

### Phase 1: Foundation Setup (Human + AI)
1. **Human**: Configure AWS IAM OIDC Identity Provider
2. **AI**: Create Terraform configurations for:
   - S3 buckets for data storage
   - ECR repositories for container images
   - IAM roles for GitHub Actions
   - Basic networking and security groups
3. **Human**: Review and apply initial Terraform configuration

### Phase 2: CI/CD Integration (AI)
4. **AI**: Create GitHub Actions workflows:
   - `build-and-push.yml`: Build Docker images and push to ECR
   - `deploy-to-aws.yml`: Deploy applications to AWS
   - `verify-aws-integration.yml`: End-to-end verification
5. **AI**: Update existing CI workflow to trigger AWS workflows

### Phase 3: Application Framework (AI)
6. **AI**: Update Python app template with:
   - AWS SDK integration (boto3)
   - Configuration management for AWS resources
   - Examples of S3 operations
   - Health checks and monitoring
7. **AI**: Create shared configuration utilities

### Phase 4: Verification & Documentation (AI)
8. **AI**: Implement comprehensive verification system
9. **AI**: Create documentation and troubleshooting guides
10. **Human**: Final review and production deployment

## Configuration Examples

### Environment Variables for Applications
```python
# Example configuration for a Python app
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "hoopstat-haus-data-prod")
ECR_REPOSITORY = os.getenv("ECR_REPOSITORY", "hoopstat-haus/app-name")
```

### S3 Bucket Mapping Strategy
```yaml
# apps/data-pipeline/config.yml
aws:
  s3:
    raw_data_bucket: "hoopstat-haus-raw-data-prod"
    processed_data_bucket: "hoopstat-haus-processed-data-prod"
    backup_bucket: "hoopstat-haus-backup-prod"
```

### ECR Repository Naming Convention
```
hoopstat-haus/data-pipeline
hoopstat-haus/stats-api
hoopstat-haus/web-dashboard
```

## Verification Strategy

### Overarching Verification GitHub Action
Create `verify-aws-integration.yml` that tests:

1. **Authentication Verification**
   - GitHub OIDC token exchange with AWS
   - IAM role assumption success
   - Permission verification for each service

2. **Infrastructure Verification**
   - S3 bucket accessibility and permissions
   - ECR repository push/pull capability
   - Network connectivity and security groups

3. **Application Integration Verification**
   - Sample Docker build and push to ECR
   - Sample S3 operations (create, read, update, delete)
   - Configuration loading and AWS resource discovery

4. **End-to-End Workflow Verification**
   - Complete CI/CD pipeline execution
   - Application deployment and health checks
   - Data pipeline execution with S3 operations

### Verification Test Structure
```yaml
name: Verify AWS Integration
on:
  schedule:
    - cron: '0 8 * * 1' # Weekly verification
  workflow_dispatch: # Manual trigger
  
jobs:
  verify-auth:
    # Test GitHub OIDC -> AWS authentication
  verify-infrastructure:
    # Test AWS resource accessibility
  verify-application-integration:
    # Test app-level AWS operations
  verify-end-to-end:
    # Test complete deployment workflow
```

## Risks & Open Questions

### Critical Risks
1. **No AWS Integration = No Deployments**: Without this setup, applications cannot be deployed to production
2. **Credential Exposure**: Improper OIDC setup could expose AWS credentials
3. **Resource Sprawl**: Uncontrolled AWS resource creation could increase costs
4. **State Management**: Terraform state corruption could prevent infrastructure changes

### Mitigation Strategies
1. **Gradual Rollout**: Implement in phases with verification at each step
2. **Least Privilege**: Start with minimal IAM permissions and expand as needed
3. **Cost Controls**: Implement AWS budget alerts and resource tagging
4. **State Backup**: Multiple Terraform state backup strategies

### Open Questions
1. **AWS Account Structure**: Single account vs. multi-account setup?
2. **Resource Naming**: Consistent naming convention across all AWS resources?
3. **Monitoring Strategy**: CloudWatch vs. external monitoring for AWS resources?
4. **Backup Strategy**: How to handle S3 data backup and disaster recovery?
5. **Scaling Strategy**: How to handle multiple environments in the future?

## Success Criteria
- [ ] GitHub Actions can authenticate to AWS without stored credentials
- [ ] Applications can build and deploy to ECR automatically
- [ ] Applications can read/write data to S3 buckets
- [ ] Infrastructure changes are managed through Terraform
- [ ] Comprehensive verification system validates all integrations
- [ ] Documentation enables team members to troubleshoot and extend

## Next Steps
1. Human maintainer: Set up AWS account and OIDC provider
2. AI assistant: Begin Terraform infrastructure development
3. Iterative development and testing of each phase
4. Final integration verification and documentation