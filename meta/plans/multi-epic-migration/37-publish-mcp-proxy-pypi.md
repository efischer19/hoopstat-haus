# feat: Publish MCP proxy to PyPI from hoopstat-data

## What do you want to build?

Configure and execute the first PyPI publication of the MCP local proxy from the hoopstat-data repository. This makes the MCP proxy installable via `pip install` for AI agent integration.

## Acceptance Criteria

- [ ] The `publish-mcp-proxy.yml` workflow is configured with the correct PyPI token
- [ ] The MCP proxy package metadata (name, version, description, author, license) is correct in `pyproject.toml`
- [ ] The package builds successfully (`poetry build`)
- [ ] The package publishes to PyPI (or TestPyPI first for validation)
- [ ] The package is installable via `pip install hoopstat-mcp-proxy` (or whatever the package name is)
- [ ] The installed package runs correctly (`hoopstat-mcp-proxy --help` or equivalent)
- [ ] The publish workflow is configured to trigger on version tags (e.g., `v*`)
- [ ] README includes installation instructions for end users

## Implementation Notes (Optional)

**PyPI publication setup:**
1. Create a PyPI account (or use existing) for the package
2. Create a PyPI API token scoped to the specific package
3. Add the token as a GitHub repository secret in hoopstat-data
4. Configure the publish workflow to use the token

**TestPyPI first:**
Before publishing to production PyPI:
1. Publish to TestPyPI (`https://test.pypi.org/`)
2. Install from TestPyPI and verify the package works
3. Then publish to production PyPI

**Package naming:**
Verify the package name is available on PyPI. If `hoopstat-mcp-proxy` is taken, consider alternatives.

**Version strategy:**
- Use semantic versioning (SemVer)
- Tag the commit with the version (e.g., `v1.0.0`)
- The workflow triggers on version tags and publishes

**MCP proxy specifics:**
The MCP local proxy has both Python and TypeScript components (ADR-034). The PyPI package covers the Python component. The TypeScript component may need separate distribution (npm) — document this if applicable.

Reference hoopstat-haus's `publish-mcp-proxy.yml` workflow for the existing publication setup.
