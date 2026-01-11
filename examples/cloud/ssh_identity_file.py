"""
Example: Cloud VM setup using SSH key authentication (public GitHub repo).
- Connects to a remote VM using SSH key and runs setup from a public repo.
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
            ssh_identity_file="/path/to/your/ssh_key",
        )
    ]
    runner.run_cloud_setup(ssh_configs)


if __name__ == "__main__":
    main()
