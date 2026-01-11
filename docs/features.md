# Features Documentation

Complete list of vm_tool features with usage examples.

---

## Phase 1: Foundation Features ✅

### 1. Configuration Management

Save defaults and create deployment profiles.

```bash
vm_tool config set default-host 192.168.1.100
vm_tool config create-profile prod --environment production --host IP
```

### 2. Idempotent Deployments

Safe to run multiple times - only redeploys on changes.

```bash
vm_tool deploy-docker --profile prod
vm_tool deploy-docker --profile prod --force  # Force redeploy
```

### 3. Health Checks & Smoke Tests

Verify deployments with port, HTTP, and custom checks.

```bash
vm_tool deploy-docker --profile prod --health-port 8000
vm_tool deploy-docker --profile prod --health-url http://IP:8000/health
```

### 4. Multi-Environment Support

Environment-tagged profiles with production safety.

```bash
vm_tool config create-profile dev --environment development
vm_tool config create-profile prod --environment production
```

### 5. Verbose/Debug Logging

Control output verbosity.

```bash
vm_tool --verbose deploy-docker --profile prod
vm_tool --debug deploy-docker --profile prod
```

---

## Phase 2: Safety & Reliability ✅

### 6. Deployment History & Rollback

Track all deployments and rollback with one command.

```bash
vm_tool history --host IP
vm_tool rollback --host IP
vm_tool rollback --host IP --to DEPLOYMENT_ID
```

### 7. Deployment Dry-Run

Preview deployments before executing.

```bash
vm_tool deploy-docker --profile prod --dry-run
```

### 8. Drift Detection

Catch manual server configuration changes.

```bash
vm_tool drift-check --host IP
```

### 9. Backup & Restore

Automated disaster recovery.

```bash
vm_tool backup create --host IP --paths /app /etc/nginx
vm_tool backup list --host IP
vm_tool backup restore --id BACKUP_ID --host IP
```

---

## Coming Soon

- Atomic Deployments
- Blue-Green Deployments
- Secrets Management
- Auto-Scaling
- GitOps Integration

See [implementation_plan.md](https://github.com/thesunnysinha/vm_tool) for full roadmap.
