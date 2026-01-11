# VM Tool Module Guide

## Quick Reference

| Module | Purpose | Status |
|--------|---------|--------|
| **Core** | | |
| config.py | Configuration management | ✅ Production |
| state.py | State tracking | ✅ Production |
| history.py | Deployment history | ✅ Production |
| runner.py | Ansible execution | ✅ Production |
| health.py | Health checks | ✅ Production |
| **Strategies** | | |
| blue_green.py | Zero-downtime deployment | ✅ Production |
| canary.py | Gradual rollout | ✅ Production |
| ab_testing.py | A/B testing | ✅ Production |
| **Operations** | | |
| metrics.py | Metrics collection | ✅ Production |
| alerting.py | Multi-channel alerts | ✅ Production |
| benchmarking.py | Performance testing | ✅ Production |
| recovery.py | Error recovery | ✅ Production |
| reporting.py | Deployment reports | ✅ Production |
| validation.py | Pre-deployment checks | ✅ Production |
| **Enterprise** | | |
| rbac.py | Access control | ✅ Production |
| audit.py | Audit logging | ✅ Production |
| policy.py | Policy enforcement | ✅ Production |
| secrets.py | Secrets management | ✅ Production |
| cloud.py | Multi-cloud | 🔧 Framework |
| kubernetes.py | K8s support | 🔧 Framework |
| compliance.py | Compliance scanning | 🔧 Framework |
| **Integrations** | | |
| webhooks.py | HTTP notifications | ✅ Production |
| notifications.py | Email/SMS | ✅ Production |
| completion.py | Shell completion | ✅ Production |
| generator.py | Pipeline generation | ✅ Production |
| plugins.py | Plugin system | 🔧 Framework |

## Legend
- ✅ Production: Fully functional
- 🔧 Framework: Needs external dependencies
- 📝 Stub: Placeholder for future development
