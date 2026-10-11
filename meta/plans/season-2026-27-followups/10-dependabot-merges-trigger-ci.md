# feat: Dependabot auto-merges trigger push CI and deploys

## What do you want to build?

`dependabot-auto-merge.yml` merges with the built-in `GITHUB_TOKEN`. GitHub deliberately doesn't trigger workflows from events created by that token, so Dependabot merges never run push CI on `main`: no image rebuilds, no Lambda deploys. Push CI hadn't run on `main` from March until a human merge on 2026-10-10.

Use a GitHub App installation token for the merge so the resulting push triggers CI like any other merge.

## Acceptance Criteria

- [ ] A private GitHub App (contents: write, pull-requests: write) exists and is installed on the repo (manual, GitHub UI)
- [ ] App ID and private key stored as **Dependabot** secrets (Dependabot-triggered workflows can't read Actions secrets)
- [ ] `dependabot-auto-merge.yml` mints a token with `actions/create-github-app-token` and uses it for `gh pr review` / `gh pr merge --auto`
- [ ] The next Dependabot merge to an app produces a `push` CI run on `main` and, for Lambda apps, a Deploy Applications run
- [ ] Merges still wait for the required `CI OK` check

## Implementation Notes (Optional)

- Consequence to accept: dependency bumps auto-deploy to prod Lambdas (and rebuild the Pi's bronze image). With `CI OK` required this is reasonably safe.
- Token-free alternative: a nightly workflow that rebuilds and deploys apps whose last image is older than `main`. Slower feedback, no secrets.
- The same auto-merge workflow likely exists in `python-aws-data-blueprint` / catch-data. Fix there too (or only there, if #693 lands first).
