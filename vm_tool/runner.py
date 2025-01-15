import sys
import ansible_runner
import os
import yaml
from pydantic import BaseModel, HttpUrl, validator
from typing import List

class SetupRunnerConfig(BaseModel):
    github_username: str
    github_token: str
    github_project_url: HttpUrl
    docker_compose_file_path: str = 'docker-compose.yml'

    @validator('docker_compose_file_path', pre=True, always=True)
    def set_default_docker_compose_file_path(cls, v):
        return v or 'docker-compose.yml'

class SSHConfig(BaseModel):
    ssh_username: str
    ssh_password: str
    ssh_hostname: str

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

    def run_cloud_setup(self, ssh_configs: List[SSHConfig]):
        # Define the path for the dynamic inventory file
        inventory_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vm_setup', 'dynamic_inventory.yml')

        # Check if the dynamic inventory file already exists
        if os.path.exists(inventory_file_path):
            # Read the existing inventory file
            with open(inventory_file_path, 'r') as inventory_file:
                inventory_content = yaml.safe_load(inventory_file)
        else:
            # Create dynamic inventory content
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
                inventory_content['all']['hosts'][host_key] = {
                    'ansible_host': ssh_config.ssh_hostname,
                    'ansible_user': ssh_config.ssh_username,
                    'ansible_ssh_pass': ssh_config.ssh_password
                }

            # Write dynamic inventory to a file
            with open(inventory_file_path, 'w') as inventory_file:
                yaml.dump(inventory_content, inventory_file)

        # Construct extravars dictionary
        extravars = {
            'GITHUB_USERNAME': self.github_username,
            'GITHUB_TOKEN': self.github_token,
            'GITHUB_PROJECT_URL': self.github_project_url,
            'EXECUTION_TYPE': "cloud"
        }

        if self.docker_compose_file_path:
            extravars["DOCKER_COMPOSE_FILE_PATH"] = self.docker_compose_file_path

        self._run_ansible_playbook(extravars, 'dynamic_inventory.yml')