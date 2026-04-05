# Architecture

## Overview

vm_tool is a CLI-driven deployment automation platform. Users issue commands, which are translated into Ansible playbooks executed against remote hosts via SSH.

```mermaid
graph TB
    User["User / CI Pipeline"] --> CLI["vm_tool CLI"]
    CLI --> Config["Config & Profiles"]
    CLI --> Runner["SetupRunner"]
    CLI --> Generator["Pipeline Generator"]

    Runner --> State["State Tracker"]
    Runner --> Ansible["Ansible Runner"]
    Runner --> Health["Health Checks"]

    Ansible --> SSH["SSH / Paramiko"]
    SSH --> VM1["Target VM 1"]
    SSH --> VM2["Target VM 2"]
    SSH --> K8s["K8s Cluster"]

    VM1 --> Docker1["Docker Compose"]
    VM2 --> Docker2["Docker Compose"]
    K8s --> Kubectl["kubectl / Helm"]

    State --> History["Deployment History"]
    State --> Drift["Drift Detection"]

    style CLI fill:#4051b5,color:#fff
    style Runner fill:#4051b5,color:#fff
    style Ansible fill:#e8710a,color:#fff
```

## Core Flow

### Docker Deployment

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as vm_tool CLI
    participant S as State Tracker
    participant A as Ansible
    participant VM as Target VM

    U->>CLI: deploy-docker --profile prod
    CLI->>S: Check if deployment needed (hash compare)
    alt No changes
        S-->>CLI: Up-to-date
        CLI-->>U: "No changes detected"
    else Changes detected
        S-->>CLI: Needs update
        CLI->>A: Run push_code.yml playbook
        A->>VM: SSH + copy files
        A->>VM: docker compose up -d
        VM-->>A: Success
        A-->>CLI: Playbook complete
        CLI->>VM: Health checks (port/HTTP)
        VM-->>CLI: Healthy
        CLI->>S: Record deployment
        CLI-->>U: "Deployment successful"
    end
```

### Kubernetes Deployment

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as vm_tool CLI
    participant S as State Tracker
    participant A as Ansible
    participant Host as Target Host

    U->>CLI: deploy-k8s --method manifest --manifest app.yml
    CLI->>S: Check if manifest changed (hash compare)
    alt No changes
        S-->>CLI: Up-to-date
        CLI-->>U: "No changes detected"
    else Changes detected
        S-->>CLI: Needs update
        CLI->>A: Run k8s_deploy.yml playbook
        A->>Host: SSH + copy manifest
        A->>Host: kubectl apply -f manifest
        A->>Host: kubectl rollout status
        Host-->>A: Rollout complete
        A-->>CLI: Playbook complete
        CLI->>S: Record deployment
        CLI-->>U: "Deployment successful"
    end
```

## Module Map

```mermaid
graph LR
    subgraph Core
        cli[cli.py]
        runner[runner.py]
        config[config.py]
        state[state.py]
        history[history.py]
    end

    subgraph Deployment
        generator[generator.py]
        release[release.py]
        validation[validation.py]
    end

    subgraph Operations
        health[health.py]
        drift[drift.py]
        backup[backup.py]
        recovery[recovery.py]
    end

    subgraph Security
        secrets[secrets.py]
        rbac[rbac.py]
        policy[policy.py]
        audit[audit.py]
    end

    subgraph Notifications
        alerting[alerting.py]
        webhooks[webhooks.py]
        notifications[notifications.py]
    end

    cli --> runner
    cli --> config
    cli --> generator
    runner --> state
    runner --> history
    runner --> health
```

## Key Design Decisions

**Ansible as execution engine** — Instead of implementing SSH command execution directly, vm_tool delegates to Ansible playbooks. This provides idempotency, error handling, and multi-host support out of the box.

**Hash-based idempotency** — Deployment state is tracked via SHA-256 hashes of compose files or K8s manifests. This allows vm_tool to skip unnecessary redeployments automatically.

**Profile system** — Deployment configurations are saved as profiles, enabling one-command deployments (`--profile prod`) and reducing the risk of misconfiguration.

**Plugin-friendly architecture** — Alert channels, deployment strategies, and cloud providers all follow an abstract base class pattern, allowing extension without modifying core code.
