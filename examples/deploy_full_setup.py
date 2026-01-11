"""
Example deployment script using run_cloud_setup for full VM provisioning.
This approach installs Docker, clones your repo, and sets up everything.
"""

import os
from vm_tool.runner import SetupRunner, SetupRunnerConfig, SSHConfig

# Configuration
config = SetupRunnerConfig(
    github_username=os.environ.get("GITHUB_USERNAME"),
    github_token=os.environ.get("GITHUB_TOKEN"),
    github_project_url=os.environ.get(
        "GITHUB_PROJECT_URL", "https://github.com/user/repo.git"
    ),
    github_branch=os.environ.get("GITHUB_BRANCH", "main"),
    docker_compose_file_path=os.environ.get(
        "DOCKER_COMPOSE_FILE", "docker-compose.yml"
    ),
    dockerhub_username=os.environ.get("DOCKERHUB_USERNAME"),
    dockerhub_password=os.environ.get("DOCKERHUB_PASSWORD"),
)

# Initialize runner
runner = SetupRunner(config)

# SSH configuration for target VM(s)
ssh_configs = [
    SSHConfig(
        ssh_username=os.environ.get("EC2_USER", "ubuntu"),
        ssh_hostname=os.environ.get("EC2_HOST"),
        ssh_identity_file=os.environ.get("SSH_IDENTITY_FILE", "~/.ssh/id_rsa"),
    ),
]

# Run full cloud setup
print("🚀 Starting full VM setup...")
print(f"   Target: {ssh_configs[0].ssh_hostname}")
print(f"   Repository: {config.github_project_url}")
print(f"   Branch: {config.github_branch}")

runner.run_cloud_setup(ssh_configs)

print("✅ VM setup complete!")
