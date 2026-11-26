# feat: MCP proxy on mcp 2.x, with a real package name, published to PyPI

## What do you want to build?

Get `apps/mcp-local-proxy` installable by anyone with `pip install hoopstat-mcp-proxy` / `uvx`, against the live data at `https://hoopstat.haus`.

Three blockers today:

1. **mcp 2.x**: Dependabot PR #959 (and #946 before it) fails CI because `mcp.server.fastmcp.FastMCP` was renamed to `mcp.server.mcpserver.MCPServer` in mcp 2.x.
2. **Package name**: the importable package is literally `app` (`packages = [{include = "app"}]`). Published to PyPI, that would install a top-level `app` module into users' environments and collide with anything else named `app`.
3. **Never published**: PyPI returns 404 for `hoopstat-mcp-proxy`; the publish workflow (`publish-mcp-proxy.yml`, tag `mcp-proxy/v*`) has never run.

## Acceptance Criteria

- [ ] Upgraded to mcp 2.x using `MCPServer`; #959's updates included or #959 closed in favor of this PR
- [ ] Package renamed (e.g. `hoopstat_mcp`); console script `hoopstat-mcp` and `python -m` entry points updated; tests and Dockerfile updated
- [ ] Default base URL is `https://hoopstat.haus` (ticket 06, if not already done)
- [ ] `uvx --from ./apps/mcp-local-proxy hoopstat-mcp get-index` returns live data
- [ ] Verified in a real MCP client (e.g. Claude Desktop / Claude Code `mcp add`) over stdio
- [ ] PyPI trusted publishing configured for `efischer19/hoopstat-haus` + `publish-mcp-proxy.yml` (manual, pypi.org UI); tag `mcp-proxy/v0.1.0` pushed; `pip install hoopstat-mcp-proxy` works
- [ ] `MCP_SETUP.md` matches the published package

## Implementation Notes (Optional)

- Do this after Oct 21, once `latest.json` is live, so the end-to-end check is real.
- ADR-033 (local proxy) and ADR-034 (dual runtime) still describe the intended architecture; no new ADR needed for a rename.
- Under #693, this app moves to `hoopstat-data`. Keep the change self-contained so it ports cleanly.
