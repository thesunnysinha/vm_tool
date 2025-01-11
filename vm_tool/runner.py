import sys
import ansible_runner
import os

class SetupRunner:
    def __init__(self, github_username, github_token, github_project_url):
        self.github_username = github_username
        self.github_token = github_token
        self.github_project_url = github_project_url

    def run_setup(self):
        # Construct extravars dictionary
        extravars = {
            'GITHUB_USERNAME': self.github_username,
            'GITHUB_TOKEN': self.github_token,
            'GITHUB_PROJECT_URL': self.github_project_url
        }

        # Get the current directory of this script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Get the virtual environment directory
        venv_dir = os.path.join(sys.prefix, 'ansible_runner_data')

        # Ensure the directory exists
        os.makedirs(venv_dir, exist_ok=True)


        # Construct dynamic paths
        playbook_path = os.path.join(current_dir, 'vm_setup', 'setup.yml')
        inventory_path = os.path.join(current_dir, 'vm_setup', 'inventory.yml')

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