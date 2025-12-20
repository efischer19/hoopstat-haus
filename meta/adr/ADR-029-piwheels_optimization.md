# ADR-029: Use Piwheels for ARM Builds

## Status
Accepted

## Context
Our CI/CD pipeline builds Docker images for multiple architectures, including `linux/arm/v7` for deployment to Raspberry Pi devices (specifically the Bronze Ingestion app).

Building these images on standard x86_64 GitHub Actions runners requires QEMU emulation. While functional, QEMU is significantly slower than native execution. This performance penalty is exacerbated when installing Python packages with C-extensions (like `numpy`, `pandas`, `pydantic`), which must be compiled from source if no matching binary wheel is found.

Standard PyPI often lacks pre-compiled wheels for `armv7` architectures on newer Python versions. As a result, our CI builds were taking 30-90 minutes, spending the vast majority of that time compiling libraries under emulation.

## Decision
We will configure Poetry to use [piwheels](https://www.piwheels.org/) as a supplemental package source for any application targeting Raspberry Pi hardware.

Piwheels is a community project that provides pre-compiled binary wheels for Raspberry Pi architectures (ARMv6/v7).

We will add the following configuration to the `pyproject.toml` of relevant applications:

```toml
[[tool.poetry.source]]
name = "piwheels"
url = "https://www.piwheels.org/simple/"
priority = "supplemental"
```

## Consequences

### Positive
*   **Drastically Reduced Build Times**: Builds that previously took 45+ minutes can drop to under 5 minutes by downloading pre-compiled binaries instead of compiling from source.
*   **Reduced CI Cost/Usage**: Frees up GitHub Actions runners for other tasks and prevents hitting usage limits.
*   **Simpler Dockerfiles**: No need to install complex build dependencies (compilers, headers) in the Docker image just for installation.

### Negative
*   **External Dependency**: We introduce a dependency on `piwheels.org`. If the site is down, builds may fall back to compilation (slow) or fail.
*   **Version Lag**: Piwheels may not have the absolute latest version of a package immediately after release. However, for our stable dependencies, this is rarely an issue.
*   **Security**: We are trusting binaries from a third-party source. Piwheels is a well-established community project, but it is an additional supply chain consideration.

## Compliance
This change applies immediately to `apps/bronze-ingestion`. Other applications targeting standard AWS infrastructure (x86_64 or ARM64) should continue to use standard PyPI, as wheels are generally available for those architectures.
