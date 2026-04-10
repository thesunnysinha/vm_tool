# Quick Start

Deploy a Docker application to a remote server in under 2 minutes.

## 0. Verify Prerequisites

```bash
vm_tool doctor
```

This checks that Ansible, Docker, kubectl, Helm, SSH, and required Python packages are all available. Fix any reported issues before continuing.

## 1. Create a Profile

```bash
vm_tool config create-profile production \
  --environment production \
  --host 10.0.2.10 \
  --user ubuntu
```

## 2. Preview the Deployment

```bash
vm_tool deploy-docker --profile production --dry-run
```

## 3. Deploy

```bash
vm_tool deploy-docker \
  --profile production \
  --health-port 8000 \
  --health-url http://10.0.2.10:8000/health
```

## 4. Check History

```bash
vm_tool history --host 10.0.2.10
```

## 5. Rollback if Needed

```bash
vm_tool rollback --host 10.0.2.10
```

---

## What's Next?

- [Configuration & Profiles](../usage.md) — Advanced config options
- [Kubernetes Deployment](../guide/kubernetes.md) — Deploy to K8s clusters
- [Pipeline Generation](../generator.md) — Auto-generate CI/CD workflows
- [SSH Key Setup](../ssh-key-setup.md) — Configure SSH authentication
