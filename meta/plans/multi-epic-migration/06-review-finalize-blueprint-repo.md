# feat: Review, test template instantiation, and finalize blueprint-repo-blueprints

## What do you want to build?

A thorough review and validation pass on the `blueprint-repo-blueprints` template repository. Test that it works as a GitHub template by creating a test repository from it, verifying all content is correct, and making final adjustments.

## Acceptance Criteria

- [ ] Create a test repository from the template using GitHub's "Use this template" feature
- [ ] Verify all files are copied correctly to the new repo (no missing files, no extra files)
- [ ] Verify the CI workflow runs and passes in the test repo
- [ ] Verify pre-commit hooks work when cloning the test repo
- [ ] Verify MkDocs builds successfully with placeholder content
- [ ] All placeholder markers (`{{PROJECT_NAME}}`, etc.) are documented in the README with replacement instructions
- [ ] No hoopstat-specific content remains in any file
- [ ] README includes a "Getting Started" section explaining what to customize after using the template
- [ ] Delete the test repository after validation
- [ ] Tag the repository as `v1.0.0` after all checks pass

## Implementation Notes (Optional)

This is a critical quality gate. The blueprint-repo-blueprints is the foundation for all other templates, so any issues here propagate everywhere.

Review checklist:
1. Read every file in the repo end-to-end
2. Check for consistency in tone, formatting, and placeholder usage
3. Verify no secrets, credentials, or environment-specific values are present
4. Ensure the repo description and topics are set correctly on GitHub
5. Test the template by actually using it — don't just assume it works

After this ticket, the blueprint-repo-blueprints is considered stable and ready for downstream use.
