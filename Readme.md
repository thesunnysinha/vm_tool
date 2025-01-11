
# VM Setup Tool

### This is a tool to set up VMs using Ansible.

## Installation

To install the VM Setup Tool, use pip:

```bash
pip install vm-tool
```

## Example Usage

```python
from vm_tool import SetupRunner

runner = SetupRunner(
    github_username='your_github_username', # e.g. username
    github_token='your_github_token', # e.g. token
    github_project_url='your_github_project_url' # e.g. https://github.com/username/repo
)

runner.run_setup()
```

## What This Will Do

- Clone the specified GitHub repository.
- Install Docker on the target machine.
- Install Docker Compose.
- Create, enable, and start a Docker service on the machine.
- Ensure that the Docker container remains up and running.
