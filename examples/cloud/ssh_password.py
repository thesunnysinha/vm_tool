"""
Example: Cloud VM setup using SSH password authentication (public GitHub repo).
- Connects to a remote VM using SSH username/password and runs setup from a public repo.
"""

from vm_tool.runner import SetupRunner, SetupRunnerConfig, SSHConfig


def main():
    config = SetupRunnerConfig(
        github_project_url="https://github.com/username/public-repo",
        github_branch="main",
        docker_compose_file_path="docker-compose.yml",
    )
    runner = SetupRunner(config)
    ssh_configs = [
        SSHConfig(
            ssh_username="your_ssh_username",
            ssh_hostname="your_ssh_hostname",
            ssh_password="your_ssh_password",
        )
    ]
    runner.run_cloud_setup(ssh_configs)


if __name__ == "__main__":
    main()
