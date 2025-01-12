# VM Setup Tool

### A Comprehensive Tool for Setting Up Virtual Machines Using Ansible

## Overview

The VM Setup Tool is designed to simplify the process of setting up virtual machines (VMs) using Ansible. This tool is particularly useful for automating the deployment and configuration of VMs, ensuring consistency and efficiency across your infrastructure.

## Pre-requisites

Currently, the tool supports projects that use Docker Compose. Ensure you have a `docker-compose.yml` file at the root level of your project.

## Installation

To install the VM Setup Tool, you can use pip, the Python package installer. Run the following command in your terminal:

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

### When you run the setup, the VM Setup Tool will perform the following actions:

- Clone the specified GitHub repository to your local machine.
- Install Docker on the target machine if it is not already installed.
- Install Docker Compose to manage multi-container Docker applications.
- Create, enable, and start a Docker service on the machine.
- Ensure that the Docker container remains up and running, providing a stable environment for your applications.

By automating these steps, the VM Setup Tool helps you save time and reduce the potential for errors, allowing you to focus on developing and deploying your applications. 