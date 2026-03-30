# feat: Documentation and README templates for blueprint-repo-blueprints

## What do you want to build?

Add documentation scaffolding to the `blueprint-repo-blueprints` template: a docs-src structure for MkDocs, README templates for common directories, and a `repomix.config.json` file. These ensure every derived repo starts with consistent documentation.

## Acceptance Criteria

- [ ] `docs-src/index.md` exists with a placeholder homepage template
- [ ] `docs-src/DEVELOPMENT_PHILOSOPHY.md` is symlinked or references `meta/DEVELOPMENT_PHILOSOPHY.md`
- [ ] `mkdocs.yml` exists with Material theme configuration (adapted from hoopstat-haus, with template placeholders for site name/URL)
- [ ] `docs-requirements.txt` lists MkDocs dependencies
- [ ] `scripts/build-docs.sh` exists to build documentation locally
- [ ] `repomix.config.json` is present (same as hoopstat-haus)
- [ ] `.repomixignore` is present with sensible defaults
- [ ] README templates exist for common directories that downstream blueprints may create (e.g., a `README.md` template for apps/, libs/, scripts/)
- [ ] All placeholder values use consistent markers (e.g., `{{PROJECT_NAME}}`)

## Implementation Notes (Optional)

From hoopstat-haus, adapt:
- `mkdocs.yml` — Keep the Material theme config, navigation structure as a starting point. Replace hoopstat-specific nav entries with generic sections.
- `repomix.config.json` — Copy as-is per issue description ("can probably live in all repos").
- `docs-requirements.txt` — Copy the MkDocs dependencies.
- `scripts/build-docs.sh` — Copy and generalize.

The docs structure should be minimal but functional — derived blueprints add their own content. The key is having the MkDocs infrastructure ready to go.
