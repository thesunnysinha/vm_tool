# CLI Reference

Complete reference for all vm_tool commands.

## Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version |
| `--verbose`, `-v` | Enable verbose output |
| `--debug`, `-d` | Enable debug logging |

---

## `vm_tool config`

Manage configuration and deployment profiles.

### `config set <key> <value>`

Set a configuration value.

```bash
vm_tool config set default-host 192.168.1.100
```

### `config get <key>`

Get a configuration value.

```bash
vm_tool config get default-host
```

### `config unset <key>`

Remove a configuration value.

### `config list`

List all configuration values.

### `config create-profile <name>`

Create a deployment profile.

| Option | Description | Default |
|--------|-------------|---------|
| `--environment` | `development`, `staging`, or `production` | `development` |
| `--host` | Target host | — |
| `--user` | SSH user | — |
| `--compose-file` | Docker Compose file | — |

```bash
vm_tool config create-profile prod \
  --environment production \
  --host 10.0.2.10 \
  --user ubuntu \
  --compose-file docker-compose.prod.yml
```

### `config list-profiles`

List all saved profiles.

### `config delete-profile <name>`

Delete a profile.

---

## `vm_tool deploy-docker`

Deploy a Docker Compose application to a remote host.

| Option | Description | Default |
|--------|-------------|---------|
| `--profile` | Use a saved profile | — |
| `--host` | Target host IP/domain | — |
| `--user` | SSH username | — |
| `--compose-file` | Docker Compose file | `docker-compose.yml` |
| `--inventory` | Ansible inventory file | `inventory.yml` |
| `--env-file` | Environment file | — |
| `--deploy-command` | Custom deploy command | — |
| `--project-dir` | Target directory on server | `~/app` |
| `--repo-name` | Repository name (sets project-dir to `~/apps/<name>`) | — |
| `--health-port` | Port to check after deploy | — |
| `--health-url` | HTTP URL to check after deploy | — |
| `--health-check` | Custom health check command | — |
| `--health-timeout` | Health check timeout (seconds) | `300` |
| `--dry-run` | Preview without deploying | — |
| `--force` | Force redeployment | — |
| `--webhook-url` | Webhook for notifications | — |
| `--notify-email` | Email for notifications (repeatable) | — |

```bash
vm_tool deploy-docker --profile production --health-port 8000
```

---

## `vm_tool deploy-k8s`

Deploy to a Kubernetes cluster using kubectl or Helm.

| Option | Description | Default |
|--------|-------------|---------|
| `--method` | `manifest` or `helm` | `manifest` |
| `--namespace` | Kubernetes namespace | `default` |
| `--manifest` | Path to K8s manifest file | — |
| `--helm-chart` | Helm chart name/path | — |
| `--helm-release` | Helm release name | — |
| `--helm-values` | Helm values file | — |
| `--kubeconfig` | Path to kubeconfig | — |
| `--host` | Target host | — |
| `--user` | SSH user | — |
| `--inventory` | Ansible inventory file | `inventory.yml` |
| `--timeout` | Rollout timeout (seconds) | `300` |
| `--dry-run` | Preview without applying | — |
| `--force` | Force redeployment | — |

```bash
vm_tool deploy-k8s --method manifest --manifest k8s/app.yml --namespace prod
```

---

## `vm_tool history`

Show deployment history.

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Filter by host | — |
| `--limit` | Number of entries | `10` |

---

## `vm_tool rollback`

Rollback to a previous deployment.

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Target host (required) | — |
| `--to` | Specific deployment ID | previous |
| `--inventory` | Inventory file | `inventory.yml` |

---

## `vm_tool drift-check`

Check for configuration drift on a server.

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Target host (required) | — |
| `--user` | SSH user | `ubuntu` |

---

## `vm_tool backup`

### `backup create`

| Option | Description |
|--------|-------------|
| `--host` | Target host (required) |
| `--user` | SSH user |
| `--paths` | Paths to backup (required, space-separated) |

### `backup list`

| Option | Description |
|--------|-------------|
| `--host` | Filter by host |

### `backup restore`

| Option | Description |
|--------|-------------|
| `--id` | Backup ID (required) |
| `--host` | Target host (required) |
| `--user` | SSH user |

---

## `vm_tool generate-pipeline`

Interactively generate a CI/CD pipeline configuration.

| Option | Description | Default |
|--------|-------------|---------|
| `--platform` | CI/CD platform | `github` |

Prompts for: branch, Python version, linting, tests, monitoring, deployment type, compose file.

---

## `vm_tool prepare-release`

Merge and prepare Docker Compose files for release.

| Option | Description |
|--------|-------------|
| `--base-file` | Base docker-compose file (required) |
| `--prod-file` | Production overlay file (required) |
| `--output` | Output file path (required) |
| `--strip-volumes` | Services to strip volumes from (comma-separated) |
| `--fix-paths` | Fix CI absolute paths to relative |

---

## `vm_tool secrets sync`

Sync local `.env` file to GitHub Secrets.

| Option | Description | Default |
|--------|-------------|---------|
| `--env-file` | Path to `.env` file | `.env` |
| `--repo` | Target GitHub repository | — |

---

## `vm_tool hydrate-env`

Reconstruct `.env` files from secrets during CI/CD.

| Option | Description | Default |
|--------|-------------|---------|
| `--compose-file` | Docker Compose file | `docker-compose.yml` |
| `--secrets` | JSON string of secrets (required) | — |
| `--project-root` | Project root directory | `.` |

---

## `vm_tool setup`

Full VM setup with Docker and code deployment.

| Option | Description |
|--------|-------------|
| `--github-project-url` | GitHub repo URL (required) |
| `--github-username` | GitHub username |
| `--github-token` | GitHub token |
| `--github-branch` | Branch | `main` |
| `--docker-compose-file-path` | Compose file | `docker-compose.yml` |
| `--dockerhub-username` | DockerHub username |
| `--dockerhub-password` | DockerHub password |

---

## `vm_tool setup-cloud`

Setup cloud VMs from SSH configs JSON file.

| Option | Description |
|--------|-------------|
| `--ssh-configs` | Path to SSH configs JSON (required) |
| `--github-project-url` | GitHub repo URL (required) |

---

## `vm_tool setup-k8s`

Install K3s Kubernetes cluster.

| Option | Description | Default |
|--------|-------------|---------|
| `--inventory` | Inventory file | `inventory.yml` |

---

## `vm_tool setup-monitoring`

Install Prometheus and Grafana.

| Option | Description | Default |
|--------|-------------|---------|
| `--inventory` | Inventory file | `inventory.yml` |

---

## `vm_tool completion <shell>`

Generate shell completion scripts.

| Argument | Description |
|----------|-------------|
| `shell` | `bash`, `zsh`, or `fish` |
| `--install` | Install the completion script |

---

## `vm_tool doctor`

Check that all required prerequisites are installed and accessible.

Verifies: Ansible, Docker, kubectl, Helm, SSH, and required Python packages.

```bash
vm_tool doctor
```

Output is rendered as a Rich table showing the status of each prerequisite. Run this before your first deployment to catch missing dependencies early.

---

## `vm_tool status`

Show the current deployment state for all known hosts.

```bash
vm_tool status
```

Displays a Rich table with each tracked host, its last deployment timestamp, deployed hash, and health status.
