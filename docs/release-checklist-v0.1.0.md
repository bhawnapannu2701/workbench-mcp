# v0.1.0 Release Checklist

This checklist records Phase 7 release-preparation evidence. It does not create a tag,
GitHub release, package publication, Docker image publication, merge to `main`, or
independent final audit.

## Verified In Phase 7

| Item | Status | Evidence |
| --- | --- | --- |
| Clean Git status before Phase 7 changes | Done | Initial `git status --short` returned no output. |
| Current branch | Done | `git branch --show-current` returned `codex/workbench-mcp-v1`. |
| Remote branch configured | Done | `git branch -vv` showed `[origin/codex/workbench-mcp-v1]`; upstream command returned `origin/codex/workbench-mcp-v1`. |
| Existing stashes preserved | Done | Initial and later `git stash list` both showed the same two stashes. |
| Lint | Done | `uv run ruff check .` returned `All checks passed!`. |
| Format check | Done | Final audit `uv run ruff format --check .` returned `49 files already formatted`. |
| Type checking | Done | Final audit `uv run mypy src` returned `Success: no issues found in 29 source files`. |
| Tests | Done | Final audit `uv run pytest -rs` returned `94 passed, 4 skipped in 11.29s`. |
| Coverage | Done | Final audit `uv run pytest --cov=workbench_mcp --cov-report=term-missing` returned display coverage `83%`. |
| Package build | Done | `uv build` produced `dist\workbench_mcp-0.1.0.tar.gz` and `dist\workbench_mcp-0.1.0-py3-none-any.whl`. |
| MCP construction smoke | Done | `tests\unit\test_mcp_server.py::test_server_startup_succeeds` passed. |
| Real MCP client/server smoke | Done | `tests\e2e\test_mcp_stdio.py` passed serially. |
| Docker build | Done | `docker build --progress=plain -t workbench-mcp:local .` succeeded after Docker Desktop recovery. |
| Container smoke | Done | `uv run python scripts\run-container-smoke.py --image workbench-mcp:local` returned JSON status `ok`. |
| Compose verification | Done | `docker compose config` passed. |
| Compose smoke workflow | Done | `docker compose run --rm --build workbench-mcp-smoke` returned JSON status `ok`. |
| Remote CI | Done | GitHub Actions run `29778875177` succeeded for latest pushed Phase 7 commit `34fc81ae32e4404f01f3f460b43e6508e108421d`. Local final-audit fixes require a new CI run after push. |
| Linux symlink tests | Done | Remote CI step `Run symlink security tests explicitly on Linux` succeeded. |
| Demo | Done | `uv run python scripts\run-demo.py` returned `Demo status: ok`. |
| Documentation | Done | README, architecture, threat model, debugging, failure catalog, runbook, design decisions, security policy, contributing guide, changelog, release checklist, and project evidence updated. |
| Security review | Done | Final audit found and fixed bounded-output, artifact-read, Git hardening, and stale-CI documentation issues. |
| Secret scan | Done | Repository search for token/password/API-key/private-key patterns found no real secrets. |
| Known limitations | Done | README, threat model, SECURITY, and PROJECT_EVIDENCE document stdio-only support and sandbox limitations. |
| Release notes | Done | `CHANGELOG.md` has `0.1.0 - Pending Release` entries. |

## Not Done In Phase 7

| Item | Status | Reason |
| --- | --- | --- |
| Merge to `main` | Not done | Explicitly out of scope. |
| Git tag | Not done | Explicitly out of scope. |
| GitHub release | Not done | Explicitly out of scope. |
| Publish Python package | Not done | Explicitly out of scope. |
| Publish Docker image | Not done | Explicitly out of scope. |
| Independent final audit | Done locally | Final pre-release audit completed in this working tree; local fixes are not pushed by this checklist. |
| Remote CI for local final-audit fixes | Not done locally | Requires pushing the final-audit commit after review. |

## Release Notes Draft

`v0.1.0` prepares a secure stdio FastMCP workspace server with bounded file inspection,
search, guarded patching, allowlisted process/test execution, read-only Git status,
approved artifact collection, diagnostics, Docker packaging, CI, and a reproducible public
demo. Known limitations: stdio only, no HTTP, no production deployment, no package/image
publication, and not a complete arbitrary-code execution sandbox.
