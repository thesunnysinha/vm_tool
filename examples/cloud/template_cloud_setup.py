"""
Template: Cloud VM setup (customize for your use case)
- Use this template to create your own cloud VM setup script.
- Supports public/private GitHub, DockerHub, SSH key or password authentication, and multiple VMs.
- Fill in only the fields you need for your scenario.
"""

from vm_tool.runner import SetupRunner, SetupRunnerConfig, SSHConfig


def main():
    # Fill in only the fields you need for your use case
    config = SetupRunnerConfig(
        github_username=None,  # e.g., 'your_github_username' (for private repos)
        github_token=None,  # e.g., 'your_github_token' (for private repos)
        github_project_url="https://github.com/username/your-repo",
        github_branch="main",  # Optional, defaults to 'main'
        docker_compose_file_path="docker-compose.yml",  # Optional
        dockerhub_username=None,  # e.g., 'your_dockerhub_username' (if DockerHub login needed)
        dockerhub_password=None,  # e.g., 'your_dockerhub_password' (if DockerHub login needed)
    )
    runner = SetupRunner(config)
    ssh_configs = [
        SSHConfig(
            ssh_username="your_ssh_username",
            ssh_hostname="your_ssh_hostname",
            ssh_identity_file=None,  # e.g., '/path/to/your/ssh_key' (for SSH key auth)
            ssh_password=None,  # e.g., 'your_ssh_password' (for SSH password auth)
        )
        # Add more SSHConfig instances for multiple VMs if needed
    ]
    runner.run_cloud_setup(ssh_configs)


if __name__ == "__main__":
    main()
