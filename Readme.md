### Welcome to initial setup of the application

1. Connect to deployment machine using VSCode.

2. Run the following command to install the package and its dependencies:
```bash
pip install .
```

### This is a tool to setup VMs using Ansible.

## Example usage:

```bash
    from vm_tool import SetupRunner

    runner = SetupRunner(
        ssh_host='your_host', # e.g. 192.168.1.1
        ssh_user='your_user', # e.g. root
        ssh_password='your_password', # e.g. password
        become_pass='your_become_pass', # e.g. password
        github_username='your_github_username', # e.g. username
        github_token='your_github_token', # e.g. token
        github_project_url='your_github_project_url' # e.g. https://github.com/username/repo
    )

    runner.run_setup()
```