# Secrets Management

vm_tool provides tools for syncing local `.env` files to GitHub Secrets and hydrating environment files during deployment.

## Sync to GitHub Secrets

Push local `.env` variables to GitHub repository secrets:

```bash
vm_tool secrets sync --env-file .env.production --repo owner/repo
```

This reads each `KEY=VALUE` pair from the file and uploads it as a GitHub Secret. You'll be prompted to confirm before uploading.

## Hydrate Environment Files

In CI/CD, reconstruct `.env` files from GitHub Secrets:

```bash
vm_tool hydrate-env \
  --compose-file docker-compose.yml \
  --secrets '{"DB_PASSWORD": "secret123", "API_KEY": "abc"}' \
  --project-root .
```

This scans your `docker-compose.yml` for `env_file` references and creates the files with the provided secrets.

## Validate Secrets

Check that required secrets are configured:

```bash
vm_tool validate-secrets
```

## Best Practices

!!! warning "Never commit secrets"
    Always use `.env` files (listed in `.gitignore`) or GitHub Secrets. Never hardcode credentials in `docker-compose.yml`.

- Use `vm_tool secrets sync` to keep GitHub Secrets in sync with local `.env` files
- Use `vm_tool hydrate-env` in CI/CD to reconstruct `.env` files at deploy time
- Use environment-specific files: `.env.development`, `.env.staging`, `.env.production`
