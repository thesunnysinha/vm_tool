# Architecture

## Overview

vm_tool is a CLI-driven deployment automation platform. Users issue commands via the CLI, which are routed through handler modules into the core orchestration layer, then out to infrastructure via Ansible and SSH.

```mermaid
graph TB
    User["User / CI Pipeline"] --> CLI["vm_tool CLI (cli.py)"]
    CLI --> Handlers["handlers/\ndeploy · setup · ops · config · tools"]

    Handlers --> Core["core/\nrunner · ansible · state · history"]
    Core --> Deploy["deploy/\nhealth · drift · backup · strategies"]
    Core --> Infra["infra/\ncloud · kubernetes · ssh"]

    subgraph Supporting
        Security["security/\ncompliance · secrets · rbac · policy · recovery"]
        Observability["observability/\nmetrics · alerting · audit · reporting"]
        Tools["tools/\ngenerator · release · completion · validation"]
        Integrations["integrations/\nnotifications · webhooks · plugins · benchmarking"]
    end

    Core --> Security
    Core --> Observability
    Handlers --> Tools
    Handlers --> Integrations

    Infra --> SSH["SSH"]
    SSH --> VM1["Target VM 1"]
    SSH --> VM2["Target VM 2"]
    SSH --> K8s["K8s Cluster"]

    VM1 --> Docker1["Docker Compose"]
    VM2 --> Docker2["Docker Compose"]
    K8s --> Kubectl["kubectl / Helm"]

    style CLI fill:#4051b5,color:#fff
    style Handlers fill:#4051b5,color:#fff
    style Core fill:#4051b5,color:#fff
```

## Subpackage Layers

| Layer | Subpackage | Responsibility |
|-------|-----------|----------------|
| Entry | `cli.py`, `console.py` | Typer CLI definition, Rich console |
| Routing | `handlers/` | Thin command handlers; translate CLI args to core calls |
| Orchestration | `core/` | `SetupRunner`, Ansible wrapper, state tracking, history |
| Deployment | `deploy/` | Health checks, drift detection, backup/restore, deployment strategies |
| Infrastructure | `infra/` | Cloud VM lifecycle (AWS/GCP/Azure), Kubernetes/Helm, SSH |
| Security | `security/` | Compliance scanning, secrets sync, RBAC, policy, recovery |
| Observability | `observability/` | Metrics, alerting, audit logs, reporting |
| Tooling | `tools/` | Pipeline generation, release prep, shell completion, validation |
| Integrations | `integrations/` | Notifications, webhooks, plugin system, benchmarking |
| Configuration | `config/` | Profile and settings management |

## Core Flow

### Docker Deployment

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as vm_tool CLI
    participant H as handlers/deploy.py
    participant S as core/state.py
    participant A as core/ansible.py
    participant VM as Target VM

    U->>CLI: deploy-docker --profile prod
    CLI->>H: dispatch
    H->>S: Check if deployment needed (hash compare)
    alt No changes
        S-->>H: Up-to-date
        H-->>U: "No changes detected"
    else Changes detected
        S-->>H: Needs update
        H->>A: Run push_code.yml playbook
        A->>VM: SSH + copy files
        A->>VM: docker compose up -d
        VM-->>A: Success
        A-->>H: Playbook complete
        H->>VM: Health checks (port/HTTP via deploy/health.py)
        VM-->>H: Healthy
        H->>S: Record deployment
        H-->>U: "Deployment successful"
    end
```

### Kubernetes Deployment

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as vm_tool CLI
    participant H as handlers/deploy.py
    participant S as core/state.py
    participant K as infra/kubernetes.py
    participant Host as Target Host

    U->>CLI: deploy-k8s --method manifest --manifest app.yml
    CLI->>H: dispatch
    H->>S: Check if manifest changed (hash compare)
    alt No changes
        S-->>H: Up-to-date
        H-->>U: "No changes detected"
    else Changes detected
        S-->>H: Needs update
        H->>K: deploy_manifest / deploy_helm_chart
        K->>Host: SSH + apply manifest / helm upgrade
        Host-->>K: Rollout complete
        K-->>H: Done
        H->>S: Record deployment
        H-->>U: "Deployment successful"
    end
```

## Key Design Decisions

**Handler-based routing** — `handlers/` modules sit between the CLI and the core, keeping command dispatch thin and testable. Each handler file corresponds to a command group (`deploy`, `setup`, `ops`, `config`, `tools`).

**Ansible as execution engine** — Instead of implementing SSH command execution directly, vm_tool delegates to Ansible playbooks. This provides idempotency, error handling, and multi-host support out of the box.

**Hash-based idempotency** — Deployment state is tracked via SHA-256 hashes of compose files or K8s manifests. This allows vm_tool to skip unnecessary redeployments automatically.

**Profile system** — Deployment configurations are saved as profiles, enabling one-command deployments (`--profile prod`) and reducing the risk of misconfiguration.

**Abstract strategy pattern** — Deployment strategies (`blue_green`, `canary`, `ab_testing`) implement `_deploy_to_host` but declare `_switch_traffic` as abstract. Users subclass to wire in their own traffic-shifting logic.

**Plugin-friendly architecture** — Alert channels, deployment strategies, and cloud providers all follow an abstract base class pattern, allowing extension without modifying core code.
