import ansible_runner

class SetupRunner:
    def __init__(self, ssh_host, ssh_user, ssh_password, become_pass, github_username, github_token, github_project_url):
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.become_pass = become_pass
        self.github_username = github_username
        self.github_token = github_token
        self.github_project_url = github_project_url

    def run_setup(self):
        # Construct extravars dictionary
        extravars = {
            'ANSIBLE_SSH_HOST': self.ssh_host,
            'ANSIBLE_SSH_USER': self.ssh_user,
            'ANSIBLE_SSH_PASS': self.ssh_password,
            'ANSIBLE_BECOME_PASS': self.become_pass,
            'GITHUB_USERNAME': self.github_username,
            'GITHUB_TOKEN': self.github_token,
            'GITHUB_PROJECT_URL': self.github_project_url
        }

        # Run the Ansible playbook using ansible-runner
        r = ansible_runner.run(
            private_data_dir='.',
            playbook='vm_tool/vm_setup/setup.yml',
            inventory='vm_tool/vm_setup/inventory.yml',
            extravars=extravars
        )

        if r.rc != 0:
            raise RuntimeError(f"Ansible playbook execution failed: {r.stdout}")

        print(r.stdout)