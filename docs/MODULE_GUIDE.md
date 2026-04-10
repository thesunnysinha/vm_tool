# VM Tool Module Guide

## Quick Reference

| Subpackage | Module | Purpose | Status |
|-----------|--------|---------|--------|
| **core** | runner.py | `SetupRunner`, Ansible orchestration | Production |
| **core** | ansible.py | `AnsibleRunner` private wrapper | Production |
| **core** | state.py | State tracking | Production |
| **core** | history.py | Deployment history | Production |
| **deploy** | health.py | Health checks (port + HTTP, Tenacity retry) | Production |
| **deploy** | drift.py | Drift detection | Production |
| **deploy** | backup.py | Backup & restore | Production |
| **deploy/strategies** | blue_green.py | Zero-downtime deployment (`_switch_traffic` requires override) | Production (traffic-switching requires override) |
| **deploy/strategies** | canary.py | Gradual rollout (`_switch_traffic` requires override) | Production (traffic-switching requires override) |
| **deploy/strategies** | ab_testing.py | A/B testing (`_switch_traffic` requires override) | Production (traffic-switching requires override) |
| **infra** | cloud.py | AWS/GCP/Azure VM lifecycle (provision/status/terminate) | Production |
| **infra** | kubernetes.py | K8s manifests, Helm charts, pod status, scale, rollback | Production |
| **infra** | ssh.py | SSH utilities | Production |
| **security** | compliance.py | Static compliance scanning (Docker Compose + secrets) | Production |
| **security** | secrets.py | Secrets management, `.env` sync via python-dotenv | Production |
| **security** | rbac.py | Access control | Production |
| **security** | policy.py | Policy enforcement | Production |
| **security** | recovery.py | Error recovery (retry / circuit breaker) | Production |
| **observability** | metrics.py | Metrics collection | Production |
| **observability** | alerting.py | Multi-channel alerts | Production |
| **observability** | audit.py | Audit logging | Production |
| **observability** | reporting.py | Deployment reports | Production |
| **tools** | generator.py | CI/CD pipeline generation | Production |
| **tools** | release.py | Docker Compose release prep | Production |
| **tools** | completion.py | Shell completion | Production |
| **tools** | validation.py | Pre-deployment checks | Production |
| **integrations** | notifications.py | Email/SMS notifications | Production |
| **integrations** | webhooks.py | HTTP notifications | Production |
| **integrations** | plugins.py | Plugin system (registration works, loading pending) | Partial |
| **integrations** | benchmarking.py | Performance benchmarking | Production |
| **config** | config.py | Configuration management | Production |
| **handlers** | deploy.py | CLI deploy command handlers | Production |
| **handlers** | setup.py | CLI setup command handlers | Production |
| **handlers** | ops.py | CLI ops command handlers | Production |
| **handlers** | config.py | CLI config command handlers | Production |
| **handlers** | tools.py | CLI tools command handlers | Production |
| *(root)* | cli.py | CLI entry point | Production |
| *(root)* | console.py | Rich console output | Production |

## Legend

- **Production**: Fully functional and tested
- **Production (traffic-switching requires override)**: Core `_deploy_to_host` logic is implemented; subclasses must override `_switch_traffic` to activate routing changes
- **Partial**: Some features work, others are pending
