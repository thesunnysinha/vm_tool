import logging
import os
import sys
from typing import List, Optional

import ansible_runner
import yaml
from pydantic import BaseModel, Field, model_validator

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

    @model_validator(mode="after")
    def check_paired_fields(self):
        """Validate that paired fields are both provided or both absent."""
        if self.env_data is not None and not self.env_path:
            raise ValueError("env_path must be provided if env_data is specified")
        if self.env_path is not None and self.env_data is None:
            raise ValueError("env_data must be provided if env_path is specified")
        if self.dockerhub_username and not self.dockerhub_password:
            raise ValueError(
                "DockerHub password must be provided if DockerHub username is specified"
            )
        if self.dockerhub_password and not self.dockerhub_username:
            raise ValueError(
                "DockerHub username must be provided if DockerHub password is specified"
            )
        if self.github_username and not self.github_token:
            raise ValueError(
                "GitHub token must be provided if GitHub username is specified"
            )
        if self.github_token and not self.github_username:
            raise ValueError(
                "GitHub username must be provided if GitHub token is specified"
            )
        return self


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

    def _get_compose_dependencies(self, compose_file: str) -> List[dict]:
        """
        Parses docker-compose file to find local file dependencies (env_files, volumes).
        Returns a list of dicts: {'src': 'local/path', 'dest': 'remote/path'}
        """
        dependencies = []
        if not os.path.exists(compose_file):
            return dependencies

        try:
            with open(compose_file, "r") as f:
                data = yaml.safe_load(f)

            if not data or "services" not in data:
                return dependencies

            found_paths = set()

            for service in data.get("services", {}).values():
                # Check env_file
                env_files = service.get("env_file", [])
                if isinstance(env_files, str):
                    env_files = [env_files]

                for env_path in env_files:
                    # Normalize local path
                    if env_path.startswith("./"):
                        clean_path = env_path[2:]
                    else:
                        clean_path = env_path

                    # Only include relative paths that are files
                    if not clean_path.startswith("/") and os.path.exists(clean_path):
                        if clean_path not in found_paths:
                            found_paths.add(clean_path)
                            dependencies.append({"src": clean_path, "dest": clean_path})
                    elif not os.path.exists(clean_path):
                        logger.warning(
                            f"⚠️  Referenced env_file not found locally: {clean_path}"
                        )

                # Check volumes (bind mounts)
                volumes = service.get("volumes", [])
                for vol in volumes:
                    host_path = None
                    if isinstance(vol, str):
                        parts = vol.split(":")
                        if len(parts) >= 2:
                            host_path = parts[0]
                    elif isinstance(vol, dict):
                        # Handle object-style volume definitions
                        if vol.get("type") == "bind":
                            host_path = vol.get("source")
                        elif "source" in vol:  # Sometimes type is omitted
                            host_path = vol.get("source")

                    if host_path:
                        # Check if it's a relative path bind mount
                        # Normalize path for existence check
                        if host_path.startswith("./"):
                            check_path = host_path[2:]
                        else:
                            check_path = host_path

                        if (
                            host_path.startswith("./")
                            or host_path.startswith("../")
                            or not host_path.startswith("/")
                        ) and os.path.exists(check_path):
                            if check_path not in found_paths:
                                found_paths.add(check_path)
                                dependencies.append(
                                    {"src": check_path, "dest": check_path}
                                )

        except Exception as e:
            logger.warning(f"Failed to parse compose file for dependencies: {e}")

        return dependencies

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
        self,
        extravars: dict,
        playbook: str = "main.yml",
        inventory_file: str = "inventory.yml",
    ):
        """Executes an Ansible playbook with the given variables and inventory.

        Args:
            extravars: Variables to pass to the playbook.
            playbook: Playbook filename (relative to vm_setup/) or absolute path.
            inventory_file: Inventory filename (relative to vm_setup/) or absolute path.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        venv_dir = os.path.join(sys.prefix, "ansible_runner_data")
        os.makedirs(venv_dir, exist_ok=True)

        if os.path.isabs(playbook):
            playbook_path = playbook
        else:
            playbook_path = os.path.join(current_dir, "vm_setup", playbook)

        if os.path.isabs(inventory_file):
            inventory_path = inventory_file
        else:
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

    def hydrate_env_from_secrets(
        self, compose_file: str, secrets_map: dict, project_root: str = "."
    ):
        """
        Scans compose file for env_files. If a file is missing locally,
        checks secrets_map for a matching key (FILENAME_EXT -> FILENAME_EXT output as SNAKE_CASE)
        and creates the file.
        Example: env/backend.env -> checks secrets_map['BACKEND_ENV']
        """
        dependencies = self._get_compose_dependencies(compose_file)

        # We need to find *potential* dependencies that might not exist yet.
        # _get_compose_dependencies only returns existing ones.
        # So we need to parse again broadly or just rely on what we find.
        # Actually, _get_compose_dependencies skips missing files.
        # So we should parse manually here to find *missing* ones.

        try:
            with open(compose_file, "r") as f:
                data = yaml.safe_load(f)

            if not data or "services" not in data:
                return

            for service in data.get("services", {}).values():
                env_files = service.get("env_file", [])
                if isinstance(env_files, str):
                    env_files = [env_files]

                for env_path in env_files:
                    # Resolve path relative to project root
                    full_path = os.path.join(project_root, env_path)

                    if not os.path.exists(full_path):
                        # Attempt to hydrate
                        filename = os.path.basename(env_path)
                        # Normalize keys: backend.env -> BACKEND_ENV
                        secret_key = filename.replace(".", "_").upper()

                        secret_value = secrets_map.get(secret_key)
                        if secret_value:
                            logger.info(
                                f"💧 Hydrating {env_path} from secret {secret_key}"
                            )
                            # Ensure directory exists
                            os.makedirs(os.path.dirname(full_path), exist_ok=True)
                            with open(full_path, "w") as out:
                                out.write(secret_value)
                        else:
                            logger.warning(
                                f"⚠️  Missing env file {env_path} and no secret found for {secret_key}"
                            )
                    else:
                        logger.debug(f"✅ Env file exists: {env_path}")

        except Exception as e:
            logger.error(f"Failed to hydrate env files: {e}")
            raise

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

        self._run_ansible_playbook(extravars, inventory_file="inventory.yml")

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

        self._run_ansible_playbook(extravars, inventory_file="dynamic_inventory.yml")

    def run_k8s_setup(self, inventory_file="inventory.yml"):
        """Runs the K8s setup playbook."""
        logger.info("Starting K8s setup...")
        # Reuse existing variables or allow bare execution
        extravars = {"ansible_python_interpreter": "/usr/bin/python3"}
        self._run_ansible_playbook(extravars, playbook="k8s.yml")
        logger.info("K8s setup completed.")

    def run_monitoring_setup(self, inventory_file="inventory.yml"):
        """Runs the Monitoring setup playbook."""
        logger.info("Starting Monitoring setup...")
        extravars = {"ansible_python_interpreter": "/usr/bin/python3"}
        self._run_ansible_playbook(extravars, playbook="monitoring.yml")
        logger.info("Monitoring setup completed.")

    def run_k8s_deploy(
        self,
        deploy_method: str = "manifest",
        namespace: str = "default",
        manifest: str = None,
        helm_chart: str = None,
        helm_release: str = None,
        helm_values: str = None,
        kubeconfig: str = None,
        kubeconfig_b64: str = None,
        inventory_file: str = "inventory.yml",
        host: str = None,
        user: str = None,
        timeout: int = 300,
        dry_run: bool = False,
        force: bool = False,
        image_substitutions: List[str] = None,
        k8s_secrets: List[str] = None,
        registry_secrets: List[str] = None,
    ):
        """Deploy to Kubernetes using kubectl/helm via Ansible.

        Args:
            deploy_method: 'manifest' or 'helm'
            namespace: Kubernetes namespace
            manifest: Path to K8s manifest file(s) or directory
            helm_chart: Helm chart name/path
            helm_release: Helm release name
            helm_values: Path to Helm values file
            kubeconfig: Path to kubeconfig file
            kubeconfig_b64: Base64-encoded kubeconfig (for CI)
            inventory_file: Ansible inventory file
            host: Target host (generates dynamic inventory)
            user: SSH user for target host
            timeout: Rollout timeout in seconds
            dry_run: Preview without applying
            force: Force redeployment
            image_substitutions: List of "PLACEHOLDER=actual-image:tag" pairs
            k8s_secrets: List of "secret-name=KEY1=val1\\nKEY2=val2" pairs
            registry_secrets: List of "secret-name=server:user:token" triples
        """
        import base64
        import tempfile
        import shutil

        from vm_tool.state import DeploymentState

        state = DeploymentState()
        temp_kubeconfig = None
        temp_manifest_dir = None

        try:
            # Handle base64-encoded kubeconfig (CI pipelines)
            if kubeconfig_b64:
                decoded = base64.b64decode(kubeconfig_b64)
                temp_kubeconfig = tempfile.NamedTemporaryFile(
                    mode="wb", suffix=".kubeconfig", delete=False
                )
                temp_kubeconfig.write(decoded)
                temp_kubeconfig.close()
                os.chmod(temp_kubeconfig.name, 0o600)
                kubeconfig = temp_kubeconfig.name
                logger.info("Decoded base64 kubeconfig to temp file")

            # Determine what to hash for idempotency
            hash_target = manifest or helm_values or helm_chart or ""
            if hash_target and os.path.exists(hash_target):
                deploy_hash = state.compute_hash(hash_target)
            else:
                deploy_hash = None

            service_name = f"k8s-{namespace}"
            if host and deploy_hash and not force and not dry_run:
                if not state.needs_update(host, deploy_hash, service_name):
                    logger.info(
                        f"Deployment is up-to-date for {host}/{namespace}. "
                        f"Use --force to redeploy."
                    )
                    print(
                        f"No changes detected for {namespace}. "
                        f"Use --force to redeploy."
                    )
                    return

            # Handle image substitutions in manifests
            if image_substitutions and manifest and deploy_method == "manifest":
                manifest = self._substitute_images(manifest, image_substitutions)
                temp_manifest_dir = os.path.dirname(manifest) if not os.path.isdir(manifest) else None

            logger.info(f"Starting Kubernetes deployment ({deploy_method}) to {namespace}...")

            # Validate method-specific args
            if deploy_method == "manifest":
                if not manifest:
                    raise ValueError("--manifest is required for manifest deployment")
                if not os.path.exists(manifest):
                    raise FileNotFoundError(f"Manifest not found: {manifest}")
            elif deploy_method == "helm":
                if not helm_chart:
                    raise ValueError("--helm-chart is required for Helm deployment")
                if not helm_release:
                    raise ValueError("--helm-release is required for Helm deployment")
                if helm_values and not os.path.exists(helm_values):
                    raise FileNotFoundError(f"Helm values file not found: {helm_values}")
            else:
                raise ValueError(f"Unknown deploy method: {deploy_method}. Use 'manifest' or 'helm'.")

            # Generate inventory
            # When --host is given: run kubectl over SSH on that host
            # When no --host: run kubectl locally (CI mode — kubeconfig points to remote cluster)
            if host:
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
            else:
                # Local execution: kubectl runs on this machine with the provided kubeconfig
                inventory_content = {
                    "all": {
                        "hosts": {
                            "localhost": {
                                "ansible_connection": "local",
                            }
                        },
                    }
                }

            current_dir = os.path.dirname(os.path.abspath(__file__))
            generated_inventory_path = os.path.join(
                current_dir, "vm_setup", "generated_inventory.yml"
            )
            with open(generated_inventory_path, "w") as f:
                yaml.dump(inventory_content, f)
            target_inventory = generated_inventory_path

            extravars = {
                "ansible_python_interpreter": "/usr/bin/python3",
                "deploy_method": deploy_method,
                "k8s_namespace": namespace,
                "rollout_timeout": f"{timeout}s",
                "dry_run": dry_run,
            }

            if kubeconfig:
                extravars["kubeconfig_path"] = os.path.abspath(kubeconfig)

            if k8s_secrets:
                extravars["k8s_generic_secrets"] = self._parse_k8s_secrets(k8s_secrets)

            if registry_secrets:
                extravars["k8s_registry_secrets"] = self._parse_registry_secrets(registry_secrets)

            if deploy_method == "manifest":
                extravars["k8s_manifest"] = os.path.abspath(manifest)
            elif deploy_method == "helm":
                extravars["helm_chart"] = helm_chart
                extravars["helm_release"] = helm_release
                if helm_values:
                    extravars["helm_values"] = os.path.abspath(helm_values)

            self._run_ansible_playbook(
                extravars,
                playbook="k8s_deploy.yml",
                inventory_file=generated_inventory_path,
            )

            # Record deployment state
            if host and deploy_hash and not dry_run:
                from vm_tool.history import DeploymentHistory

                state.record_deployment(
                    host=host,
                    compose_file=manifest or helm_chart or "",
                    compose_hash=deploy_hash,
                    service_name=service_name,
                )
                history = DeploymentHistory()
                history.record_deployment(
                    host=host,
                    compose_file=manifest or helm_chart or "",
                    compose_hash=deploy_hash,
                    status="success",
                    service_name=service_name,
                )
                logger.info(f"Kubernetes deployment to {namespace} completed.")

        finally:
            # Cleanup temp files
            if temp_kubeconfig and os.path.exists(temp_kubeconfig.name):
                os.unlink(temp_kubeconfig.name)
            if temp_manifest_dir and os.path.exists(temp_manifest_dir):
                shutil.rmtree(temp_manifest_dir, ignore_errors=True)

    @staticmethod
    def _substitute_images(manifest_path: str, substitutions: List[str]) -> str:
        """Replace image placeholders in manifest files.

        Args:
            manifest_path: Path to manifest file or directory
            substitutions: List of "PLACEHOLDER=actual-image:tag" strings

        Returns:
            Path to temp directory with substituted manifests
        """
        import tempfile
        import shutil
        import glob

        # Parse substitution pairs
        subs = {}
        for s in substitutions:
            if "=" not in s:
                raise ValueError(
                    f"Invalid --image format: {s!r}. Expected PLACEHOLDER=image:tag"
                )
            placeholder, replacement = s.split("=", 1)
            subs[placeholder] = replacement

        # Collect manifest files
        if os.path.isdir(manifest_path):
            files = sorted(glob.glob(os.path.join(manifest_path, "**/*.yaml"), recursive=True))
            files += sorted(glob.glob(os.path.join(manifest_path, "**/*.yml"), recursive=True))
        else:
            files = [manifest_path]

        if not files:
            raise FileNotFoundError(f"No YAML files found in {manifest_path}")

        # Create temp dir with substituted copies
        temp_dir = tempfile.mkdtemp(prefix="vm_tool_k8s_")
        for src_file in files:
            with open(src_file, "r") as f:
                content = f.read()

            for placeholder, replacement in subs.items():
                content = content.replace(placeholder, replacement)

            # Preserve relative structure
            if os.path.isdir(manifest_path):
                rel = os.path.relpath(src_file, manifest_path)
            else:
                rel = os.path.basename(src_file)

            dest = os.path.join(temp_dir, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w") as f:
                f.write(content)

        logger.info(f"Substituted {len(subs)} image(s) in {len(files)} manifest(s)")
        return temp_dir

    @staticmethod
    def _parse_k8s_secrets(secrets: List[str]) -> list:
        """Parse --k8s-secret flags into structured data for Ansible.

        Format: "secret-name=KEY1=val1\\nKEY2=val2"
        Returns list of dicts: [{"name": "secret-name", "data": "KEY1=val1\\nKEY2=val2"}]
        """
        result = []
        for s in secrets:
            if "=" not in s:
                raise ValueError(
                    f"Invalid --k8s-secret format: {s!r}. "
                    f"Expected name=KEY1=val1\\nKEY2=val2"
                )
            name, data = s.split("=", 1)
            if not name or not data:
                raise ValueError(f"Invalid --k8s-secret: name and data are both required")
            result.append({"name": name.strip(), "data": data})
        return result

    @staticmethod
    def _parse_registry_secrets(secrets: List[str]) -> list:
        """Parse --registry-secret flags into structured data for Ansible.

        Format: "secret-name=server:user:token"
        Returns list of dicts with name, server, username, password.
        """
        result = []
        for s in secrets:
            if "=" not in s:
                raise ValueError(
                    f"Invalid --registry-secret format: {s!r}. "
                    f"Expected name=server:user:token"
                )
            name, spec = s.split("=", 1)
            parts = spec.split(":", 2)
            if len(parts) != 3:
                raise ValueError(
                    f"Invalid --registry-secret value: {spec!r}. "
                    f"Expected server:user:token (3 colon-separated parts)"
                )
            result.append({
                "name": name.strip(),
                "server": parts[0],
                "username": parts[1],
                "password": parts[2],
            })
        return result

    def run_docker_deploy(
        self,
        compose_file="docker-compose.yml",
        inventory_file="inventory.yml",
        host: str = None,
        user: str = None,
        env_file: str = None,
        deploy_command: str = None,
        force: bool = False,
        project_dir: str = "~/app",
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
            "project_dest_dir": project_dir,
            "GITHUB_REPOSITORY_OWNER": os.environ.get("GITHUB_REPOSITORY_OWNER", ""),
        }

        if env_file:
            extravars["ENV_FILE_PATH"] = env_file

        if deploy_command:
            extravars["DEPLOY_COMMAND"] = deploy_command

        # Dynamic Dependency Detection
        dependencies = self._get_compose_dependencies(compose_file)

        # Ensure CLI-provided env_file is included in detection logic
        if env_file:
            # Normalize and check existence
            clean_env_path = env_file[2:] if env_file.startswith("./") else env_file
            if os.path.exists(clean_env_path):
                # Check if already in dependencies
                if not any(d["src"] == clean_env_path for d in dependencies):
                    dependencies.append({"src": clean_env_path, "dest": clean_env_path})

        if dependencies:
            logger.info(
                f"📦 Detected dependencies to copy: {[d['src'] for d in dependencies]}"
            )
            extravars["FILES_TO_COPY"] = dependencies

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

    @staticmethod
    def setup_ci_environment(provider="github"):
        """
        Configures CI environment (SSH, Inventory) based on standard env vars.
        Inputs (Env Vars): SSH_ID_RSA, SSH_HOSTNAME, SSH_USERNAME
        Outputs: ~/.ssh/deploy_key, inventory.yml
        """
        ssh_key = os.environ.get("SSH_ID_RSA")
        ssh_host = os.environ.get("SSH_HOSTNAME")
        ssh_user = os.environ.get("SSH_USERNAME")

        missing = []
        if not ssh_key:
            missing.append("SSH_ID_RSA")
        if not ssh_host:
            missing.append("SSH_HOSTNAME")
        if not ssh_user:
            missing.append("SSH_USERNAME")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        # 1. Setup SSH Key
        ssh_dir = os.path.expanduser("~/.ssh")
        os.makedirs(ssh_dir, exist_ok=True)
        key_path = os.path.join(ssh_dir, "deploy_key")

        # Handle both literal \n strings and actual newlines
        # GitHub secrets might store keys with literal \n or actual newlines
        ssh_key_clean = ssh_key.replace("\\n", "\n")

        # Ensure the key has proper formatting
        if not ssh_key_clean.endswith("\n"):
            ssh_key_clean += "\n"

        with open(key_path, "w") as f:
            f.write(ssh_key_clean)
        os.chmod(key_path, 0o600)
        logger.info(f"✅ SSH key written to {key_path}")

        # 2. Create Inventory
        inventory_content = {
            "all": {
                "hosts": {
                    "production": {
                        "ansible_host": ssh_host,
                        "ansible_user": ssh_user,
                        "ansible_ssh_private_key_file": key_path,
                        # Using standard CI strict checking disabled for automation
                        "ansible_ssh_common_args": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=60 -o ServerAliveCountMax=10",
                    }
                }
            }
        }

        with open("inventory.yml", "w") as f:
            yaml.dump(inventory_content, f)
        logger.info("✅ inventory.yml created")
