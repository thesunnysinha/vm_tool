import logging
import os
import sys
from typing import List, Optional

import ansible_runner
import yaml
from pydantic import BaseModel, Field, model_validator, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SetupRunnerConfig(BaseModel):
    """
    Configuration model for setting up the runner.

    Attributes:
        github_username (Optional[str]): GitHub username for authentication.
        github_token (Optional[str]): GitHub token for authentication.
        github_project_url (str): URL of the GitHub repository.
        github_branch (str): GitHub branch to use (default: 'main').
        docker_compose_file_path (str): Path to the Docker Compose file (default: 'docker-compose.yml').
        dockerhub_username (Optional[str]): DockerHub username (optional).
        dockerhub_password (Optional[str]): DockerHub password (required if username is provided).
        env_path (Optional[str]): Path where the environment file should be created (optional).
        env_data (Optional[dict]): Environment data to dump into the file (optional, should be a dict).
    """

    github_username: Optional[str] = Field(
        default=None, description="GitHub username for authentication (optional)"
    )
    github_token: Optional[str] = Field(
        default=None, description="GitHub token for authentication (optional)"
    )
    github_project_url: str = Field(..., description="URL of the GitHub repository")
    github_branch: str = Field(
        default="main", description="GitHub branch to use (default: 'main')"
    )
    docker_compose_file_path: str = Field(
        default="docker-compose.yml",
        description="Path to the Docker Compose file (default: 'docker-compose.yml')",
    )
    dockerhub_username: Optional[str] = Field(
        default=None, description="DockerHub username (optional)"
    )
    dockerhub_password: Optional[str] = Field(
        default=None,
        description="DockerHub password (required if username is provided)",
    )
    env_path: Optional[str] = Field(
        default=None,
        description="Path where the environment file should be created (optional)",
    )
    env_data: Optional[dict] = Field(
        default=None,
        description="Environment data to dump into the file (optional, should be a dict)",
    )

    @validator("env_path", always=True)
    def check_env_path_with_env_data(cls, v, values):
        """If env_data is provided, env_path must also be provided."""
        if values.get("env_data") is not None and not v:
            raise ValueError("env_path must be provided if env_data is specified")
        return v

    @validator("env_data", always=True)
    def check_env_data_with_env_path(cls, v, values):
        """If env_path is provided, env_data must also be provided."""
        if values.get("env_path") is not None and v is None:
            raise ValueError("env_data must be provided if env_path is specified")
        return v

    @validator("dockerhub_password", always=True)
    def check_dockerhub_password(cls, v, values):
        """Ensures that a password is provided if a DockerHub username is set."""
        if values.get("dockerhub_username") and not v:
            raise ValueError(
                "DockerHub password must be provided if DockerHub username is specified"
            )
        return v

    @validator("dockerhub_username", always=True)
    def check_dockerhub_username(cls, v, values):
        """Ensures that a username is provided if a DockerHub password is set."""
        if values.get("dockerhub_password") and not v:
            raise ValueError(
                "DockerHub username must be provided if DockerHub password is specified"
            )
        return v

    @validator("github_token", always=True)
    def check_github_token(cls, v, values):
        """Ensures that a GitHub token is provided if a GitHub username is set."""
        if values.get("github_username") and not v:
            raise ValueError(
                "GitHub token must be provided if GitHub username is specified"
            )
        return v

    @validator("github_username", always=True)
    def check_github_username(cls, v, values):
        """Ensures that a GitHub username is provided if a GitHub token is set."""
        if values.get("github_token") and not v:
            raise ValueError(
                "GitHub username must be provided if GitHub token is specified"
            )
        return v


class SSHConfig(BaseModel):
    """
    Configuration model for SSH authentication.

    Attributes:
        ssh_username (str): SSH username.
        ssh_hostname (str): SSH host/IP.
        ssh_password (Optional[str]): SSH password (optional if identity file is provided).
        ssh_identity_file (Optional[str]): Path to SSH private key file (optional if password is provided).
    """

    ssh_username: str = Field(..., description="SSH username")
    ssh_hostname: str = Field(..., description="SSH host/IP")
    ssh_password: Optional[str] = Field(
        default=None, description="SSH password (optional if identity file is provided)"
    )
    ssh_identity_file: Optional[str] = Field(
        default=None,
        description="Path to SSH private key file (optional if password is provided)",
    )

    @model_validator(mode="before")
    def validate_authentication(cls, values):
        """Ensures that either an SSH password or identity file is provided for authentication."""
        password = values.get("ssh_password")
        identity_file = values.get("ssh_identity_file")
        if not password and not identity_file:
            raise ValueError(
                "Either ssh_password or ssh_identity_file must be provided."
            )
        return values


class SetupRunner:
    """
    Main class to handle setup execution.

    Attributes:
        github_username (str): GitHub username.
        github_token (str): GitHub token.
        github_project_url (str): GitHub repository URL.
        github_branch (str): GitHub branch to use.
        docker_compose_file_path (str): Path to Docker Compose file.
        dockerhub_username (str): DockerHub username.
        dockerhub_password (str): DockerHub password.
    """

    def __init__(self, config: SetupRunnerConfig):
        """Initializes the setup runner with the given configuration."""
        self.config = config
        self.github_username = config.github_username
        self.github_token = config.github_token
        self.github_project_url = config.github_project_url
        self.github_branch = config.github_branch
        self.docker_compose_file_path = config.docker_compose_file_path
        self.dockerhub_username = config.dockerhub_username
        self.dockerhub_password = config.dockerhub_password
        self.env_path = config.env_path
        self.env_data = config.env_data

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash if in a git repository."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _run_ansible_playbook(
        self, extravars: dict, inventory_file: str = "inventory.yml"
    ):
        """Executes an Ansible playbook with the given variables and inventory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        venv_dir = os.path.join(sys.prefix, "ansible_runner_data")
        os.makedirs(venv_dir, exist_ok=True)

        playbook_path = os.path.join(current_dir, "vm_setup", "main.yml")
        inventory_path = os.path.join(current_dir, "vm_setup", inventory_file)

        try:
            r = ansible_runner.run(
                private_data_dir=venv_dir,
                playbook=playbook_path,
                inventory=inventory_path,
                extravars=extravars,
            )

            if r.rc != 0:
                logger.error(
                    f"Ansible playbook execution failed with return code {r.rc}: {r.stdout}"
                )
                raise RuntimeError(
                    f"Ansible playbook execution failed with return code {r.rc}: {r.stdout}"
                )

            logger.info("Ansible playbook executed successfully.")

        except Exception as e:
            logger.error(
                f"An error occurred while running the Ansible playbook: {str(e)}"
            )
            raise RuntimeError(
                f"An error occurred while running the Ansible playbook: {str(e)}"
            )

    def run_setup(self):
        """Runs the setup process using Ansible."""
        extravars = {
            "GITHUB_USERNAME": self.github_username,
            "GITHUB_TOKEN": self.github_token,
            "GITHUB_PROJECT_URL": self.github_project_url,
            "GITHUB_BRANCH": self.github_branch,
            "DOCKERHUB_USERNAME": self.dockerhub_username,
            "DOCKERHUB_PASSWORD": self.dockerhub_password,
            "EXECUTION_TYPE": "normal",
        }

        if self.docker_compose_file_path:
            extravars["DOCKER_COMPOSE_FILE_PATH"] = self.docker_compose_file_path
        if self.env_path and self.env_data:
            extravars["ENV_PATH"] = self.env_path
            extravars["ENV_DATA"] = self.env_data

        self._run_ansible_playbook(extravars, "inventory.yml")

    def run_cloud_setup(self, ssh_configs: List[SSHConfig]):
        """Runs the cloud setup using Ansible with dynamic inventory generation."""
        inventory_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "vm_setup",
            "dynamic_inventory.yml",
        )

        inventory_content = {
            "all": {
                "hosts": {},
                "vars": {"ansible_python_interpreter": "/usr/bin/python3"},
            }
        }

        for i, ssh_config in enumerate(ssh_configs):
            host_key = f"cloud_host_{i}"
            host_entry = {
                "ansible_host": ssh_config.ssh_hostname,
                "ansible_user": ssh_config.ssh_username,
            }
            if ssh_config.ssh_identity_file:
                host_entry["ansible_ssh_private_key_file"] = (
                    ssh_config.ssh_identity_file
                )
            elif ssh_config.ssh_password:
                host_entry["ansible_ssh_pass"] = ssh_config.ssh_password

            inventory_content["all"]["hosts"][host_key] = host_entry

        with open(inventory_file_path, "w") as inventory_file:
            yaml.dump(inventory_content, inventory_file)

        extravars = {
            "GITHUB_USERNAME": self.github_username,
            "GITHUB_TOKEN": self.github_token,
            "GITHUB_PROJECT_URL": self.github_project_url,
            "GITHUB_BRANCH": self.github_branch,
            "DOCKERHUB_USERNAME": self.dockerhub_username,
            "DOCKERHUB_PASSWORD": self.dockerhub_password,
            "EXECUTION_TYPE": "cloud",
        }

        if self.docker_compose_file_path:
            extravars["DOCKER_COMPOSE_FILE_PATH"] = self.docker_compose_file_path
        if self.env_path and self.env_data:
            extravars["ENV_PATH"] = self.env_path
            extravars["ENV_DATA"] = self.env_data

        self._run_ansible_playbook(extravars, "dynamic_inventory.yml")

    def run_k8s_setup(self, inventory_file="inventory.yml"):
        """Runs the K8s setup playbook."""
        logger.info("Starting K8s setup...")
        # Reuse existing variables or allow bare execution
        extravars = {"ansible_python_interpreter": "/usr/bin/python3"}
        self._run_ansible_playbook(extravars, "k8s.yml")
        logger.info("K8s setup completed.")

    def run_monitoring_setup(self, inventory_file="inventory.yml"):
        """Runs the Monitoring setup playbook."""
        logger.info("Starting Monitoring setup...")
        extravars = {"ansible_python_interpreter": "/usr/bin/python3"}
        self._run_ansible_playbook(extravars, "monitoring.yml")
        logger.info("Monitoring setup completed.")

    def run_docker_deploy(
        self,
        compose_file="docker-compose.yml",
        inventory_file="inventory.yml",
        host: str = None,
        user: str = None,
        env_file: str = None,
        deploy_command: str = None,
        force: bool = False,
    ):
        """Runs the Docker Compose deployment with idempotency."""
        from vm_tool.state import DeploymentState

        # Initialize state tracker
        state = DeploymentState()

        # Compute hash of compose file for change detection
        compose_hash = state.compute_hash(compose_file)

        # Check if deployment is needed (unless force is True)
        service_name = "docker-compose"
        if host and not force:
            if not state.needs_update(host, compose_hash, service_name):
                logger.info(
                    f"✅ Deployment is up-to-date for {host}. "
                    f"Use --force to redeploy anyway."
                )
                print(
                    f"✅ No changes detected. Deployment is up-to-date.\n"
                    f"   Use --force flag to redeploy anyway."
                )
                return

        target_inventory = inventory_file

        # Generate dynamic inventory if host is provided
        if host:
            logger.info(f"Generating dynamic inventory for host: {host}")
            inventory_content = {
                "all": {
                    "hosts": {
                        "target_host": {
                            "ansible_host": host,
                            "ansible_connection": "ssh",
                            "ansible_ssh_common_args": "-o StrictHostKeyChecking=no",
                        }
                    },
                    "vars": {"ansible_python_interpreter": "/usr/bin/python3"},
                }
            }
            if user:
                inventory_content["all"]["hosts"]["target_host"]["ansible_user"] = user

            # Use a temporary file or override inventory.yml locally
            current_dir = os.path.dirname(os.path.abspath(__file__))
            generated_inventory_path = os.path.join(
                current_dir, "vm_setup", "generated_inventory.yml"
            )

            with open(generated_inventory_path, "w") as f:
                yaml.dump(inventory_content, f)

            target_inventory = generated_inventory_path

        else:
            # If not generating dynamic inventory, ensure the provided inventory path is absolute
            target_inventory = os.path.abspath(inventory_file)

        logger.info(
            f"Starting Docker deployment using {compose_file} on {target_inventory}..."
        )

        extravars = {
            "ansible_python_interpreter": "/usr/bin/python3",
            "DOCKER_COMPOSE_FILE_PATH": compose_file,
            "GITHUB_USERNAME": self.github_username,
            "GITHUB_TOKEN": self.github_token,
            "GITHUB_PROJECT_URL": self.github_project_url,
            "DEPLOY_MODE": "push",
            "SOURCE_PATH": os.getcwd(),  # Current working directory where vm_tool is run
            "project_dest_dir": "~/app",
            "GITHUB_REPOSITORY_OWNER": os.environ.get("GITHUB_REPOSITORY_OWNER", ""),
        }

        if env_file:
            extravars["ENV_FILE_PATH"] = env_file

        if deploy_command:
            extravars["DEPLOY_COMMAND"] = deploy_command

        playbook_path = os.path.join(
            os.path.dirname(__file__), "vm_setup", "push_code.yml"
        )

        try:
            r = ansible_runner.run(
                private_data_dir=os.path.dirname(__file__),
                playbook=playbook_path,
                inventory=target_inventory,
                extravars=extravars,
            )

            if r.status == "successful":
                logger.info("Docker deployment completed successfully.")
                # Record successful deployment
                if host:
                    state.record_deployment(
                        host, compose_file, compose_hash, service_name
                    )
                    logger.info(f"✅ Deployment state recorded for {host}")

                    # Record in history
                    from vm_tool.history import DeploymentHistory

                    history = DeploymentHistory()
                    git_commit = self._get_git_commit()
                    deployment_id = history.record_deployment(
                        host=host,
                        compose_file=compose_file,
                        compose_hash=compose_hash,
                        git_commit=git_commit,
                        service_name=service_name,
                        status="success",
                    )
                    logger.info(f"📝 Deployment recorded in history: {deployment_id}")
            else:
                error_msg = f"Deployment failed with status: {r.status}"
                logger.error(error_msg)
                if host:
                    state.mark_failed(host, service_name, error_msg)
                raise RuntimeError(error_msg)

        except Exception as e:
            if host:
                state.mark_failed(host, service_name, str(e))
            raise
