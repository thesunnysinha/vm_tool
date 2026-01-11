# VM Tool - Deployment Approaches

## Two Deployment Methods

vm_tool supports two deployment approaches:

### 1. Simple Deployment (`deploy-docker`)

**Use when**: VM is already set up with Docker

```bash
vm_tool deploy-docker --host IP --user USER
```

**Features**:

- Deploys docker-compose application
- Health checks
- Rollback support
- Idempotent

**GitHub Actions**:

```yaml
- name: Deploy
  run: vm_tool deploy-docker --host ${{ secrets.EC2_HOST }}
```

---

### 2. Full Setup (`run_cloud_setup`)

**Use when**: Fresh VM needs complete setup

```python
from vm_tool.runner import SetupRunner, SetupRunnerConfig, SSHConfig

config = SetupRunnerConfig(
    github_username=os.environ.get('GITHUB_USERNAME'),
    github_token=os.environ.get('GITHUB_TOKEN'),
    github_project_url='https://github.com/user/repo.git',
    docker_compose_file_path='docker-compose.prod.yml',
)

runner = SetupRunner(config)
ssh_configs = [SSHConfig(...)]
runner.run_cloud_setup(ssh_configs)
```

**Features**:

- Installs Docker
- Clones GitHub repository
- Sets up docker-compose
- Configures environment

**GitHub Actions**:

```yaml
- name: Deploy
  run: python scripts/deploy_to_vm.py
```

---

## When to Use Each

| Scenario           | Method            | Why                        |
| ------------------ | ----------------- | -------------------------- |
| Fresh EC2 instance | Full Setup        | Needs Docker installation  |
| Existing server    | Simple Deployment | Docker already installed   |
| First deployment   | Full Setup        | Complete environment setup |
| Updates/redeploys  | Simple Deployment | Faster, idempotent         |
| Multiple VMs       | Full Setup        | Provision all at once      |
| Single VM          | Either            | Both work                  |

---

## Migration Path

**Start**: Full Setup (first time)

```python
runner.run_cloud_setup(ssh_configs)  # Installs everything
```

**Later**: Simple Deployment (updates)

```bash
vm_tool deploy-docker --profile prod  # Just deploy changes
```

---

## Comparison

| Feature             | Simple Deployment      | Full Setup    |
| ------------------- | ---------------------- | ------------- |
| Docker installation | ❌ (assumes installed) | ✅            |
| GitHub clone        | ❌ (manual)            | ✅            |
| Deploy app          | ✅                     | ✅            |
| Health checks       | ✅                     | ❌            |
| Rollback            | ✅                     | ❌            |
| Idempotent          | ✅                     | ⚠️            |
| Speed               | Fast                   | Slower        |
| Use case            | Updates                | Initial setup |

---

## Recommendation

**Best Practice**:

1. Use **Full Setup** for initial VM provisioning
2. Use **Simple Deployment** for all subsequent updates

This gives you the best of both worlds!
