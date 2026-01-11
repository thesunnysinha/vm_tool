# Pipeline Generator Examples

The pipeline generator creates production-ready GitHub Actions workflows with all vm_tool features.

## Basic Usage

```bash
# Generate with all features (recommended)
vm_tool generate-pipeline

# Minimal pipeline
vm_tool generate-pipeline --no-backup --no-rollback --no-health-checks
```

## Advanced Options

### Full-Featured Pipeline

```bash
vm_tool generate-pipeline \
  --platform github \
  --strategy docker \
  --health-checks \
  --backup \
  --rollback \
  --drift-detection \
  --dry-run-step \
  --monitoring \
  --health-port 8000 \
  --app-port 8000
```

### Custom Health Check URL

```bash
vm_tool generate-pipeline \
  --health-url "http://\${{ secrets.EC2_HOST }}:3000/api/health"
```

### Different Application Port

```bash
vm_tool generate-pipeline \
  --app-port 3000 \
  --health-port 3000
```

### Custom Output Path

```bash
vm_tool generate-pipeline \
  --output .github/workflows/production-deploy.yml
```

## Generated Features

The generator creates a workflow with:

### ✅ Always Included

- Checkout code
- Setup Python & vm_tool
- SSH configuration
- File copying to EC2
- Docker deployment
- Deployment verification
- Status notification

### 🎛️ Optional (Enabled by Default)

- **Health Checks** (`--health-checks`)

  - Port availability check
  - HTTP endpoint verification
  - Configurable timeout and retries

- **Backup** (`--backup`)

  - Pre-deployment backup
  - Automatic cleanup (keeps last 5)
  - Rollback capability

- **Rollback** (`--rollback`)

  - Automatic on deployment failure
  - Restores from latest backup
  - Verifies rollback success

- **Dry-Run** (`--dry-run-step`)
  - Preview deployment plan
  - Validate docker-compose config
  - No actual changes made

### 🔧 Optional (Disabled by Default)

- **Drift Detection** (`--drift-detection`)

  - Pre-deployment drift check
  - Warns about manual changes
  - Continues deployment with warning

- **Monitoring** (`--monitoring`)
  - Prometheus & Grafana setup
  - Metrics collection
  - Dashboard configuration

## Example Workflows

### 1. Production Deployment (Recommended)

```bash
vm_tool generate-pipeline \
  --health-checks \
  --backup \
  --rollback \
  --dry-run-step \
  --drift-detection \
  --app-port 8000
```

Features:

- ✅ Health checks after deployment
- ✅ Automatic backup before deployment
- ✅ Auto-rollback on failure
- ✅ Dry-run preview
- ✅ Drift detection warning

### 2. Fast Deployment (Development)

```bash
vm_tool generate-pipeline \
  --no-backup \
  --no-rollback \
  --no-dry-run-step \
  --health-checks
```

Features:

- ✅ Health checks only
- ❌ No backup (faster)
- ❌ No rollback
- ❌ No dry-run

### 3. Maximum Safety (Critical Systems)

```bash
vm_tool generate-pipeline \
  --health-checks \
  --backup \
  --rollback \
  --drift-detection \
  --dry-run-step \
  --monitoring \
  --health-port 8000 \
  --health-url "http://\${{ secrets.EC2_HOST }}:8000/health"
```

Features:

- ✅ All safety features enabled
- ✅ Monitoring included
- ✅ Custom health check URL
- ✅ Maximum reliability

## Customizing Generated Workflow

After generation, you can customize:

1. **Triggers**: Change `on:` section
2. **Environment Variables**: Add to `env:` section
3. **Steps**: Add custom steps
4. **Secrets**: Configure in GitHub Settings

## GitHub Secrets Required

Add these in: **Repository → Settings → Secrets → Actions**

| Secret        | Description     | Example                        |
| ------------- | --------------- | ------------------------------ |
| `EC2_HOST`    | EC2 instance IP | `54.123.45.67`                 |
| `EC2_USER`    | SSH username    | `ubuntu` or `deploy`           |
| `EC2_SSH_KEY` | Private SSH key | Content of `~/.ssh/id_ed25519` |

## Testing Generated Workflow

1. Generate workflow:

   ```bash
   vm_tool generate-pipeline
   ```

2. Review file:

   ```bash
   cat .github/workflows/deploy.yml
   ```

3. Commit and push:

   ```bash
   git add .github/workflows/deploy.yml
   git commit -m "Add deployment workflow"
   git push origin main
   ```

4. Watch in GitHub Actions tab

## Troubleshooting

**Workflow fails at SSH step?**

- Check EC2_SSH_KEY secret is correct
- Verify EC2 security group allows SSH (port 22)

**Health check fails?**

- Verify app is running on correct port
- Check EC2 security group allows app port
- Test health endpoint manually

**Backup fails?**

- Check disk space on EC2
- Verify ~/backups directory exists
- Check file permissions

## Next Steps

1. Customize workflow for your needs
2. Add staging environment
3. Set up monitoring
4. Configure notifications (Slack, Email)
