import os
import logging

logger = logging.getLogger(__name__)


class PipelineGenerator:
    """
    Generates CI/CD pipeline configurations.
    """

    GITHUB_TEMPLATE = """name: Project Deployment

on:
  push:
    branches: [ (( branch_name )) ]
  workflow_dispatch:  # Allow manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '(( python_version ))'

    - name: Install vm_tool
      run: pip install vm-tool

    {% if run_linting %}
    - name: Run Linting
      run: |
        pip install flake8
        flake8 .
    {% endif %}

    {% if run_tests %}
    - name: Run Tests
      run: |
        pip install pytest
        pytest
    {% endif %}

    - name: Check for Secrets
      run: |
        if [ -z "${{ secrets.SSH_PRIVATE_KEY }}" ]; then
          echo "Error: SSH_PRIVATE_KEY secret is not set."
          exit 1
        fi
        if [ -z "${{ secrets.VM_HOST }}" ]; then
          echo "Error: VM_HOST secret is not set."
          exit 1
        fi
        if [ -z "${{ secrets.SSH_USER }}" ]; then
          echo "Error: SSH_USER secret is not set."
          exit 1
        fi

    - name: Setup SSH Key
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts

    {% if deployment_type == 'kubernetes' %}
    - name: Setup Kubernetes (K3s)
      run: |
        echo "Setting up K3s..."
        # vm_tool setup-k8s --inventory inventory.yml
    {% endif %}

    {% if deployment_type == 'docker' %}
    - name: Deploy with Docker Compose
      run: |
        echo "Deploying with Docker Compose..."
        vm_tool deploy-docker --compose-file (( docker_compose_file )) --host ${{ secrets.VM_HOST }} --user ${{ secrets.SSH_USER }}
    {% endif %}

    {% if setup_monitoring %}
    - name: Setup Observability (Prometheus/Grafana)
      if: success()
      run: |
        echo "Setting up Monitoring..."
        # vm_tool setup-monitoring --inventory inventory.yml
    {% endif %}
"""

    def generate(self, platform: str = "github", context: dict = None):
        """Generate pipeline configuration."""
        if platform != "github":
            raise NotImplementedError(f"Platform {platform} not supported yet.")

        if context is None:
            context = {
                "branch_name": "main",
                "python_version": "3.12",
                "run_linting": False,
                "run_tests": False,
                "setup_monitoring": False,
                "deployment_type": "docker",
                "docker_compose_file": "docker-compose.yml",
            }

        from jinja2 import Environment, BaseLoader

        env = Environment(
            loader=BaseLoader(),
            variable_start_string="((",
            variable_end_string="))",
            autoescape=True,
        )
        template = env.from_string(self.GITHUB_TEMPLATE)
        rendered_content = template.render(**context)

        workflow_dir = ".github/workflows"
        os.makedirs(workflow_dir, exist_ok=True)

        file_path = os.path.join(workflow_dir, "deploy.yml")
        with open(file_path, "w") as f:
            f.write(rendered_content)

        logger.info(f"Generated GitHub Actions workflow at {file_path}")
