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

Install only what you need:

=== "AWS"

    ```bash
    pip install vm-tool[aws]
    ```

    Adds `boto3` for AWS VM lifecycle management.

=== "GCP"

    ```bash
    pip install vm-tool[gcp]
    ```

    Adds `google-cloud-compute` for GCP VM lifecycle management.

=== "Azure"

    ```bash
    pip install vm-tool[azure]
    ```

    Adds `azure-mgmt-compute` for Azure VM lifecycle management.

=== "SSH (Fabric)"

    ```bash
    pip install vm-tool[ssh]
    ```

    Adds `fabric` for advanced SSH operations.

=== "All Extras"

    ```bash
    pip install vm-tool[all]
    ```

    Installs all optional dependencies.

## Verify Installation

```bash
vm_tool --version
vm_tool doctor
```

`vm_tool doctor` checks that all runtime prerequisites (Ansible, Docker, kubectl, Helm, SSH, Python packages) are available on your system.

## Development Installation

```bash
git clone https://github.com/thesunnysinha/vm_tool.git
cd vm_tool
pip install -e ".[dev]"
```

For development workflows, use `run.py` instead of `make`:

```bash
python run.py test   # run the test suite
python run.py push   # commit and push to GitHub
```

`run.py` is cross-platform and replaces the old `Makefile` and `codePushToGithub.py`.
