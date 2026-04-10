import argparse
import sys
import importlib.metadata


def main():
    parser = argparse.ArgumentParser(
        description="VM Tool: Setup, Provision, and Manage VMs"
    )
    try:
        version = importlib.metadata.version("vm_tool")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    parser.add_argument("--version", action="version", version=version)
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Config operations"
    )

    # config set
    set_parser = config_subparsers.add_parser("set", help="Set a config value")
    set_parser.add_argument("key", type=str, help="Config key")
    set_parser.add_argument("value", type=str, help="Config value")

    # config get
    get_parser = config_subparsers.add_parser("get", help="Get a config value")
    get_parser.add_argument("key", type=str, help="Config key")

    # config unset
    unset_parser = config_subparsers.add_parser("unset", help="Unset a config value")
    unset_parser.add_argument("key", type=str, help="Config key")

    # config list
    list_parser = config_subparsers.add_parser("list", help="List all config values")

    # config create-profile
    create_profile_parser = config_subparsers.add_parser(
        "create-profile", help="Create a deployment profile"
    )
    create_profile_parser.add_argument("name", type=str, help="Profile name")
    create_profile_parser.add_argument(
        "--environment",
        type=str,
        default="development",
        choices=["development", "staging", "production"],
        help="Environment tag for this profile",
    )
    create_profile_parser.add_argument("--host", type=str, help="Target host")
    create_profile_parser.add_argument("--user", type=str, help="SSH user")
    create_profile_parser.add_argument(
        "--compose-file", type=str, help="Docker Compose file"
    )

    # config list-profiles
    list_profiles_parser = config_subparsers.add_parser(
        "list-profiles", help="List all profiles"
    )

    # config delete-profile
    delete_profile_parser = config_subparsers.add_parser(
        "delete-profile", help="Delete a profile"
    )
    delete_profile_parser.add_argument("name", type=str, help="Profile name")

    # History command
    history_parser = subparsers.add_parser("history", help="Show deployment history")
    history_parser.add_argument("--host", type=str, help="Filter by host")
    history_parser.add_argument(
        "--limit", type=int, default=10, help="Number of deployments to show"
    )

    # Rollback command
    rollback_parser = subparsers.add_parser(
        "rollback", help="Rollback to previous deployment"
    )
    rollback_parser.add_argument("--host", type=str, required=True, help="Target host")
    rollback_parser.add_argument(
        "--to", type=str, help="Deployment ID to rollback to (default: previous)"
    )
    rollback_parser.add_argument(
        "--inventory", type=str, default="inventory.yml", help="Inventory file"
    )

    # Drift check command
    drift_parser = subparsers.add_parser(
        "drift-check", help="Check for configuration drift on server"
    )
    drift_parser.add_argument(
        "--host", type=str, required=True, help="Target host to check"
    )
    drift_parser.add_argument("--user", type=str, default="ubuntu", help="SSH user")

    # Backup commands
    backup_parser = subparsers.add_parser(
        "backup", help="Backup and restore operations"
    )
    backup_subparsers = backup_parser.add_subparsers(dest="backup_command")

    # backup create
    create_backup_parser = backup_subparsers.add_parser(
        "create", help="Create a backup"
    )
    create_backup_parser.add_argument("--host", type=str, required=True)
    create_backup_parser.add_argument("--user", type=str, default="ubuntu")
    create_backup_parser.add_argument(
        "--paths", type=str, nargs="+", required=True, help="Paths to backup"
    )

    # backup list
    list_backup_parser = backup_subparsers.add_parser("list", help="List backups")
    list_backup_parser.add_argument("--host", type=str, help="Filter by host")

    # backup restore
    restore_backup_parser = backup_subparsers.add_parser(
        "restore", help="Restore a backup"
    )
    restore_backup_parser.add_argument(
        "--id", type=str, required=True, help="Backup ID"
    )
    restore_backup_parser.add_argument("--host", type=str, required=True)
    restore_backup_parser.add_argument("--user", type=str, default="ubuntu")
    # VM Setup command
    setup_parser = subparsers.add_parser(
        "setup", help="Setup VM with Docker and deploy"
    )
    setup_parser.add_argument("--github-username", type=str)
    setup_parser.add_argument("--github-token", type=str)
    setup_parser.add_argument("--github-project-url", type=str, required=True)
    setup_parser.add_argument("--github-branch", type=str, default="main")
    setup_parser.add_argument(
        "--docker-compose-file-path", type=str, default="docker-compose.yml"
    )
    setup_parser.add_argument("--dockerhub-username", type=str)
    setup_parser.add_argument("--dockerhub-password", type=str)

    # Cloud Setup command
    setup_cloud_parser = subparsers.add_parser("setup-cloud", help="Setup cloud VMs")
    setup_cloud_parser.add_argument(
        "--ssh-configs", type=str, required=True, help="Path to SSH configs JSON file"
    )
    setup_cloud_parser.add_argument("--github-username", type=str)
    setup_cloud_parser.add_argument("--github-token", type=str)
    setup_cloud_parser.add_argument("--github-project-url", type=str, required=True)
    setup_cloud_parser.add_argument("--github-branch", type=str, default="main")
    setup_cloud_parser.add_argument(
        "--docker-compose-file-path", type=str, default="docker-compose.yml"
    )

    # K8s Setup command
    k8s_parser = subparsers.add_parser(
        "setup-k8s", help="Install K3s Kubernetes cluster"
    )
    k8s_parser.add_argument(
        "--inventory", type=str, default="inventory.yml", help="Inventory file to use"
    )
    # Reuse SetupRunnerConfig arguments if needed, but for now we assume inventory is enough or environment vars

    # Monitoring Setup command
    mon_parser = subparsers.add_parser(
        "setup-monitoring", help="Install Prometheus and Grafana"
    )
    mon_parser.add_argument(
        "--inventory", type=str, default="inventory.yml", help="Inventory file to use"
    )

    # Hydrate Env command
    hydrate_parser = subparsers.add_parser(
        "hydrate-env", help="Hydrate missing env files from secrets"
    )
    hydrate_parser.add_argument(
        "--compose-file",
        type=str,
        default="docker-compose.yml",
        help="Path to docker-compose.yml",
    )
    hydrate_parser.add_argument(
        "--secrets",
        type=str,
        required=True,
        help="JSON string of GitHub secrets",
    )
    hydrate_parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Project root directory",
    )

    # Docker Deploy command
    docker_parser = subparsers.add_parser(
        "deploy-docker", help="Deploy using Docker Compose"
    )
    docker_parser.add_argument(
        "--inventory", type=str, default="inventory.yml", help="Inventory file to use"
    )
    docker_parser.add_argument(
        "--compose-file",
        type=str,
        default="docker-compose.yml",
        help="Path to docker-compose.yml",
    )
    docker_parser.add_argument(
        "--host", type=str, help="Target host IP/domain (generates dynamic inventory)"
    )
    docker_parser.add_argument("--user", type=str, help="SSH username for target host")
    docker_parser.add_argument(
        "--env-file", type=str, help="Path to env file (optional)"
    )
    docker_parser.add_argument(
        "--webhook-url", type=str, help="Webhook URL for deployment notifications"
    )
    docker_parser.add_argument(
        "--notify-email",
        type=str,
        action="append",
        help="Email addresses for notifications (can be specified multiple times)",
    )
    docker_parser.add_argument(
        "--smtp-host", type=str, default="localhost", help="SMTP server host"
    )
    docker_parser.add_argument(
        "--smtp-port", type=int, default=587, help="SMTP server port"
    )
    docker_parser.add_argument(
        "--deploy-command",
        type=str,
        help="Custom deployment command (overrides default docker compose up)",
    )
    docker_parser.add_argument(
        "--profile", type=str, help="Use a saved deployment profile"
    )
    docker_parser.add_argument(
        "--force",
        action="store_true",
        help="Force redeployment even if no changes detected",
    )
    docker_parser.add_argument(
        "--health-check",
        type=str,
        help="Health check command to run after deployment (e.g., 'curl http://localhost:8000/health')",
    )
    docker_parser.add_argument(
        "--health-port",
        type=int,
        help="Port to check for availability after deployment",
    )
    docker_parser.add_argument(
        "--health-url",
        type=str,
        help="HTTP URL to check after deployment (e.g., 'http://localhost:8000/health')",
    )
    docker_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deployment without executing (shows what would be deployed)",
    )
    docker_parser.add_argument(
        "--repo-name",
        type=str,
        help="Repository name (used to default project-dir to ~/apps/NAME)",
    )
    docker_parser.add_argument(
        "--project-dir",
        type=str,
        help="Target directory on the server (default: ~/apps/<repo-name>)",
    )
    docker_parser.add_argument(
        "--health-timeout",
        type=int,
        default=300,
        help="Timeout in seconds for health checks (default: 300)",
    )

    # Kubernetes Deploy command
    k8s_deploy_parser = subparsers.add_parser(
        "deploy-k8s", help="Deploy to Kubernetes using kubectl or Helm"
    )
    k8s_deploy_parser.add_argument(
        "--method",
        type=str,
        default="manifest",
        choices=["manifest", "helm"],
        help="Deployment method: 'manifest' (kubectl apply) or 'helm' (helm upgrade --install)",
    )
    k8s_deploy_parser.add_argument(
        "--namespace", type=str, default="default", help="Kubernetes namespace"
    )
    k8s_deploy_parser.add_argument(
        "--manifest", type=str, help="Path to Kubernetes manifest file or directory"
    )
    k8s_deploy_parser.add_argument(
        "--helm-chart", type=str, help="Helm chart name or path"
    )
    k8s_deploy_parser.add_argument(
        "--helm-release", type=str, help="Helm release name"
    )
    k8s_deploy_parser.add_argument(
        "--helm-values", type=str, help="Path to Helm values file"
    )
    k8s_deploy_parser.add_argument(
        "--kubeconfig", type=str, help="Path to kubeconfig file"
    )
    k8s_deploy_parser.add_argument(
        "--host", type=str, help="Target host (where kubectl/helm runs)"
    )
    k8s_deploy_parser.add_argument(
        "--user", type=str, help="SSH user for target host"
    )
    k8s_deploy_parser.add_argument(
        "--inventory", type=str, default="inventory.yml", help="Inventory file to use"
    )
    k8s_deploy_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Rollout timeout in seconds (default: 300)",
    )
    k8s_deploy_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deployment without applying (server-side dry-run)",
    )
    k8s_deploy_parser.add_argument(
        "--force",
        action="store_true",
        help="Force redeployment even if no changes detected",
    )
    k8s_deploy_parser.add_argument(
        "--image",
        action="append",
        dest="images",
        metavar="PLACEHOLDER=IMAGE:TAG",
        help="Replace image placeholder in manifests (repeatable). "
             "Example: --image IMAGE_REGISTRY/app:IMAGE_TAG=ghcr.io/user/app:sha-abc",
    )
    k8s_deploy_parser.add_argument(
        "--k8s-secret",
        action="append",
        dest="k8s_secrets",
        metavar="NAME=KEY1=val1\\nKEY2=val2",
        help="Create/sync a generic K8s secret from env string (repeatable). "
             "Example: --k8s-secret backend-secret=\"DB_HOST=db\\nDB_PORT=5432\"",
    )
    k8s_deploy_parser.add_argument(
        "--registry-secret",
        action="append",
        dest="registry_secrets",
        metavar="NAME=SERVER:USER:TOKEN",
        help="Create/sync a docker-registry pull secret (repeatable). "
             "Example: --registry-secret ghcr-secret=ghcr.io:user:ghp_token",
    )
    k8s_deploy_parser.add_argument(
        "--kubeconfig-b64",
        type=str,
        help="Base64-encoded kubeconfig (for CI pipelines). "
             "Decoded to temp file at runtime.",
    )

    # Completion command
    completion_parser = subparsers.add_parser(
        "completion", help="Generate shell completion scripts"
    )
    completion_parser.add_argument(
        "shell",
        type=str,
        choices=["bash", "zsh", "fish"],
        help="Shell type",
    )
    completion_parser.add_argument(
        "--install",
        action="store_true",
        help="Install completion script",
    )

    # Pipeline Generator command
    pipe_parser = subparsers.add_parser(
        "generate-pipeline", help="Generate CI/CD pipeline configuration"
    )
    pipe_parser.add_argument(
        "--platform",
        type=str,
        default="github",
        choices=["github"],
        help="CI/CD Platform",
    )

    # Release Prep command
    release_parser = subparsers.add_parser(
        "prepare-release", help="Prepare Docker Compose file for release"
    )
    release_parser.add_argument(
        "--base-file", required=True, help="Base docker-compose file"
    )
    release_parser.add_argument(
        "--prod-file", required=True, help="Production overlay file"
    )
    release_parser.add_argument("--output", required=True, help="Output file path")
    release_parser.add_argument(
        "--strip-volumes", help="Comma-separated list of services to strip volumes from"
    )
    release_parser.add_argument(
        "--fix-paths", action="store_true", help="Fix CI absolute paths to relative"
    )

    # Setup CI command
    setup_ci_parser = subparsers.add_parser(
        "setup-ci", help="Configure CI environment (SSH, Inventory)"
    )
    setup_ci_parser.add_argument(
        "--provider", default="github", choices=["github"], help="CI Provider"
    )

    # Secrets command
    secrets_parser = subparsers.add_parser("secrets", help="Manage secrets")
    secrets_subparsers = secrets_parser.add_subparsers(
        dest="secrets_command", help="Secrets operations"
    )

    # secrets sync
    sync_parser = secrets_subparsers.add_parser(
        "sync", help="Sync local .env to GitHub Secrets"
    )
    sync_parser.add_argument(
        "--env-file", type=str, default=".env", help="Path to .env file"
    )
    sync_parser.add_argument(
        "--repo", type=str, help="Target GitHub repository (owner/repo)"
    )

    # Doctor command
    subparsers.add_parser("doctor", help="Check prerequisites and environment health")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show deployment state for all known hosts")
    status_parser.add_argument("--host", type=str, help="Filter by host")

    args = parser.parse_args()

    # Configure logging based on flags
    import logging

    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        print("🐛 Debug logging enabled")
    elif args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        print("📢 Verbose output enabled")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    if args.command == "config":
        from vm_tool.handlers.config import handle_config
        handle_config(args, config_parser)

    elif args.command == "history":
        from vm_tool.handlers.ops import handle_history
        handle_history(args)

    elif args.command == "rollback":
        from vm_tool.handlers.ops import handle_rollback
        handle_rollback(args)

    elif args.command == "drift-check":
        from vm_tool.handlers.ops import handle_drift
        handle_drift(args)

    elif args.command == "backup":
        from vm_tool.handlers.ops import handle_backup
        handle_backup(args)

    elif args.command == "setup":
        from vm_tool.handlers.setup import handle_setup
        handle_setup(args)

    elif args.command == "setup-cloud":
        from vm_tool.handlers.setup import handle_cloud_setup
        handle_cloud_setup(args)

    elif args.command == "setup-k8s":
        from vm_tool.handlers.setup import handle_k8s_setup
        handle_k8s_setup(args)

    elif args.command == "setup-monitoring":
        from vm_tool.handlers.setup import handle_monitoring_setup
        handle_monitoring_setup(args)

    elif args.command == "setup-ci":
        from vm_tool.handlers.setup import handle_ci_setup
        handle_ci_setup(args)

    elif args.command == "deploy-docker":
        from vm_tool.handlers.deploy import handle_docker_deploy
        handle_docker_deploy(args)

    elif args.command == "deploy-k8s":
        from vm_tool.handlers.deploy import handle_k8s_deploy
        handle_k8s_deploy(args)

    elif args.command == "hydrate-env":
        from vm_tool.handlers.tools import handle_hydrate_env
        handle_hydrate_env(args)

    elif args.command == "completion":
        from vm_tool.handlers.tools import handle_completion
        handle_completion(args)

    elif args.command == "prepare-release":
        from vm_tool.handlers.tools import handle_prepare_release
        handle_prepare_release(args)

    elif args.command == "generate-pipeline":
        from vm_tool.handlers.tools import handle_generate_pipeline
        handle_generate_pipeline(args)

    elif args.command == "secrets":
        from vm_tool.handlers.tools import handle_secrets
        handle_secrets(args)

    elif args.command == "doctor":
        from vm_tool.handlers.ops import handle_doctor
        handle_doctor(args)

    elif args.command == "status":
        from vm_tool.handlers.ops import handle_status
        handle_status(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
