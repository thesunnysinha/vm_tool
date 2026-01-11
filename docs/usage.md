# Usage Guide

Complete guide to using vm_tool for deployment automation.

---

## Installation

```bash
pip install vm-tool
```

---

## CLI Commands

### Configuration Management

```bash
# Set configuration
vm_tool config set default-host 192.168.1.100
vm_tool config set default-user ubuntu

# Get configuration
vm_tool config get default-host

# List all configuration
vm_tool config list

# Unset configuration
vm_tool config unset default-host

# Create deployment profile
vm_tool config create-profile production \
  --environment production \
  --host 10.0.2.10 \
  --user ubuntu \
  --compose-file docker-compose.prod.yml

# List profiles
vm_tool config list-profiles

# Delete profile
vm_tool config delete-profile staging
```

---

### Docker Deployment

```bash
# Basic deployment
vm_tool deploy-docker \
  --host 192.168.1.100 \
  --user ubuntu \
  --compose-file docker-compose.yml

# Using profile
vm_tool deploy-docker --profile production

# With health checks
vm_tool deploy-docker \
  --profile production \
  --health-port 8000 \
  --health-url http://192.168.1.100:8000/health

# With environment file
vm_tool deploy-docker \
  --profile production \
  --env-file .env.production

# Force redeployment (skip idempotency check)
vm_tool deploy-docker --profile production --force

# Dry-run (preview only)
vm_tool deploy-docker --profile production --dry-run

# Custom deployment command
vm_tool deploy-docker \
  --host IP \
  --user USER \
  --deploy-command "./custom-deploy.sh"
```

---

### Deployment History & Rollback

```bash
# View deployment history
vm_tool history --host 192.168.1.100

# Limit results
vm_tool history --host 192.168.1.100 --limit 5

# Rollback to previous deployment
vm_tool rollback --host 192.168.1.100

# Rollback to specific deployment
vm_tool rollback --host 192.168.1.100 --to DEPLOYMENT_ID
```

---

### Drift Detection

```bash
# Check for configuration drift
vm_tool drift-check \
  --host 192.168.1.100 \
  --user ubuntu
```

---

### Backup & Restore

```bash
# Create backup
vm_tool backup create \
  --host 192.168.1.100 \
  --user ubuntu \
  --paths /app /etc/nginx /var/www

# List backups
vm_tool backup list

# List backups for specific host
vm_tool backup list --host 192.168.1.100

# Restore backup
vm_tool backup restore \
  --id BACKUP_ID \
  --host 192.168.1.100 \
  --user ubuntu
```

---

### Pipeline Generation

```bash
# Generate GitHub Actions workflow (default)
vm_tool generate-pipeline

# With all features
vm_tool generate-pipeline \
  --platform github \
  --strategy docker \
  --health-checks \
  --backup \
  --rollback \
  --drift-detection \
  --dry-run-step \
  --monitoring

# Custom health check
vm_tool generate-pipeline \
  --health-port 3000 \
  --health-url "http://\${{ secrets.EC2_HOST }}:3000/api/health"

# Custom output path
vm_tool generate-pipeline \
  --output .github/workflows/production.yml

# Minimal pipeline
vm_tool generate-pipeline \
  --no-backup \
  --no-rollback \
  --no-health-checks
```

---

### SSH Management

```bash
# Generate SSH configuration
vm_tool generate-ssh-config \
  --host 192.168.1.100 \
  --user ubuntu \
  --key-path ~/.ssh/id_rsa

# Validate SSH connection
vm_tool validate-ssh \
  --host 192.168.1.100 \
  --user ubuntu

# Validate secrets
vm_tool validate-secrets
```

---

### VM Setup (Ansible-based)

```bash
# Setup single VM
vm_tool setup \
  --github-username USER \
  --github-token TOKEN \
  --github-project-url https://github.com/user/repo \
  --dockerhub-username USER \
  --dockerhub-password PASS

# Setup cloud VMs
vm_tool setup-cloud \
  --ssh-configs config.json

# Setup Kubernetes (K3s) - Coming Soon
vm_tool setup-k8s --inventory inventory.yml

# Setup Monitoring - Coming Soon
vm_tool setup-monitoring --inventory inventory.yml
```

---

### Global Options

```bash
# Verbose output
vm_tool --verbose deploy-docker --profile prod

# Debug logging
vm_tool --debug deploy-docker --profile prod

# Version
vm_tool --version
```

---

## Features

### 1. Idempotent Deployments

Deployments are tracked by SHA256 hash. Only redeploys if changes detected.

```bash
# First run: deploys
vm_tool deploy-docker --profile prod

# Second run: skips (no changes)
vm_tool deploy-docker --profile prod

# Force redeploy
vm_tool deploy-docker --profile prod --force
```

### 2. Health Checks

Verify deployments with multiple check types:

```bash
# Port check
vm_tool deploy-docker --profile prod --health-port 8000

# HTTP endpoint check
vm_tool deploy-docker --profile prod \
  --health-url http://IP:8000/health

# Both
vm_tool deploy-docker --profile prod \
  --health-port 8000 \
  --health-url http://IP:8000/health
```

### 3. Multi-Environment Safety

Production deployments require confirmation:

```bash
# Creates production profile
vm_tool config create-profile prod --environment production

# Deployment prompts for confirmation
vm_tool deploy-docker --profile prod

# Skip confirmation
vm_tool deploy-docker --profile prod --force
```

### 4. Deployment History

All deployments are recorded with:

- Timestamp
- Git commit (if available)
- Deployment status
- Configuration used

```bash
vm_tool history --host IP
```

### 5. One-Command Rollback

```bash
# Rollback to previous
vm_tool rollback --host IP

# Rollback to specific deployment
vm_tool rollback --host IP --to DEPLOYMENT_ID
```

### 6. Drift Detection

Detect manual server changes:

```bash
vm_tool drift-check --host IP --user USER
```

### 7. Backup & Restore

Automated disaster recovery:

```bash
# Backup
vm_tool backup create --host IP --paths /app

# Restore
vm_tool backup restore --id ID --host IP
```

### 8. Dry-Run

Preview deployments:

```bash
vm_tool deploy-docker --profile prod --dry-run
```

### 9. Configuration Profiles

Save deployment configurations:

```bash
vm_tool config create-profile prod \
  --environment production \
  --host 10.0.2.10 \
  --user ubuntu \
  --compose-file docker-compose.prod.yml

vm_tool deploy-docker --profile prod
```

---

## Ansible Integration

vm_tool uses Ansible under the hood for production-grade deployments.

**Playbooks**: `vm_tool/vm_setup/`

- `main.yml` - Main playbook
- `push_code.yml` - Code deployment

**Inventory**: Auto-generated or custom

**Benefits**:

- Idempotent operations
- Proper error handling
- State tracking
- Rollback support

---

## Configuration Files

### Config Location

`~/.vm_tool/config.json`

### State Files

- Deployment state: `~/.vm_tool/deployment_state.json`
- History: `~/.vm_tool/deployment_history.json`
- Drift state: `~/.vm_tool/drift_state.json`
- Backups: `~/.vm_tool/backups.json`

---

## Examples

### Production Deployment Workflow

```bash
# 1. Create profile
vm_tool config create-profile prod \
  --environment production \
  --host 10.0.2.10 \
  --user ubuntu

# 2. Dry-run
vm_tool deploy-docker --profile prod --dry-run

# 3. Deploy with health checks
vm_tool deploy-docker --profile prod \
  --health-port 8000 \
  --health-url http://10.0.2.10:8000/health

# 4. Verify
vm_tool history --host 10.0.2.10

# 5. If issues, rollback
vm_tool rollback --host 10.0.2.10
```

### CI/CD Integration

```bash
# Generate workflow
vm_tool generate-pipeline

# Commit and push
git add .github/workflows/deploy.yml
git commit -m "Add deployment workflow"
git push origin main
```

---

## Troubleshooting

### Deployment Fails

```bash
# Check history
vm_tool history --host IP

# Rollback
vm_tool rollback --host IP

# Try with verbose logging
vm_tool --verbose deploy-docker --profile prod
```

### Health Check Fails

```bash
# Test endpoint manually
curl http://IP:8000/health

# Deploy without health checks
vm_tool deploy-docker --profile prod --no-health-check
```

### SSH Issues

```bash
# Validate SSH
vm_tool validate-ssh --host IP --user USER

# Check SSH config
cat ~/.ssh/config
```

---

## Next Steps

- [Features Documentation](features.md)
- [Pipeline Generator](generator.md)
- [EC2 Deployment Guide](ec2-github-actions-guide.md)
- [SSH Key Setup](ssh-key-setup.md)
