# Usage Guide

Complete guide to using vm_tool for production deployments.

---

## Quick Start

```bash
# Install
pip install vm-tool

# Create a profile
vm_tool config create-profile production \
  --environment production \
  --host 10.0.2.10 \
  --user ubuntu

# Deploy
vm_tool deploy-docker --profile production
```

---

## Configuration Management

### Creating Profiles

```bash
# Development profile
vm_tool config create-profile dev \
  --environment development \
  --host 192.168.1.100 \
  --user ubuntu \
  --compose-file docker-compose.dev.yml

# Staging profile
vm_tool config create-profile staging \
  --environment staging \
  --host 10.0.1.5 \
  --user deploy

# Production profile
vm_tool config create-profile prod \
  --environment production \
  --host 10.0.2.10 \
  --user prod
```

### Managing Configuration

```bash
# Set defaults
vm_tool config set default-host 192.168.1.100
vm_tool config set default-user ubuntu

# Get values
vm_tool config get default-host

# List all config
vm_tool config list

# List profiles
vm_tool config list-profiles

# Delete profile
vm_tool config delete-profile old-profile
```

---

## Docker Deployment

### Basic Deployment

```bash
# Deploy to specific host
vm_tool deploy-docker \
  --host 192.168.1.100 \
  --user ubuntu \
  --compose-file docker-compose.yml

# Deploy using profile
vm_tool deploy-docker --profile production
```

### Deployment with Health Checks

```bash
# Port check
vm_tool deploy-docker \
  --profile production \
  --health-port 8000

# HTTP endpoint check
vm_tool deploy-docker \
  --profile production \
  --health-url http://10.0.2.10:8000/health

# Custom health check
vm_tool deploy-docker \
  --profile production \
  --health-check "docker ps | grep web"

# Multiple checks
vm_tool deploy-docker \
  --profile production \
  --health-port 8000 \
  --health-url http://10.0.2.10:8000/api/status \
  --health-check "curl -f http://localhost:8000/ready"
```

### Dry-Run Mode

Preview deployment without making changes:

```bash
vm_tool deploy-docker --profile production --dry-run
```

Output:

```
🔍 DRY-RUN MODE - No changes will be made

📋 Deployment Plan:
   Target Host: 10.0.2.10
   SSH User: prod
   Compose File: docker-compose.yml
   Inventory: inventory.yml

📄 Compose File Contents (docker-compose.yml):
     1 | version: '3'
     2 | services:
     3 |   web:
     4 |     image: nginx:latest
     ...

✅ Dry-run complete. Use without --dry-run to deploy.
```

### Force Redeployment

```bash
# Force redeploy even if no changes
vm_tool deploy-docker --profile production --force
```

---

## Deployment History & Rollback

### View History

```bash
# All deployments
vm_tool history

# Filter by host
vm_tool history --host 10.0.2.10

# Show more entries
vm_tool history --host 10.0.2.10 --limit 20
```

Output:

```
📜 Deployment History (showing 3 deployments):

✅ 20260111_195500 - 2026-01-11T19:55:00
   Host: 10.0.2.10
   Service: default
   Compose: docker-compose.yml
   Git: a1b2c3d4

✅ 20260111_143000 - 2026-01-11T14:30:00
   Host: 10.0.2.10
   Service: default
   Compose: docker-compose.yml
   Git: e5f6g7h8
```

### Rollback

```bash
# Rollback to previous deployment
vm_tool rollback --host 10.0.2.10

# Rollback to specific deployment
vm_tool rollback --host 10.0.2.10 --to 20260111_143000
```

---

## Drift Detection

Check for manual configuration changes:

```bash
vm_tool drift-check --host 10.0.2.10 --user ubuntu
```

Output:

```
⚠️  Drift Detected on 10.0.2.10:

🔄 /etc/nginx/nginx.conf
   Status: modified
   Expected: a1b2c3d4e5f6g7h8...
   Actual: x9y8z7w6v5u4t3s2...

❌ /app/config.json
   Status: deleted
   Expected: 1a2b3c4d5e6f7g8h...

Found 2 file(s) with drift
```

---

## Backup & Restore

### Create Backup

```bash
vm_tool backup create \
  --host 10.0.2.10 \
  --user ubuntu \
  --paths /app /etc/nginx /var/www
```

### List Backups

```bash
# All backups
vm_tool backup list

# Filter by host
vm_tool backup list --host 10.0.2.10
```

Output:

```
📦 Available Backups (3):

  20260111_200000
    Host: 10.0.2.10
    Time: 2026-01-11T20:00:00
    Size: 45.32 MB
    Paths: /app, /etc/nginx

  20260111_150000
    Host: 10.0.2.10
    Time: 2026-01-11T15:00:00
    Size: 42.18 MB
    Paths: /app, /etc/nginx
```

### Restore Backup

```bash
vm_tool backup restore \
  --id 20260111_200000 \
  --host 10.0.2.10 \
  --user ubuntu
```

---

## Pipeline Generation

Generate GitHub Actions workflow:

```bash
vm_tool generate-pipeline \
  --platform github \
  --strategy docker \
  --monitoring
```

---

## Logging & Debugging

### Verbose Mode

```bash
vm_tool --verbose deploy-docker --profile production
```

### Debug Mode

```bash
vm_tool --debug deploy-docker --profile production
```

Output includes detailed logging:

```
🐛 Debug logging enabled
DEBUG: Loading config from /Users/user/.vm_tool/config.json
DEBUG: Computing hash of docker-compose.yml
INFO: Deployment is up-to-date
```

---

## Best Practices

### 1. Always Use Profiles

```bash
# ✅ Good
vm_tool deploy-docker --profile production

# ❌ Avoid
vm_tool deploy-docker --host IP --user USER ...
```

### 2. Dry-Run First

```bash
# Always preview production deployments
vm_tool deploy-docker --profile production --dry-run
vm_tool deploy-docker --profile production
```

### 3. Enable Health Checks

```bash
vm_tool deploy-docker \
  --profile production \
  --health-port 8000 \
  --health-url http://IP:8000/health
```

### 4. Regular Backups

```bash
# Before major deployments
vm_tool backup create --host IP --paths /app /etc
vm_tool deploy-docker --profile production
```

### 5. Monitor Drift

```bash
# Weekly drift checks
vm_tool drift-check --host IP
```

---

## Troubleshooting

### Deployment Fails

1. Check with dry-run: `vm_tool deploy-docker --profile prod --dry-run`
2. Enable debug: `vm_tool --debug deploy-docker --profile prod`
3. Verify SSH access: `ssh user@host`
4. Check compose file: `docker-compose config`

### Health Checks Fail

1. Verify port is open: `nc -zv host port`
2. Check service logs: `ssh user@host docker-compose logs`
3. Test endpoint manually: `curl http://host:port/health`

### Rollback Issues

1. View history: `vm_tool history --host IP`
2. Verify backup exists: `vm_tool backup list --host IP`
3. Check SSH access and permissions

---

## Advanced Usage

### Custom Deployment Commands

```bash
vm_tool deploy-docker \
  --profile production \
  --deploy-command "docker-compose up -d --build"
```

### Environment Files

```bash
vm_tool deploy-docker \
  --profile production \
  --env-file .env.production
```

### Production Deployment Workflow

```bash
# 1. Create backup
vm_tool backup create --host IP --paths /app

# 2. Dry-run
vm_tool deploy-docker --profile prod --dry-run

# 3. Deploy with health checks
vm_tool deploy-docker \
  --profile prod \
  --health-port 8000 \
  --health-url http://IP:8000/health

# 4. Verify deployment
vm_tool history --host IP

# 5. Check for drift
vm_tool drift-check --host IP
```
