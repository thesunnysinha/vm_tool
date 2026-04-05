# Installation

## Requirements

- Python 3.9+
- SSH access to target hosts
- Docker & Docker Compose on target hosts (for Docker deployments)
- kubectl/Helm on target hosts (for Kubernetes deployments)

## Install from PyPI

```bash
pip install vm-tool
```

## Optional Extras

Install cloud provider support as needed:

=== "AWS"

    ```bash
    pip install vm-tool[aws]
    ```

=== "GCP"

    ```bash
    pip install vm-tool[gcp]
    ```

=== "Azure"

    ```bash
    pip install vm-tool[azure]
    ```

=== "All Extras"

    ```bash
    pip install vm-tool[all]
    ```

## Verify Installation

```bash
vm_tool --version
```

## Development Installation

```bash
git clone https://github.com/thesunnysinha/vm_tool.git
cd vm_tool
pip install -e ".[dev]"
```
