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

Verify deployments with port, HTTP, and custom checks. Health checks use Tenacity retry with configurable timeouts (`wait_for_port` and `wait_for_http`).

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

Control output verbosity. All output is rendered with Rich (colored tables, spinners, styled messages).

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

## Phase 3: Advanced Deployment ✅

### 10. Deployment Strategies

Blue-green, canary, and A/B testing strategies are implemented in `vm_tool.deploy.strategies`. Each strategy implements `_deploy_to_host`; subclasses must override `_switch_traffic` to wire in their own load-balancer or routing logic.

### 11. Multi-Cloud VM Provisioning

Provision, inspect, and terminate VMs on AWS, GCP, and Azure via `vm_tool.infra.cloud`. Requires the corresponding extra (`vm-tool[aws]`, `vm-tool[gcp]`, or `vm-tool[azure]`).

### 12. Kubernetes Support

Full Kubernetes support via `vm_tool.infra.kubernetes`: manifest apply, Helm chart deploy, pod status, scale, and rollback.

```bash
vm_tool deploy-k8s --method manifest --manifest k8s/app.yml --namespace prod
vm_tool deploy-k8s --method helm --helm-chart ./chart --helm-release myapp
```

### 13. Compliance Scanning

Static analysis for Docker Compose files and secrets via `vm_tool.security.compliance`. No network access required.

---

## Phase 4: Operations & Observability ✅

### 14. Prerequisites Check

Verify all runtime dependencies before deploying.

```bash
vm_tool doctor
```

### 15. Deployment Status Dashboard

Show current deployment state for all tracked hosts.

```bash
vm_tool status
```

### 16. Secrets Sync

Sync a local `.env` file (parsed via `python-dotenv`) to GitHub Secrets.

```bash
vm_tool secrets sync --env-file .env --repo owner/repo
```

### 17. CI/CD Pipeline Generation

```bash
vm_tool generate-pipeline --platform github
```

---

## Roadmap

- GitOps Integration (ArgoCD/Flux)
- Web dashboard
- Notification webhooks (Slack/Discord)
