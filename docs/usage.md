# Usage Guide

VM Tool provides a powerful CLI to manage your infrastructure lifecycle.

## 🚀 Quick Start

Ensure you have installed the tool:

```bash
pip install vm-tool
```

## 🏗️ Infrastructure Provisioning

Provision cloud resources using Terraform.

### Command

```bash
vm_tool provision --provider <PROVIDER> --action <ACTION> [--vars KEY=VALUE ...]
```

### Examples

**Apply AWS Configuration:**

```bash
vm_tool provision --provider aws --action apply --vars region=us-west-2 instance_type=t3.medium
```

**Destroy Infrastructure:**

```bash
vm_tool provision --provider aws --action destroy
```

## ☸️ Kubernetes Setup (K3s)

Deploy a lightweight K3s cluster.

### Command

```bash
vm_tool setup-k8s --inventory <INVENTORY_FILE>
```

### Inventory Example (`inventory.yml`)

```yaml
all:
  hosts:
    server1:
      ansible_host: 192.168.1.10
      ansible_user: ubuntu
```

## 📊 Observability Stack

Deploy Prometheus and Grafana for monitoring.

### Command

```bash
vm_tool setup-monitoring --inventory <INVENTORY_FILE>
```

## ⚡ CI/CD Pipeline Generator

Generate a GitHub Actions workflow to automate everything.

### Command

```bash
vm_tool generate-pipeline --platform github
```

The command is **interactive** by default. It will prompt you for:

- Branch to trigger the workflow.
- Python Version (default: 3.12).
- Whether to run **Linting** (flake8).
- Whether to run **Tests** (pytest).
- **Deployment Type** (Kubernetes or Docker Compose).
- Whether to include **Observability** (Monitoring) steps.

This creates a `.github/workflows/deploy.yml` file in your current directory.

## 🌐 Deploying Documentation

### Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project root.
3. Build Command: `pip install -e .[dev] && python -m mkdocs build`
4. Output Directory: `site`

### GitHub Pages

1. A workflow is included to build docs.
2. Enable GitHub Pages in Repository Settings > Pages.
3. Select `gh-pages` branch (after first run).
