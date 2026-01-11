"""
Template: Local VM setup (customize for your use case)
- Use this template to create your own local VM setup script.
- Supports public/private GitHub, DockerHub, and custom Docker Compose file path.
- Fill in only the fields you need for your scenario.
"""

from vm_tool.runner import SetupRunner, SetupRunnerConfig


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
    runner.run_setup()


if __name__ == "__main__":
    main()
