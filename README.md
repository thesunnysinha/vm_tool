# 🚀 VM Setup Tool

[![PyPI version](https://img.shields.io/pypi/v/vm-tool.svg)](https://pypi.org/project/vm-tool/) [![Python versions](https://img.shields.io/pypi/pyversions/vm-tool.svg)](https://pypi.org/project/vm-tool/)

[**Documentation**](https://vm-tool.sunnysinha.online/) • [**PyPI**](https://pypi.org/project/vm-tool/) • [**GitHub**](https://github.com/thesunnysinha/vm_tool) • [**Contributing**](CONTRIBUTING) • [**License**](LICENSE)

A modern, user-friendly solution for automating and managing virtual machine (VM) setup and configuration using Ansible.

---

## ✨ Features

- Automated VM setup with Docker & Docker Compose
- Cloud VM provisioning via SSH (AWS, GCP, Azure)
- **Kubernetes Ready**: One-click K3s cluster setup + manifest/Helm deployments
- **CI/CD Pipelines**: Deploy to Kubernetes from GitHub Actions with zero kubectl boilerplate
- **Observability**: Instant Prometheus & Grafana deployment
- SSH key management and configuration
- Simple Python API for integration
- One-command version check: `vm_tool --version`

---

## ⚡️ Installation

Install the latest version from PyPI:

```bash
pip install vm-tool
```

---

## 🛠️ Usage Examples

### 🚀 Universal Deployment (CLI)

#### 1. Generate CI/CD Pipeline

Bootstrap your project with a complete GitHub Actions workflow:

```bash
vm_tool generate-pipeline
```

#### 2. Setup Kubernetes (K3s)

Deploy a lightweight Kubernetes cluster to your servers:

```bash
vm_tool setup-k8s --inventory inventory.yml
```

#### 3. Deploy to Kubernetes

Deploy manifests or Helm charts to an existing Kubernetes cluster:

```bash
# Manifest-based deployment
vm_tool deploy-k8s \
  --method manifest \
  --manifest ./k8s/ \
  --namespace myapp \
  --kubeconfig ~/.kube/config

# Helm-based deployment
vm_tool deploy-k8s \
  --method helm \
  --helm-chart ./charts/myapp \
  --helm-release myapp \
  --namespace myapp \
  --kubeconfig ~/.kube/config
```

#### 4. Deploy to Kubernetes from CI/CD (no SSH needed)

Pass a base64-encoded kubeconfig, inject images, and sync secrets — all from GitHub Actions:

```bash
vm_tool deploy-k8s \
  --method manifest \
  --manifest k8s/ \
  --namespace myapp \
  --kubeconfig-b64 "$KUBECONFIG_B64" \
  --image "IMAGE_REGISTRY/myapp:IMAGE_TAG=${IMAGE_REF}" \
  --k8s-secret "app-secret=${APP_ENV}" \
  --k8s-secret "db-secret=${DB_ENV}" \
  --registry-secret "ghcr-secret=ghcr.io:${GH_ACTOR}:${GH_TOKEN}" \
  --timeout 300
```

**CI flags:**

| Flag | Description |
|------|-------------|
| `--kubeconfig-b64` | Base64-encoded kubeconfig (decoded to `~/.kube/config` automatically) |
| `--image KEY=VALUE` | Substitute image refs in manifests. Key format: `PLACEHOLDER_VAR=actual_image:tag` |
| `--k8s-secret NAME=ENVFILE` | Create/update a generic Kubernetes secret from an env-file string |
| `--registry-secret NAME=SERVER:USER:PASS` | Create/update a docker-registry pull secret |
| `--dry-run` | Validate manifests against the cluster without applying |
| `--force` | Skip hash-based change detection and always deploy |

#### 5. Setup Observability

Deploy Prometheus and Grafana for instant monitoring:

```bash
vm_tool setup-monitoring --inventory inventory.yml
```

---

### 📦 GitHub Actions Example

Full pipeline: build image → push to GHCR → deploy to Kubernetes:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}
      image:     ${{ steps.image.outputs.full }}
    steps:
      - uses: actions/checkout@v4
      # ... docker build-push steps ...

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install kubectl
        uses: azure/setup-kubectl@v4

      - name: Install vm_tool
        run: pip install vm-tool

      - name: Deploy with vm_tool
        env:
          IMAGE_REF: ${{ needs.build.outputs.image }}:${{ needs.build.outputs.image_tag }}
          KUBECONFIG_B64: ${{ secrets.KUBECONFIG_B64 }}
          APP_ENV: ${{ secrets.APP_ENV }}
          DB_ENV: ${{ secrets.DB_ENV }}
          GH_ACTOR: ${{ github.actor }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          vm_tool deploy-k8s \
            --method manifest \
            --manifest k8s/ \
            --namespace myapp \
            --kubeconfig-b64 "$KUBECONFIG_B64" \
            --image "IMAGE_REGISTRY/myapp:IMAGE_TAG=${IMAGE_REF}" \
            --k8s-secret "app-secret=${APP_ENV}" \
            --k8s-secret "db-secret=${DB_ENV}" \
            --registry-secret "ghcr-secret=ghcr.io:${GH_ACTOR}:${GH_TOKEN}" \
            --timeout 300 \
            --force
```

> **Secret setup**: Store your cluster's kubeconfig as a base64 secret:
> ```bash
> gh secret set KUBECONFIG_B64 --body "$(base64 -i ~/.kube/config)"
> ```

---

### 🐍 Python API Usage

#### Automated Local VM Setup

```python
from vm_tool.runner import SetupRunner, SetupRunnerConfig

config = SetupRunnerConfig(
    github_username='your_github_username',
    github_token='your_github_token',
    github_project_url='your_github_project_url',
    github_branch='your_branch_name',
    docker_compose_file_path='path_to_your_docker_compose_file',
    dockerhub_username='your_dockerhub_username',
    dockerhub_password='your_dockerhub_password'
)

runner = SetupRunner(config)
runner.run_setup()
```

#### Cloud VM Setup (via SSH)

```python
from vm_tool.runner import SetupRunner, SetupRunnerConfig, SSHConfig

config = SetupRunnerConfig(
    github_username='your_github_username',
    github_token='your_github_token',
    github_project_url='your_github_project_url',
    github_branch='your_branch_name',
    docker_compose_file_path='path_to_your_docker_compose_file',
    dockerhub_username='your_dockerhub_username',
    dockerhub_password='your_dockerhub_password'
)

runner = SetupRunner(config)

ssh_configs = [
    SSHConfig(
        ssh_username='your_ssh_username',
        ssh_password='your_ssh_password',
        ssh_hostname='your_ssh_hostname',
        ssh_identity_file='/path/to/your/ssh_key'  # Optional
    )
]

runner.run_cloud_setup(ssh_configs)
```

#### Kubernetes Deployment via Python API

```python
from vm_tool.runner import SetupRunner, SetupRunnerConfig

config = SetupRunnerConfig(...)
runner = SetupRunner(config)

runner.run_k8s_deploy(
    method="manifest",
    manifest="k8s/",
    namespace="myapp",
    kubeconfig_b64="<base64-encoded-kubeconfig>",
    images={"IMAGE_REGISTRY/myapp:IMAGE_TAG": "ghcr.io/org/myapp:sha-abc123"},
    k8s_secrets={"app-secret": "KEY=val\nOTHER=val2"},
    registry_secrets={"ghcr-secret": ("ghcr.io", "user", "token")},
    timeout=300,
    force=True,
)
```

#### SSH Key Management

```python
from vm_tool.ssh import SSHSetup

ssh_setup = SSHSetup(
    hostname='your_vm_hostname',
    username='your_vm_username',
    password='your_vm_password',
    email='your_email_for_ssh_key'
)

ssh_setup.setup()
```

---

## 🖥️ Command Line Version Check

Check your installed version at any time:

```bash
vm_tool --version
```

---

## ⚙️ Configuration Options

- `github_username`: GitHub username (for private repos)
- `github_token`: GitHub token (for private repos)
- `github_project_url`: GitHub repository URL
- `github_branch`: Branch to use (default: main)
- `docker_compose_file_path`: Path to Docker Compose file (default: docker-compose.yml)
- `dockerhub_username`: Docker Hub username (if login needed)
- `dockerhub_password`: Docker Hub password (if login needed)

---

## 📚 Learn More

See the [Official Documentation](https://vm-tool.sunnysinha.online/) for complete guides. Visit the [PyPI page](https://pypi.org/project/vm-tool/) for details, or the [GitHub repository](https://github.com/thesunnysinha/vm_tool) for code and issues.

---

## 🗺️ Roadmap

- **Terraform integration** — `vm_tool provision` command wrapping `terraform apply` with variable passthrough
- **Per-host password support** — when multiple SSH configs have different passwords, support a per-host vault lookup instead of last-wins env var
- **Traffic splitting** — built-in nginx/AWS ALB/HAProxy helpers for blue-green and canary `_switch_traffic` override

---

Empower your infrastructure automation with **VM Setup Tool** – fast, reliable, and developer-friendly!
