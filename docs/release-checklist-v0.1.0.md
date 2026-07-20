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
| Format check | Done | `uv run ruff format --check .` returned `48 files already formatted`. |
| Type checking | Done | `uv run mypy src` returned `Success: no issues found in 28 source files`. |
| Tests | Done | `uv run pytest -rs` returned `89 passed, 4 skipped in 15.75s`. |
| Coverage | Done | `uv run pytest --cov=workbench_mcp --cov-report=term-missing` returned display coverage `84%`. |
| Package build | Done | `uv build` produced `dist\workbench_mcp-0.1.0.tar.gz` and `dist\workbench_mcp-0.1.0-py3-none-any.whl`. |
| MCP construction smoke | Done | `tests\unit\test_mcp_server.py::test_server_startup_succeeds` passed. |
| Real MCP client/server smoke | Done | `tests\e2e\test_mcp_stdio.py` passed serially. |
| Docker build | Done | `docker build --progress=plain -t workbench-mcp:local .` succeeded after Docker Desktop recovery. |
| Container smoke | Done | `uv run python scripts\run-container-smoke.py --image workbench-mcp:local` returned JSON status `ok`. |
| Compose verification | Done | `docker compose config` passed. |
| Compose smoke workflow | Done | `docker compose run --rm --build workbench-mcp-smoke` returned JSON status `ok`. |
| Remote CI | Done | GitHub Actions run `29775378084` succeeded for commit `4efddd89c8aed22310f3dc14a74ed1e215ec21e1`. |
| Linux symlink tests | Done | Remote CI step `Run symlink security tests explicitly on Linux` succeeded. |
| Demo | Done | `uv run python scripts\run-demo.py` returned `Demo status: ok`. |
| Documentation | Done | README, architecture, threat model, debugging, failure catalog, runbook, design decisions, security policy, contributing guide, changelog, release checklist, and project evidence updated. |
| Security review | Done | Threat model maps current mitigations to source and tests; unsupported-claim/security searches reviewed. |
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
| Independent final audit | Not started | Explicitly out of scope until after Phase 7. |
| Remote CI for the Phase 7 commit | Not done locally | Requires pushing the Phase 7 commit after this checklist is committed. |

## Release Notes Draft

`v0.1.0` prepares a secure stdio FastMCP workspace server with bounded file inspection,
search, guarded patching, allowlisted process/test execution, read-only Git status,
approved artifact collection, diagnostics, Docker packaging, CI, and a reproducible public
demo. Known limitations: stdio only, no HTTP, no production deployment, no package/image
publication, and not a complete arbitrary-code execution sandbox.
