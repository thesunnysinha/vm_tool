import sys
import ansible_runner
import os
import yaml
from pydantic import BaseModel, validator, model_validator, Field
from typing import List, Optional

class SetupRunnerConfig(BaseModel):
    """
    Configuration model for setting up the runner.
    
    Attributes:
        github_username (Optional[str]): GitHub username for authentication.
        github_token (Optional[str]): GitHub token for authentication.
        github_project_url (str): URL of the GitHub repository.
        github_branch (str): GitHub branch to use (default: 'main').
        docker_compose_file_path (str): Path to the Docker Compose file (default: 'docker-compose.yml').
        dockerhub_username (Optional[str]): DockerHub username (optional).
        dockerhub_password (Optional[str]): DockerHub password (required if username is provided).
    """

    github_username: Optional[str] = Field(
        default=None, description="GitHub username for authentication (optional)"
    )
    github_token: Optional[str] = Field(
        default=None, description="GitHub token for authentication (optional)"
    )
    github_project_url: str = Field(..., description="URL of the GitHub repository")
    github_branch: str = Field(default='main', description="GitHub branch to use (default: 'main')")
    docker_compose_file_path: str = Field(
        default='docker-compose.yml', description="Path to the Docker Compose file (default: 'docker-compose.yml')"
    )
    dockerhub_username: Optional[str] = Field(
        default=None, description="DockerHub username (optional)"
    )
    dockerhub_password: Optional[str] = Field(
        default=None, description="DockerHub password (required if username is provided)"
    )

    @validator('docker_compose_file_path', pre=True, always=True)
    def set_default_docker_compose_file_path(cls, v):
        """Ensures a default value for the Docker Compose file path."""
        return v or 'docker-compose.yml'

    @validator('dockerhub_password', always=True)
    def check_dockerhub_password(cls, v, values):
        """Ensures that a password is provided if a DockerHub username is set."""
        if values.get('dockerhub_username') and not v:
            raise ValueError("DockerHub password must be provided if DockerHub username is specified")
        return v

    @validator('dockerhub_username', always=True)
    def check_dockerhub_username(cls, v, values):
        """Ensures that a username is provided if a DockerHub password is set."""
        if values.get('dockerhub_password') and not v:
            raise ValueError("DockerHub username must be provided if DockerHub password is specified")
        return v

    @validator('github_token', always=True)
    def check_github_token(cls, v, values):
        """Ensures that a GitHub token is provided if a GitHub username is set."""
        if values.get('github_username') and not v:
            raise ValueError("GitHub token must be provided if GitHub username is specified")
        return v

    @validator('github_username', always=True)
    def check_github_username(cls, v, values):
        """Ensures that a GitHub username is provided if a GitHub token is set."""
        if values.get('github_token') and not v:
            raise ValueError("GitHub username must be provided if GitHub token is specified")
        return v

class SSHConfig(BaseModel):
    """
    Configuration model for SSH authentication.

    Attributes:
        ssh_username (str): SSH username.
        ssh_hostname (str): SSH host/IP.
        ssh_password (Optional[str]): SSH password (optional if identity file is provided).
        ssh_identity_file (Optional[str]): Path to SSH private key file (optional if password is provided).
    """

    ssh_username: str = Field(..., description="SSH username")
    ssh_hostname: str = Field(..., description="SSH host/IP")
    ssh_password: Optional[str] = Field(
        default=None, description="SSH password (optional if identity file is provided)"
    )
    ssh_identity_file: Optional[str] = Field(
        default=None, description="Path to SSH private key file (optional if password is provided)"
    )

    @model_validator(mode="before")
    def validate_authentication(cls, values):
        """Ensures that either an SSH password or identity file is provided for authentication."""
        password = values.get('ssh_password')
        identity_file = values.get('ssh_identity_file')
        if not password and not identity_file:
            raise ValueError("Either ssh_password or ssh_identity_file must be provided.")
        return values

class SetupRunner:
    """
    Main class to handle setup execution.

    Attributes:
        github_username (str): GitHub username.
        github_token (str): GitHub token.
        github_project_url (str): GitHub repository URL.
        github_branch (str): GitHub branch to use.
        docker_compose_file_path (str): Path to Docker Compose file.
        dockerhub_username (str): DockerHub username.
        dockerhub_password (str): DockerHub password.
    """

    def __init__(self, config: SetupRunnerConfig):
        """Initializes the setup runner with the given configuration."""
        self.github_username = config.github_username
        self.github_token = config.github_token
        self.github_project_url = config.github_project_url
        self.github_branch = config.github_branch
        self.docker_compose_file_path = config.docker_compose_file_path
        self.dockerhub_username = config.dockerhub_username
        self.dockerhub_password = config.dockerhub_password

    def _run_ansible_playbook(self, extravars, inventory_file):
        """Executes an Ansible playbook with the given variables and inventory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        venv_dir = os.path.join(sys.prefix, 'ansible_runner_data')
        os.makedirs(venv_dir, exist_ok=True)

        playbook_path = os.path.join(current_dir, 'vm_setup', 'main.yml')
        inventory_path = os.path.join(current_dir, 'vm_setup', inventory_file)

        try:
            r = ansible_runner.run(
                private_data_dir=venv_dir,
                playbook=playbook_path,
                inventory=inventory_path,
                extravars=extravars
            )

            if r.rc != 0:
                raise RuntimeError(f"Ansible playbook execution failed with return code {r.rc}: {r.stdout}")

        except Exception as e:
            raise RuntimeError(f"An error occurred while running the Ansible playbook: {str(e)}")

    def run_setup(self):
        """Runs the setup process using Ansible."""
        extravars = {
            'GITHUB_USERNAME': self.github_username,
            'GITHUB_TOKEN': self.github_token,
            'GITHUB_PROJECT_URL': self.github_project_url,
            'GITHUB_BRANCH': self.github_branch,
            'DOCKERHUB_USERNAME': self.dockerhub_username,
            'DOCKERHUB_PASSWORD': self.dockerhub_password,
            'EXECUTION_TYPE': "normal"
        }

        if self.docker_compose_file_path:
            extravars["DOCKER_COMPOSE_FILE_PATH"] = self.docker_compose_file_path

        self._run_ansible_playbook(extravars, 'inventory.yml')

    def run_cloud_setup(self, ssh_configs: List[SSHConfig]):
        """Runs the cloud setup using Ansible with dynamic inventory generation."""
        inventory_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vm_setup', 'dynamic_inventory.yml')

        inventory_content = {
            'all': {
                'hosts': {},
                'vars': {
                    'ansible_python_interpreter': '/usr/bin/python3'
                }
            }
        }

        for i, ssh_config in enumerate(ssh_configs):
            host_key = f'cloud_host_{i}'
            host_entry = {
                'ansible_host': ssh_config.ssh_hostname,
                'ansible_user': ssh_config.ssh_username,
            }
            if ssh_config.ssh_identity_file:
                host_entry['ansible_ssh_private_key_file'] = ssh_config.ssh_identity_file
            elif ssh_config.ssh_password:
                host_entry['ansible_ssh_pass'] = ssh_config.ssh_password

            inventory_content['all']['hosts'][host_key] = host_entry

        with open(inventory_file_path, 'w') as inventory_file:
            yaml.dump(inventory_content, inventory_file)

        extravars = {
            'GITHUB_USERNAME': self.github_username,
            'GITHUB_TOKEN': self.github_token,
            'GITHUB_PROJECT_URL': self.github_project_url,
            'GITHUB_BRANCH': self.github_branch,
            'DOCKERHUB_USERNAME': self.dockerhub_username,
            'DOCKERHUB_PASSWORD': self.dockerhub_password,
            'EXECUTION_TYPE': "cloud"
        }

        if self.docker_compose_file_path:
            extravars["DOCKER_COMPOSE_FILE_PATH"] = self.docker_compose_file_path

        self._run_ansible_playbook(extravars, 'dynamic_inventory.yml')