# VM Tool Module Guide

## Quick Reference

| Module | Purpose | Status |
|--------|---------|--------|
| **Core** | | |
| config.py | Configuration management | Production |
| state.py | State tracking | Production |
| history.py | Deployment history | Production |
| runner.py | Ansible execution | Production |
| health.py | Health checks | Production |
| ssh.py | SSH utilities | Production |
| cli.py | CLI entry point | Production |
| **Deployment** | | |
| generator.py | Pipeline generation | Production |
| release.py | Docker Compose release prep | Production |
| validation.py | Pre-deployment checks | Production |
| **Strategies** | | |
| blue_green.py | Zero-downtime deployment | Scaffold (not wired to CLI) |
| canary.py | Gradual rollout | Scaffold (not wired to CLI) |
| ab_testing.py | A/B testing | Scaffold (not wired to CLI) |
| **Operations** | | |
| metrics.py | Metrics collection | Production |
| alerting.py | Multi-channel alerts | Production |
| benchmarking.py | Performance testing | Production |
| recovery.py | Error recovery (retry/circuit breaker) | Production (rollback pending) |
| reporting.py | Deployment reports | Production |
| notifications.py | Email/SMS notifications | Production |
| webhooks.py | HTTP notifications | Production |
| **Security & Policy** | | |
| rbac.py | Access control | Production |
| audit.py | Audit logging | Production |
| policy.py | Policy enforcement | Production |
| secrets.py | Secrets management | Production |
| **Cloud & K8s** | | |
| cloud.py | Multi-cloud (AWS/GCP/Azure) | Not implemented (raises on use) |
| kubernetes.py | K8s/Helm/GitOps | Not implemented (raises on use) |
| compliance.py | Compliance scanning | Not implemented (raises on use) |
| **Integrations** | | |
| completion.py | Shell completion | Production |
| drift.py | Drift detection | Production |
| backup.py | Backup & restore | Production |
| plugins.py | Plugin system | Partial (registration works, loading pending) |

## Legend
- **Production**: Fully functional and tested
- **Scaffold**: Code structure exists but core logic is not connected to CLI
- **Partial**: Some features work, others are pending
- **Not implemented**: Raises `NotImplementedError` on use — safe to import but will fail at runtime
