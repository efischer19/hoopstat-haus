# Multi-Epic Migration: Executive Summary

> "Plan to throw one away; you will, anyhow." — Fred Brooks, *The Mythical Man-Month*

## Overview

This plan decomposes the hoopstat-haus monorepo into a hierarchy of reusable **blueprint** (template) repositories and two **product** repositories (`hoopstat-data` and `hoopstat-app`), then deploys hoopstat.haus v1 from the new repos. The goal is to capture lessons learned as reusable templates that can spin up similar projects in 5-10 minutes, while cleanly separating concerns that have outgrown the monorepo.

**Proposed ADR:** [ADR-042 — Multi-Repository Migration Strategy](../../adr/ADR-042-multi-repository-migration.md)

## Repository Hierarchy

```
blueprint-repo-blueprints          (language-agnostic grandparent template)
├── static-js-app-blueprint        (static frontend template)
│   └── hoopstat-app               (product: analytics dashboard)
└── python-project-blueprint       (Python monorepo template)
    └── python-aws-data-blueprint  (Python + AWS template)
        └── hoopstat-data          (product: data pipeline + infra)
```

## Epic Sequence

The migration is organized into **9 epics**, executed in strict dependency order. Each epic's tickets are designed as small, independently verifiable chunks of work.

| # | Epic | Tickets | Depends On | Target Repo |
|---|------|---------|------------|-------------|
| 1 | File Mapping Investigation | 01 | — | hoopstat-haus |
| 2 | blueprint-repo-blueprints | 02–06 | Epic 1 | blueprint-repo-blueprints |
| 3 | static-js-app-blueprint | 07–11 | Epic 2 | static-js-app-blueprint |
| 4 | python-project-blueprint | 12–15 | Epic 2 | python-project-blueprint |
| 5 | python-aws-data-blueprint | 16–19 | Epic 4 | python-aws-data-blueprint |
| 6 | hoopstat-data Initial Cut | 20–24 | Epics 1, 5 | hoopstat-data |
| 7 | hoopstat-app Initial Cut | 25–28 | Epics 1, 3 | hoopstat-app |
| 8 | Archive/Teardown Existing Repo | 29–31 | Epics 6, 7, 9 | hoopstat-haus |
| 9 | Integration & Deployment (v1) | 32–38 | Epics 6, 7 | hoopstat-data, hoopstat-app |

**Note:** Epics 3 and 4 can be executed in parallel (both depend only on Epic 2). Epics 6 and 7 can also be parallelized. Epic 8 (archive) must wait until Epic 9 (v1 deployment) is validated — the old repo stays alive as a fallback until the new deployment is confirmed working.

## Sequencing Diagram

```
Epic 1 (File Mapping)
  │
  ▼
Epic 2 (blueprint-repo-blueprints)
  │
  ├──────────────────┐
  ▼                  ▼
Epic 3              Epic 4
(static-js-app)     (python-project)
  │                  │
  │                  ▼
  │               Epic 5
  │               (python-aws-data)
  │                  │
  ├──────┐     ┌─────┘
  ▼      │     ▼
Epic 7   │   Epic 6
(app)    │   (data)
  │      │     │
  │      ▼     │
  │  Epic 9 ◄──┘
  │  (v1 deploy)
  │      │
  │      ▼
  └─► Epic 8
      (archive)
```

## Ticket Summary

### Epic 1: File Mapping Investigation
- **01** — Create file-to-repo mapping document

### Epic 2: blueprint-repo-blueprints
- **02** — Initialize repository structure
- **03** — Development philosophy, AI instructions, and meta scaffolding
- **04** — CI/CD quality tooling (pre-commit, linting, basic workflows)
- **05** — Documentation and README templates
- **06** — Review, test template instantiation, and finalize

### Epic 3: static-js-app-blueprint
- **07** — Initialize from blueprint-repo-blueprints
- **08** — Frontend scaffolding with accessibility foundations
- **09** — GitHub Pages deployment workflow
- **10** — Optional AWS S3/CloudFront deployment path
- **11** — Review and finalize

### Epic 4: python-project-blueprint
- **12** — Initialize from blueprint-repo-blueprints
- **13** — Python monorepo structure (Poetry, apps/, libs/, templates/)
- **14** — CI/CD with PyPI stub and Docker build
- **15** — Review and finalize

### Epic 5: python-aws-data-blueprint
- **16** — Initialize from python-project-blueprint
- **17** — AWS integration scaffolding (Lambda, ECR, S3, Terraform)
- **18** — Medallion architecture example structure
- **19** — Review and finalize

### Epic 6: hoopstat-data Initial Cut
- **20** — Initialize from python-aws-data-blueprint
- **21** — Migrate data pipeline apps and shared libraries
- **22** — Migrate and adapt Terraform infrastructure
- **23** — Adapt CI/CD workflows
- **24** — Validation and smoke testing

### Epic 7: hoopstat-app Initial Cut
- **25** — Initialize from static-js-app-blueprint
- **26** — Migrate frontend-app content
- **27** — Configure AWS S3/CloudFront deployment
- **28** — Validation and smoke testing

### Epic 8: Archive/Teardown Existing Repo
- **29** — Tear down AWS infrastructure and disable scheduled workflows
- **30** — Remove secrets, tokens, and decommission GitHub OIDC role
- **31** — Archive repository with final README

### Epic 9: Integration & Deployment (hoopstat.haus v1)
- **32** — Provision new AWS OIDC tokens for both product repos
- **33** — Deploy hoopstat-data infrastructure (Terraform apply)
- **34** — Deploy hoopstat-app to S3/CloudFront
- **35** — Route53 DNS cutover (human-run)
- **36** — Restart bronze cronjob and validate pipeline
- **37** — Publish MCP proxy to PyPI
- **38** — End-to-end smoke test and v1 sign-off

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Downtime during migration | Keep old repo alive until new deployment is validated (Epic 8 last) |
| Lost secrets/tokens | Document all secrets needed before teardown; provision new ones first |
| Broken CI/CD in new repos | Each blueprint repo is reviewed and tested before cutting product repos |
| Template drift | Blueprint repos are GitHub template repos; updates are manual but tracked |
| DNS propagation issues | Route53 changes are human-run with TTL planning; old infra stays up |
| Data pipeline interruption | Bronze cronjob is stopped last, restarted first in new repo |

## Success Criteria

1. All four blueprint repos exist as functional GitHub template repositories.
2. `hoopstat-data` and `hoopstat-app` are initialized from their respective blueprints.
3. hoopstat.haus serves the same frontend dashboard from the new `hoopstat-app` repo's S3 deployment.
4. The data pipeline (bronze → silver → gold) runs successfully in `hoopstat-data`.
5. The MCP proxy is published to PyPI from `hoopstat-data`.
6. The original hoopstat-haus repository is archived with a clear redirect README.
7. No user-facing downtime occurs during the migration.
