import sys
import ansible_runner
import os
from pydantic import BaseModel, HttpUrl, validator

class SetupRunnerConfig(BaseModel):
    github_username: str
    github_token: str
    github_project_url: HttpUrl
    docker_compose_file_path: str = 'docker-compose.yml'

    @validator('docker_compose_file_path', pre=True, always=True)
    def set_default_docker_compose_file_path(cls, v):
        return v or 'docker-compose.yml'

class SetupRunner:
    def __init__(self, config: SetupRunnerConfig):
        self.github_username = config.github_username
        self.github_token = config.github_token
        self.github_project_url = config.github_project_url
        self.docker_compose_file_path = config.docker_compose_file_path

    def _run_ansible_playbook(self, extravars, inventory_file):
        # Get the current directory of this script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Get the virtual environment directory
        venv_dir = os.path.join(sys.prefix, 'ansible_runner_data')

        # Ensure the directory exists
        os.makedirs(venv_dir, exist_ok=True)

        # Construct dynamic paths
        playbook_path = os.path.join(current_dir, 'vm_setup', 'setup.yml')
        inventory_path = os.path.join(current_dir, 'vm_setup', inventory_file)

        try:
            # Run the Ansible playbook using ansible-runner
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
        # Construct extravars dictionary
        extravars = {
            'GITHUB_USERNAME': self.github_username,
            'GITHUB_TOKEN': self.github_token,
            'GITHUB_PROJECT_URL': self.github_project_url,
            'EXECUTION_TYPE': "normal"
        }

        if self.docker_compose_file_path:
            extravars["DOCKER_COMPOSE_FILE_PATH"] = self.docker_compose_file_path

        self._run_ansible_playbook(extravars, 'inventory.yml')

    def run_cloud_setup(self, ssh_username: str, ssh_password: str, ssh_hostname: str):
        # Construct extravars dictionary
        extravars = {
            'SSH_USERNAME': ssh_username,
            'SSH_PASSWORD': ssh_password,
            'SSH_HOSTNAME': ssh_hostname,
            'GITHUB_USERNAME': self.github_username,
            'GITHUB_TOKEN': self.github_token,
            'GITHUB_PROJECT_URL': self.github_project_url,
            'EXECUTION_TYPE': "cloud"
        }

        if self.docker_compose_file_path:
            extravars["DOCKER_COMPOSE_FILE_PATH"] = self.docker_compose_file_path

        self._run_ansible_playbook(extravars, 'cloud_inventory.yml')