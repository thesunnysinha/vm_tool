# 🚀 VM Setup Tool

[![PyPI version](https://img.shields.io/pypi/v/vm-tool.svg)](https://pypi.org/project/vm-tool/) [![Python versions](https://img.shields.io/pypi/pyversions/vm-tool.svg)](https://pypi.org/project/vm-tool/)

[**PyPI**](https://pypi.org/project/vm-tool/) • [**GitHub**](https://github.com/thesunnysinha/vm_tool) • [**Contributing**](CONTRIBUTING) • [**License**](LICENSE)

A modern, user-friendly solution for automating and managing virtual machine (VM) setup and configuration using Ansible.

---

## ✨ Features
- Automated VM setup with Docker & Docker Compose
- Cloud VM provisioning via SSH
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

### Automated Local VM Setup
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

### Cloud VM Setup (via SSH)
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

### SSH Key Management
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
See the [PyPI page](https://pypi.org/project/vm-tool/) for more details, or visit the [GitHub repository](https://github.com/thesunnysinha/vm_tool) for full documentation, issues, and contributions.

---

Empower your infrastructure automation with **VM Setup Tool** – fast, reliable, and developer-friendly!