# feat: Remove secrets, tokens, and decommission GitHub OIDC role

## What do you want to build?

Remove all secrets and tokens from the hoopstat-haus GitHub repository and decommission the GitHub OIDC IAM role that grants the repository AWS access. This severs the old repository's ability to interact with AWS.

## Acceptance Criteria

- [ ] All GitHub repository secrets are deleted (list and remove each one)
- [ ] All GitHub repository variables are deleted
- [ ] All GitHub environment secrets are deleted (if any environments are configured)
- [ ] The GitHub OIDC IAM role for hoopstat-haus is deleted from AWS (or its trust policy is updated to remove hoopstat-haus)
- [ ] The PyPI token (if any) for MCP proxy publication is revoked or transferred to hoopstat-data
- [ ] Any other API tokens or credentials are revoked
- [ ] A checklist of all removed secrets is documented (secret names only, not values)
- [ ] Verify no workflows can authenticate to AWS after removal

## Implementation Notes (Optional)

**OIDC Role Decommission:**
The GitHub OIDC role (documented in `infrastructure/GITHUB_ACTIONS_ROLE.md`) trusts the hoopstat-haus repository. To decommission:
1. Update the IAM role's trust policy to remove the `repo:efischer19/hoopstat-haus:*` condition
2. OR delete the IAM role entirely if hoopstat-data has its own role
3. Verify that no workflow in hoopstat-haus can assume any AWS role

**Secret Inventory:**
Before deletion, document all secrets and their purposes. Expected secrets:
- `AWS_ROLE_ARN` — OIDC role ARN for AWS access
- Any PyPI tokens for MCP proxy
- Any other API keys

**Coordination:**
- Ensure hoopstat-data and hoopstat-app have their own OIDC roles provisioned (Epic 9, ticket 32) BEFORE removing the old role
- If any secret needs to be "transferred" (e.g., PyPI token), create the new secret in the target repo first
- Do NOT delete secrets until the new repos are confirmed working
