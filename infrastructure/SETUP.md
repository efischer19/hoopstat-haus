# Infrastructure Setup Guide

This guide outlines the **one-time manual setup steps** required to link this GitHub repository with your AWS account for automated infrastructure deployment.

## Prerequisites

- AWS account with administrative access
- Access to this GitHub repository's settings
- AWS CLI installed locally (optional, for verification)

## Manual Setup Steps

### 1. Set GitHub Repository Secret

You need to add your AWS Account ID as a repository secret:

1. Go to your repository settings: `https://github.com/efischer19/hoopstat-haus/settings/secrets/actions`
2. Click "New repository secret"
3. Set the name as: `AWS_ACCOUNT_ID`
4. Set the value as your 12-digit AWS account ID (e.g., `123456789012`)
5. Click "Add secret"

### 2. Bootstrap AWS Infrastructure

The GitHub Actions workflow requires certain AWS resources to exist before it can run. You need to create these manually **once**:

#### Option A: Using AWS Console (Recommended)

1. **Create the OIDC Provider:**
   - Go to IAM → Identity providers → Add provider
   - Provider type: OpenID Connect
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
   - Thumbprints: `6938fd4d98bab03faadb97b34396831e3780aea1`, `1c58a3a8518e8759bf075b76b750d4f2df264fcd`

2. **Create the IAM Role:**
   - Go to IAM → Roles → Create role
   - Trusted entity type: Web identity
   - Identity provider: `token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
   - Role name: `hoopstat-haus-github-actions`
   - Attach policies for Terraform operations (see below)

#### Option B: Using AWS CLI

If you prefer command line, save this as `bootstrap.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:efischer19/hoopstat-haus:*"
        }
      }
    }
  ]
}
```

Then run:
```bash
# Create OIDC provider
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 1c58a3a8518e8759bf075b76b750d4f2df264fcd

# Create the role (replace YOUR_ACCOUNT_ID)
aws iam create-role \
  --role-name hoopstat-haus-github-actions \
  --assume-role-policy-document file://bootstrap.json
```

### 3. Required IAM Permissions

The `hoopstat-haus-github-actions` role needs these permissions to manage infrastructure:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:*",
        "s3:*",
        "ecr:*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

**Note:** This is a bootstrap policy. Once Terraform runs the first time, it will create more restrictive policies and you can remove this broad access.

## Verification

After completing the setup:

1. Check that your secret is set:
   - Go to repository Settings → Secrets and variables → Actions
   - Verify `AWS_ACCOUNT_ID` is listed

2. Verify the IAM role exists:
   ```bash
   aws iam get-role --role-name hoopstat-haus-github-actions
   ```

3. Test the workflow:
   - Create a small change to any file in `infrastructure/`
   - Open a PR
   - The workflow should run and post a Terraform plan comment

## Security Notes

- ✅ **No long-lived credentials** are stored in GitHub
- ✅ **Temporary tokens** are generated for each workflow run
- ✅ **Repository-scoped access** - the role can only be assumed by this specific repo
- ✅ **Least privilege** - permissions are scoped to only required AWS services

## Troubleshooting

### "Error assuming role"
- Verify the AWS Account ID secret is correct
- Check that the OIDC provider exists in IAM
- Ensure the role trust policy allows the repository

### "Access denied" errors
- Verify the IAM role has the required permissions
- Check AWS CloudTrail logs for detailed error information

### Workflow doesn't trigger
- Ensure changes are made to files in `infrastructure/` directory
- Check that the workflow file exists in `.github/workflows/infrastructure.yml`

## Next Steps

Once setup is complete:
- The workflow will automatically plan infrastructure changes on PRs
- Approved changes will automatically apply when merged to main
- Manual deployment is available via the Actions tab → Infrastructure Deployment → Run workflow