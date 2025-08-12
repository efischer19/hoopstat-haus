# AWS ECR Image Management Guide

This document outlines the procedures for managing Docker images in AWS Elastic Container Registry (ECR) for the Hoopstat Haus project.

## Overview

The project uses AWS ECR to store and manage Docker images built by our CI/CD pipeline. All application containers are stored in a single ECR repository with a standardized tagging strategy.

## ECR Repository Configuration

- **Repository Name**: `hoopstat-haus/prod`
- **Registry Region**: `us-east-1`
- **Image Scanning**: Enabled (automatic scan on push)
- **Tag Mutability**: MUTABLE (allows tag updates)

## Image Tagging Strategy

Images are tagged using the following convention:

### Standard Tags
- `{app-name}-{git-sha}` - Immutable tag linked to specific commit
- `{app-name}-latest` - Points to the most recent build of the application

### Examples
- `example-calculator-app-a1b2c3d4` - Specific commit of calculator app
- `example-calculator-app-latest` - Latest version of calculator app

## CI/CD Integration

### Automatic Image Building and Pushing

Images are automatically built and pushed to ECR when:
1. Code is pushed to the `main` branch
2. The application has a `Dockerfile`
3. CI tests pass successfully

### Build Process
1. **Detection**: CI detects changed applications with Dockerfiles
2. **Testing**: Applications are tested for code quality and functionality
3. **Building**: Docker images are built using multi-stage Dockerfiles
4. **Authentication**: GitHub Actions authenticates to AWS using OIDC
5. **Pushing**: Images are tagged and pushed to ECR
6. **Scanning**: ECR automatically scans images for vulnerabilities

## Deployment Workflow

### Manual Deployment
Use the deployment workflow to deploy specific application versions:

```bash
# Via GitHub Actions UI
1. Go to Actions → Deploy Applications
2. Select "Run workflow"
3. Choose application, environment, and image tag
4. Click "Run workflow"
```

### Automatic Deployment
Applications are automatically deployed when:
1. Code is pushed to `main` branch
2. Application has deployable changes
3. CI/CD pipeline completes successfully

## Image Lifecycle Management

### Automatic Cleanup Policies
ECR is configured with lifecycle policies to manage costs:

1. **Tagged Images**: Keep last 10 images with `v` prefix tags
2. **Untagged Images**: Delete images older than 1 day

### Manual Image Management

#### List Images
```bash
# List all images in the repository
aws ecr describe-images --repository-name hoopstat-haus/prod

# List images for specific application
aws ecr describe-images --repository-name hoopstat-haus/prod \
  --query "imageDetails[?starts_with(imageTag, 'example-calculator-app-')]"
```

#### Delete Specific Image
```bash
# Delete by tag
aws ecr batch-delete-image --repository-name hoopstat-haus/prod \
  --image-ids imageTag=example-calculator-app-old-version
```

#### Pull Image Locally
```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin {account-id}.dkr.ecr.us-east-1.amazonaws.com

# Pull specific image
docker pull {account-id}.dkr.ecr.us-east-1.amazonaws.com/hoopstat-haus/prod:example-calculator-app-latest
```

## Security Features

### Image Scanning
- **Scan on Push**: All images are automatically scanned for vulnerabilities
- **Scan Results**: View scan results in AWS Console under ECR → Repository → Images
- **Integration**: CI/CD pipeline can be configured to fail on critical vulnerabilities

### Access Control
- **GitHub Actions**: Uses OIDC for secure authentication without long-lived credentials
- **IAM Policies**: Least-privilege access for ECR operations
- **Repository Policies**: Configured to allow access only from authorized sources

## Monitoring and Observability

### CloudWatch Integration
- **Push Metrics**: Automatic metrics for image pushes and pulls
- **Storage Metrics**: Monitor repository size and costs
- **Access Logs**: Track who accesses which images

### Cost Monitoring
- **Lifecycle Policies**: Automatic cleanup to control storage costs
- **Usage Tracking**: Monitor repository size trends
- **Billing Alerts**: Set up alerts for unexpected ECR costs

## Troubleshooting

### Common Issues

#### Image Push Failures
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify ECR permissions
aws ecr describe-repositories --repository-names hoopstat-haus/prod

# Check Docker login
docker info | grep -i registry
```

#### Image Pull Failures
```bash
# Verify image exists
aws ecr describe-images --repository-name hoopstat-haus/prod \
  --image-ids imageTag=your-app-name-tag

# Check network connectivity
aws ecr get-login-password --region us-east-1
```

#### Authentication Issues
```bash
# Verify GitHub Actions role
aws iam get-role --role-name hoopstat-haus-github-actions

# Check OIDC provider
aws iam list-open-id-connect-providers
```

### Getting Help

1. **Infrastructure Issues**: Check Terraform configuration in `infrastructure/main.tf`
2. **CI/CD Issues**: Review GitHub Actions logs and workflow files
3. **AWS Issues**: Check CloudWatch logs and AWS console
4. **Application Issues**: Review application logs and health checks

## Best Practices

### Development Workflow
1. **Local Testing**: Always test Docker builds locally before pushing
2. **Branch Protection**: Use feature branches and PR reviews
3. **Image Size**: Optimize Dockerfiles for smaller images
4. **Security**: Regularly review scan results and update base images

### Production Deployment
1. **Staging**: Test deployments in staging environment first
2. **Rollback**: Keep previous versions available for quick rollback
3. **Monitoring**: Monitor application health after deployment
4. **Documentation**: Update deployment logs and documentation

### Cost Optimization
1. **Regular Cleanup**: Review and clean up unused images
2. **Base Images**: Use official, minimal base images
3. **Multi-stage Builds**: Use multi-stage Dockerfiles to reduce image size
4. **Lifecycle Policies**: Regularly review and update lifecycle policies

## Related Documentation

- [AWS ECR User Guide](https://docs.aws.amazon.com/ecr/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions with AWS](https://github.com/aws-actions)
- [Infrastructure Documentation](../infrastructure/README.md)

---

*Last updated: 2024-07-21*
*Document version: 1.0*