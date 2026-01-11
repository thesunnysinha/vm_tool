# Welcome to VM Tool

A **production-grade deployment platform** with enterprise features for Docker-based applications.

---

## 🚀 Features

### Phase 1: Foundation

- ✅ **Configuration Management** - Profiles and defaults
- ✅ **Idempotent Deployments** - Safe to run multiple times
- ✅ **Health Checks** - Port, HTTP, and custom checks
- ✅ **Multi-Environment** - Dev/staging/prod with safety
- ✅ **Verbose Logging** - Debug and verbose modes

### Phase 2: Safety & Reliability

- ✅ **Deployment History & Rollback** - One-command rollback
- ✅ **Dry-Run** - Preview before deploy
- ✅ **Drift Detection** - Catch manual changes
- ✅ **Backup & Restore** - Disaster recovery

### Core Technology

- 🔧 **Ansible-Based** - Production-grade automation
- 🔧 **Idempotent** - Safe to run multiple times
- 🔧 **Scalable** - Multi-host support

---

## ⚡ Quick Start

```bash
# Install
pip install vm-tool

# Create profile
vm_tool config create-profile production \
  --environment production \
  --host 10.0.2.10 \
  --user ubuntu

# Deploy with health checks
vm_tool deploy-docker \
  --profile production \
  --health-port 8000

# View history
vm_tool history --host 10.0.2.10

# Rollback if needed
vm_tool rollback --host 10.0.2.10
```

---

## 📚 Documentation

- [Usage Guide](usage.md) - Complete usage documentation
- [Features](features.md) - Detailed feature documentation
- [Pipeline Generator](generator.md) - Generate GitHub Actions workflows
- [EC2 Deployment](ec2-github-actions-guide.md) - Deploy to EC2 with GitHub Actions
- [SSH Setup](ssh-key-setup.md) - SSH key configuration

---

## 🎯 Use Cases

### Automated Deployments

```bash
vm_tool deploy-docker --profile production --health-port 8000
```

### CI/CD Integration

```bash
vm_tool generate-pipeline  # Creates GitHub Actions workflow
```

### Disaster Recovery

```bash
vm_tool backup create --host IP --paths /app
vm_tool rollback --host IP
```

---

## 🏗️ Architecture

**vm_tool = User-Friendly CLI + Production-Grade Ansible**

- Simple commands for users
- Ansible power under the hood
- Production-ready reliability
- Scalable architecture

---

## 📊 Status

- **Features**: 9/50 implemented (18%)
- **Tests**: 56/56 passing ✅
- **Production Ready**: Yes ✅

---

## 🔗 Links

- [GitHub Repository](https://github.com/thesunnysinha/vm_tool)
- [PyPI Package](https://pypi.org/project/vm-tool/)
- [Issue Tracker](https://github.com/thesunnysinha/vm_tool/issues)
