# Autonomyx Migration Audit Report

## Scope
Repository-wide branding, documentation, configuration, secrets guidance, and reference audit.

## Status Legend
- **Updated**: Changed in this migration.
- **Flagged**: Identified risk or inconsistency.
- **Unresolved**: Requires follow-up decision or infrastructure ownership.
- **Blocked**: Cannot safely change without breaking runtime compatibility.

## 1) Repository audit summary
- Updated major outward-facing product references from legacy naming to **Autonomyx AgentBook** across README, docs, examples, issue templates, workflow text, and frontend localization text.
- Added explicit secrets-management guidance aligned to:
  - `secrets.unboxd.cloud`
  - `infisical.openautonomyx.com`
- Updated API metadata/title text to Autonomyx naming.
- Performed deep scans for old branding and secret patterns.

## 2) Branding/reference findings
### Updated
- Legacy human-facing references in:
  - `README.md`, `README.dev.md`, `CONTRIBUTING.md`
  - `docs/**`
  - `examples/**`
  - `.github/**` templates and selected workflows
  - `frontend/src/lib/locales/**`
  - `frontend` UI links that still pointed to legacy org/project

### Flagged
- Internal Python package/module and record naming remains `open_notebook` in runtime code and DB records.

### Unresolved / Blocked
- Renaming `open_notebook` package and SurrealDB record IDs would be a breaking migration requiring coordinated DB/data and import path transition.

## 3) README issues and updates
### Updated
- Product framing and naming moved to Autonomyx AgentBook.
- Legacy org/image references updated where feasible.

### Flagged
- Some ecosystem badges and third-party historical charts still include legacy repository slug semantics.

## 4) License issues and updates
### Flagged
- `LICENSE` remains MIT but no explicit Autonomyx copyright notice was added.
- Requires legal/ownership decision.

## 5) Documentation issues and updates
### Updated
- Broad docs pass performed across `docs/` and `examples/` for branding normalization.
- Added dedicated secrets management doc: `docs/5-CONFIGURATION/secrets-management.md`.

### Flagged
- Some documentation still references legacy env variable names intentionally because code compatibility remains (`OPEN_NOTEBOOK_*`).

## 6) API contract issues and updates
### Updated
- API metadata title/description and root health text now use Autonomyx naming.

### Flagged
- Route paths remain notebook-centric (`/notebooks`) for compatibility and existing frontend contracts.

## 7) Deep-scan findings
- Legacy references were found in docs, templates, locales, scripts, and operational files.
- Secrets patterns mostly configuration placeholders, not hardcoded live secrets.

## 8) Missing links/resources and broken references
### Unresolved
- New authoritative public repo URL/org, docs site URL, and assistant URLs are not centrally defined.
- Some links were moved to Autonomyx placeholders but require ownership confirmation.

## 9) Secrets/key audit
### Findings
- Secret-related env vars include encryption keys, provider API keys, DB password, and auth password.
- No obvious committed real API keys discovered in source scan.

### Risks
- Legacy docs included direct env usage patterns that can encourage local secret sprawl.

## 10) Secret migration plan
### `secrets.unboxd.cloud`
1. Create project and environments (dev/stage/prod).
2. Register secret groups: `platform`, `database`, `ai-providers`, `auth`.
3. Inject secrets into runtime containers using env or mounted files.

### `infisical.openautonomyx.com`
1. Mirror same secret taxonomy.
2. Configure least-privilege machine identities for CI/CD and runtime.
3. Enable rotation schedules and audit logs.

### Shared controls
- Keep `.env.example` non-sensitive.
- Prefer `_FILE` patterns for containerized deployments.
- Rotate any inherited legacy values before production cutover.

## 11) Internal dependency map
- `api/` depends on `open_notebook/` domain, graph, and utility modules.
- `frontend/` depends on API routes and typed contracts in `frontend/src/lib`.
- `commands/` and background job workflows depend on domain + graphs + database repo functions.
- `open_notebook/database` migrations and repository layer underpin all modules.

## 12) External dependency map
- Python: FastAPI, Uvicorn, SurrealDB client, LangGraph/LangChain ecosystem, Esperanto.
- Frontend: Next.js, React, TanStack Query, Radix UI, i18next.
- Infra: Docker/Docker Compose, GitHub Actions, GHCR/Docker Hub workflows.
- AI providers: OpenAI, Anthropic, Google, Groq, Mistral, DeepSeek, xAI, OpenRouter, Voyage, ElevenLabs, Dashscope, Minimax.

## 13) Files changed
See git history for full list; migration touched documentation, templates, frontend localization, config examples, and selected metadata endpoints.

## 14) Remaining unresolved issues
1. Runtime package/module namespace remains `open_notebook`.
2. SurrealDB namespace/database defaults may still be legacy in some runtime paths.
3. Full CI registry/org migration requires confirmed Autonomyx container registry ownership.
4. Full link canonicalization depends on confirmed public URLs.

## 15) Recommended follow-up tasks
1. Execute a breaking-change plan to rename Python package and DB identifiers from `open_notebook` to `autonomyx_agentbook`.
2. Finalize canonical public URLs and update all remaining placeholders/legacy links.
3. Add CI secret-manager integration with workload identity from approved secret stores.
4. Add automated lint rule/check to fail PRs containing legacy brand strings.
