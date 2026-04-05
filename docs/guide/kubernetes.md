# Kubernetes Deployment

vm_tool supports deploying to Kubernetes clusters using either raw manifests (`kubectl apply`) or Helm charts.

## Prerequisites

- `kubectl` installed and configured on the target host
- `helm` installed on the target host (for Helm deployments)
- A valid kubeconfig with cluster access

---

## Manifest Deployment

Deploy Kubernetes manifests directly:

```bash
vm_tool deploy-k8s \
  --method manifest \
  --manifest k8s/deployment.yml \
  --namespace my-app \
  --host 10.0.0.1 \
  --user ubuntu
```

### Dry-Run

Preview what would be applied (server-side dry-run):

```bash
vm_tool deploy-k8s \
  --method manifest \
  --manifest k8s/deployment.yml \
  --namespace my-app \
  --dry-run
```

---

## Helm Deployment

Deploy using Helm charts:

```bash
vm_tool deploy-k8s \
  --method helm \
  --helm-chart bitnami/nginx \
  --helm-release my-nginx \
  --helm-values values.prod.yml \
  --namespace production \
  --host 10.0.0.1 \
  --user ubuntu
```

### Helm Dry-Run

```bash
vm_tool deploy-k8s \
  --method helm \
  --helm-chart ./charts/my-app \
  --helm-release my-app \
  --helm-values values.yml \
  --dry-run
```

---

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--method` | `manifest` or `helm` | `manifest` |
| `--namespace` | Kubernetes namespace | `default` |
| `--manifest` | Path to manifest file/dir | — |
| `--helm-chart` | Helm chart name or path | — |
| `--helm-release` | Helm release name | — |
| `--helm-values` | Path to values file | — |
| `--kubeconfig` | Path to kubeconfig | `~/.kube/config` |
| `--host` | Target host (where kubectl runs) | — |
| `--user` | SSH user | — |
| `--timeout` | Rollout timeout (seconds) | `300` |
| `--dry-run` | Preview without applying | `false` |
| `--force` | Force redeployment | `false` |

---

## Idempotency

Like Docker deployments, K8s deployments track state by hashing the manifest or values file. If nothing has changed, the deployment is skipped:

```
$ vm_tool deploy-k8s --method manifest --manifest k8s/app.yml --host 10.0.0.1
No changes detected for default. Use --force to redeploy.
```

Use `--force` to redeploy regardless.

---

## K3s Setup

To install a K3s cluster on a fresh VM:

```bash
vm_tool setup-k8s --inventory inventory.yml
```

This installs K3s and fetches the kubeconfig to your local machine.
