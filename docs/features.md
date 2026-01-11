# Features

## Overview

VM Tool is a production-grade deployment platform with enterprise features for Docker-based applications.

---

## Phase 1: Foundation Features

### 1. Configuration Management ⭐⭐⭐⭐⭐

Save defaults and create deployment profiles to avoid re-entering settings.

**Commands**:

```bash
vm_tool config set <key> <value>
vm_tool config get <key>
vm_tool config list
vm_tool config create-profile <name> --environment <env> --host <ip>
vm_tool config list-profiles
vm_tool config delete-profile <name>
```

**Use Cases**:

- Multi-environment deployments
- Team collaboration
- Consistent configurations

---

### 2. Idempotent Deployments ⭐⭐⭐⭐⭐

Safe to run multiple times - only redeploys when changes are detected.

**How it Works**:

- Computes SHA256 hash of docker-compose.yml
- Compares with last deployment
- Skips if no changes (unless `--force` used)

**Commands**:

```bash
vm_tool deploy-docker --profile prod
vm_tool deploy-docker --profile prod --force
```

**Benefits**:

- Safe CI/CD retries
- Prevents unnecessary downtime
- Production reliability

---

### 3. Health Checks & Smoke Tests ⭐⭐⭐⭐⭐

Verify deployments actually work after completion.

**Check Types**:

- **Port Checks**: Wait for port availability
- **HTTP Checks**: Verify endpoint returns expected status
- **Custom Checks**: Run arbitrary commands via SSH

**Commands**:

```bash
vm_tool deploy-docker --profile prod --health-port 8000
vm_tool deploy-docker --profile prod --health-url http://IP:8000/health
vm_tool deploy-docker --profile prod --health-check "docker ps | grep web"
```

**Benefits**:

- Catch deployment failures immediately
- Automated verification
- Confidence in deployments

---

### 4. Multi-Environment Support ⭐⭐⭐⭐

Environment-tagged profiles with production safety checks.

**Environments**: `development`, `staging`, `production`

**Commands**:

```bash
vm_tool config create-profile dev --environment development --host IP
vm_tool config create-profile prod --environment production --host IP
vm_tool deploy-docker --profile prod  # Requires confirmation
```

**Safety Features**:

- Production confirmation prompts
- Environment-specific settings
- Prevent accidental deployments

---

### 5. Verbose/Debug Logging ⭐⭐⭐⭐

Control logging verbosity for easier troubleshooting.

**Levels**:

- **Default**: WARNING only
- **Verbose (`-v`)**: INFO + WARNING + ERROR
- **Debug (`-d`)**: DEBUG + INFO + WARNING + ERROR

**Commands**:

```bash
vm_tool --verbose deploy-docker --profile prod
vm_tool --debug deploy-docker --profile prod
```

---

## Phase 2: Safety & Reliability Features

### 6. Deployment History & Rollback ⭐⭐⭐⭐⭐

Track all deployments and enable one-command rollback.

**Features**:

- Tracks all deployments with timestamps
- Records git commits
- Stores deployment status
- Keeps last 100 deployments

**Commands**:

```bash
vm_tool history --host IP
vm_tool history --host IP --limit 20
vm_tool rollback --host IP
vm_tool rollback --host IP --to DEPLOYMENT_ID
```

**Use Cases**:

- Revert bad deployments
- Audit trail
- Compliance requirements

---

### 7. Deployment Dry-Run ⭐⭐⭐⭐

Preview deployments before executing.

**Shows**:

- Target host and user
- Compose file contents
- Environment variables
- Custom commands

**Commands**:

```bash
vm_tool deploy-docker --profile prod --dry-run
```

**Benefits**:

- Preview changes
- Catch configuration errors
- Team review before deployment

---

### 8. Drift Detection ⭐⭐⭐⭐

Catch manual server configuration changes.

**How it Works**:

- Records expected file hashes
- Compares with actual server state
- Reports modifications and deletions

**Commands**:

```bash
vm_tool drift-check --host IP --user USER
```

**Use Cases**:

- Security compliance
- Configuration auditing
- Detect unauthorized changes

---

### 9. Backup & Restore ⭐⭐⭐⭐

Automated disaster recovery with backup management.

**Features**:

- Create tar.gz backups
- Store metadata (size, timestamp, paths)
- List and filter backups
- Restore to any host

**Commands**:

```bash
vm_tool backup create --host IP --paths /app /etc/nginx
vm_tool backup list --host IP
vm_tool backup restore --id BACKUP_ID --host IP
```

**Use Cases**:

- Pre-deployment backups
- Disaster recovery
- Migration between servers

---

## Coming Soon

### Phase 3: Testing & Quality

- Integration Testing Framework
- Load Testing Support
- Security Scanning
- Code Quality Checks
- Test Coverage Reports

### Phase 4: Advanced Deployments

- Blue-Green Deployments
- Canary Deployments
- A/B Testing
- Traffic Splitting
- Auto-Scaling

### Phase 5: Security & Compliance

- Secrets Management (Vault/AWS)
- RBAC & Permissions
- Audit Logging
- Compliance Reports
- Vulnerability Scanning

---

## Feature Comparison

| Feature                | Basic Tools | VM Tool |
| ---------------------- | ----------- | ------- |
| Docker Deployment      | ✅          | ✅      |
| Configuration Profiles | ❌          | ✅      |
| Idempotent Deployments | ❌          | ✅      |
| Health Checks          | ❌          | ✅      |
| Rollback               | ❌          | ✅      |
| Drift Detection        | ❌          | ✅      |
| Backup/Restore         | ❌          | ✅      |
| Multi-Environment      | ❌          | ✅      |
| Dry-Run                | ❌          | ✅      |
| History Tracking       | ❌          | ✅      |
