# Secrets Management (Autonomyx Standard)

Autonomyx AgentBook supports environment variables, but production deployments should use managed secret storage.

## Approved secret managers

- `secrets.unboxd.cloud`
- `infisical.openautonomyx.com`

## Migration policy

1. Store all sensitive values in one of the approved secret managers.
2. Inject secrets at runtime (container env or mounted files).
3. Keep `.env` files for local development only.
4. Never commit real keys, tokens, passwords, or certificates.

## Secret classification

### Must be managed secrets
- `OPEN_NOTEBOOK_ENCRYPTION_KEY`
- `OPEN_NOTEBOOK_PASSWORD`
- `SURREAL_PASSWORD`
- AI provider API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.)
- OAuth/JWT secrets when enabled

### Non-secret configuration
- `SURREAL_URL`
- `SURREAL_USER`
- `SURREAL_NAMESPACE`
- `SURREAL_DATABASE`
- `API_URL`
- `OLLAMA_BASE_URL`

## Runtime injection patterns

### Pattern A: env injection from secret manager
- Sync secret material from `secrets.unboxd.cloud` or `infisical.openautonomyx.com` into runtime environment.
- Keep only non-sensitive defaults in `.env.example`.

### Pattern B: file-based injection (`_FILE`)
Use Docker/Kubernetes mounted files and `_FILE`-style environment variables where supported:
- `OPEN_NOTEBOOK_PASSWORD_FILE`
- `OPEN_NOTEBOOK_ENCRYPTION_KEY_FILE`

## Operational checklist

- [ ] Confirm secret source of truth is one approved manager.
- [ ] Remove stale copies from CI variable sets and local scripts.
- [ ] Rotate any default/legacy values before go-live.
- [ ] Enforce masked logs for all secret-like variables.
- [ ] Verify no secrets are present in git history, issue templates, or screenshots.

## Notes

Environment variable names in code remain backward-compatible today (for example `OPEN_NOTEBOOK_*`). A future major migration can rename env variables to `AUTONOMYX_*` without silent API/ops breakage.
