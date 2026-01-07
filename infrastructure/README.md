# Infrastructure

This directory contains the Terraform configuration for managing the cloud infrastructure of the Hoopstat Haus project.

## Overview

The infrastructure is managed using Terraform and deployed via GitHub Actions. The setup follows the principles outlined in our ADRs:

- **ADR-007**: Uses GitHub Actions for CI/CD workflows
- **ADR-009**: Targets AWS as the cloud provider  
- **ADR-010**: Uses Terraform for Infrastructure as Code
- **ADR-011**: Uses GitHub OIDC with AWS IAM Roles for secure authentication

## Architecture

The infrastructure includes:

- **S3 Bucket**: Primary storage for application data and artifacts
- **Medallion Architecture S3 Buckets**: Three-tier data lake (Bronze/Silver/Gold layers) for NBA data processing
- **ECR Repository**: Container registry for Docker images
- **IAM Roles**: Least-privilege access roles for different services
- **OIDC Provider**: GitHub OIDC integration for keyless authentication
- **CloudWatch Observability** (ADR-018): Log groups, metrics, alarms, and monitoring
- **SNS Topics**: Alert routing for critical and warning notifications

### Medallion Data Architecture

The infrastructure implements a three-tier medallion architecture for data processing:

#### Bronze Layer (`hoopstat-haus-bronze`)
- **Purpose**: Raw data landing zone for NBA API ingestion (local execution)
- **Retention**: 2 years (primary), 30 days (errors), 90 days (metadata)
- **Storage**: Intelligent Tiering after 30 days for cost optimization
- **Security**: AES256 encryption, versioning enabled, public access blocked
- **Ingestion**: Local execution using `bronze_data_access` role (not Lambda)

#### Silver Layer (`hoopstat-haus-silver`)
- **Purpose**: Cleaned and conformed data with schema enforcement
- **Retention**: 3 years (primary), 90 days (quality logs), 30 days (quarantine)
- **Storage**: Standard-IA after 90 days
- **Security**: Same as Bronze, with read access to Bronze layer

#### Gold Layer (`hoopstat-haus-gold`)
- **Purpose**: Business-ready aggregated datasets for MCP server integration
- **Retention**: Indefinite (core business value)
- **Storage**: Standard class (frequently accessed by applications)
- **Security**: Same as Silver, with read access to Silver layer

#### Access Logs (`hoopstat-haus-access-logs`)
- **Purpose**: Audit trails for all S3 bucket operations
- **Retention**: 90 days
- **Storage**: Standard class with automatic cleanup

### Data Pipeline Orchestration

The medallion layers are connected via S3 event notifications (ADR-028):

- **Bronze→Silver**: Triggered by `_metadata/summary.json` updates in Bronze bucket
- **Silver→Gold**: Triggered by `metadata/{YYYY-MM-DD}/silver-ready.json` marker in Silver bucket
  - Ensures Gold runs **~1x/day** after Silver completes for the day
  - Prevents over-invocation (previously triggered on every Silver file write)
  - URL-safe naming per ADR-032

For detailed information about the data architecture strategy, see `meta/plans/medallion-data-architecture.md`.

## Deployment Workflow

### Automatic Deployment
- **Plan on PR**: When a PR is opened that modifies infrastructure files, a Terraform plan is automatically generated and posted as a comment
- **Apply on Merge**: When changes are merged to the main branch, Terraform apply is automatically executed

### Manual Deployment
- Manual deployment can be triggered via the GitHub Actions "workflow_dispatch" event
- Useful for emergency fixes or one-off infrastructure changes

## Security

The infrastructure uses a two-role security model that separates infrastructure administration from day-to-day operations:

### Infrastructure Administration Role
- **Role Name**: `hoopstat-haus-github-actions` (externally managed)
- **Purpose**: Infrastructure deployment and administrative tasks
- **Used By**: Infrastructure workflow (`infrastructure.yml`)
- **Permissions**: Full administrative access for Terraform operations
- **Management**: Created manually outside Terraform to avoid circular dependency

### Operations Role  
- **Role Name**: `hoopstat-haus-operations` (managed in Terraform)
- **Purpose**: Day-to-day application operations with least-privilege access
- **Used By**: CI workflow (`ci.yml`) and deployment workflow (`deploy.yml`)
- **Permissions**: 
  - ECR: Push/pull container images
  - S3: Object operations on medallion buckets (bronze/silver/gold/access_logs/main)
  - CloudWatch Logs: Create log streams and write log events
  - **Explicit denials**: All administrative actions (bucket creation, IAM operations, etc.)

### Data Access Roles (Medallion Architecture)
- **Bronze Data Access Role** (`hoopstat-haus-bronze-data-access`)
  - **Purpose**: Local bronze ingestion from external data sources
  - **Used By**: Local bronze-ingestion application
  - **Permissions**: Write to Bronze bucket, read/write CloudWatch logs
  
- **Silver Data Access Role** (`hoopstat-haus-silver-data-access`)
  - **Purpose**: Data transformation from Bronze to Silver
  - **Used By**: Silver processing Lambda function
  - **Permissions**: Read Bronze, write Silver, CloudWatch logs

- **Gold Data Access Role** (`hoopstat-haus-gold-data-access`)
  - **Purpose**: Business analytics and Gold layer data processing
  - **Used By**: Gold analytics Lambda function and GitHub Actions for Gold processing
  - **Permissions**: Read Silver bucket, write Gold bucket (including served/ artifacts), CloudWatch logs

### Security Benefits
- **Principle of Least Privilege**: Operations workflows cannot perform administrative actions
- **Separation of Concerns**: Infrastructure changes require the admin role, runtime operations use the limited role
- **Defense in Depth**: Even if CI/deploy workflows are compromised, infrastructure cannot be modified

### Authentication
- No long-lived AWS credentials are stored in GitHub
- Authentication uses GitHub OIDC with temporary tokens
- IAM roles follow the principle of least privilege
- S3 buckets include encryption and access controls
- ECR repository includes image scanning and lifecycle policies

## Usage

### Local Development
For local testing (not recommended for production changes):

```bash
cd infrastructure
terraform init
terraform plan
```

### Making Infrastructure Changes
1. Create a new branch
2. Modify the Terraform configuration files
3. Open a PR - this will trigger a Terraform plan
4. Review the plan output in the PR comments
5. Merge the PR - this will trigger Terraform apply

### ECR Integration
The infrastructure includes a fully configured ECR repository (`hoopstat-haus/prod`) that:
- Automatically scans images for vulnerabilities on push
- Applies lifecycle policies to manage storage costs
- Integrates with GitHub Actions for automated CI/CD
- See [ECR Image Management Guide](../docs/ECR_IMAGE_MANAGEMENT.md) for detailed usage

### Public JSON Artifacts (ADR-028)
The infrastructure serves public basketball analytics via small JSON artifacts through CloudFront:
- **Gold Presentation Layer**: Pre-computed JSON files under a `served/` prefix in S3
- **Public Access**: Via CloudFront distribution with Origin Access Control (OAC)
- **Security**: Private S3 bucket (Block Public Access enabled); CloudFront OAC with signed requests; read-only access limited to `served/` prefix
- **Access Method**: CloudFront HTTPS URLs
  - Base URL: `https://<cloudfront-domain>.cloudfront.net/`
  - Example: `https://<cloudfront-domain>.cloudfront.net/player_daily/{date}/{player_id}.json`
  - Global edge caching for low latency
  - Small payloads (≤100KB) for fast delivery
- **CORS Configuration**: CloudFront response headers policy allows GET/HEAD/OPTIONS from any origin (`*`) with 1-hour max-age
- **Cache Behavior**: 1-hour default TTL with automatic gzip/brotli compression
- **Details**: See [PUBLIC_ACCESS_GUIDE.md](PUBLIC_ACCESS_GUIDE.md), [ADR-028](../meta/adr/ADR-028-gold_layer_final.md), and [JSON Artifact Schemas](../docs-src/JSON_ARTIFACT_SCHEMAS.md)

## File Structure

- `main.tf` - Main Terraform configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `versions.tf` - Provider and Terraform version constraints
- `.terraform-version` - Terraform version specification

## Testing

The infrastructure includes comprehensive test suites to validate configuration and ensure compliance:

```bash
# Run general infrastructure validation
bash tests/test_infrastructure.sh

# Run medallion architecture specific tests  
bash tests/test_medallion_architecture.sh

# Run observability configuration tests
python tests/test_observability.py
```

### Test Coverage
- **Syntax validation**: Terraform configuration syntax and structure
- **Security checks**: No sensitive data in configuration files
- **Resource validation**: All required resources are properly configured
- **Medallion architecture compliance**: Data layer configuration matches requirements
- **Lifecycle policies**: Retention and storage class transitions are correct
- **IAM policies**: Least-privilege access patterns are implemented