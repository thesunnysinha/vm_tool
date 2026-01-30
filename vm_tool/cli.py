import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="VM Tool: Setup, Provision, and Manage VMs"
    )
    parser.add_argument("--version", action="version", version="1.0.37")
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
        from vm_tool.config import Config

        config = Config()

        if args.config_command == "set":
            config.set(args.key, args.value)
            print(f"✅ Set {args.key} = {args.value}")

        elif args.config_command == "get":
            value = config.get(args.key)
            if value is not None:
                print(f"{args.key} = {value}")
            else:
                print(f"❌ Config key '{args.key}' not found")
                sys.exit(1)

        elif args.config_command == "unset":
            config.unset(args.key)
            print(f"✅ Unset {args.key}")

        elif args.config_command == "list":
            all_config = config.list_all()
            if all_config:
                print("📋 Configuration:")
                for key, value in all_config.items():
                    print(f"  {key} = {value}")
            else:
                print("No configuration set")

        elif args.config_command == "create-profile":
            profile_data = {}
            if args.host:
                profile_data["host"] = args.host
            if args.user:
                profile_data["user"] = args.user
            if args.compose_file:
                profile_data["compose_file"] = args.compose_file

            config.create_profile(
                args.name, environment=args.environment, **profile_data
            )
            print(f"✅ Created profile '{args.name}' (environment: {args.environment})")

        elif args.config_command == "list-profiles":
            profiles = config.list_profiles()
            if profiles:
                print("📋 Profiles:")
                for name, data in profiles.items():
                    print(f"  {name}:")
                    for key, value in data.items():
                        print(f"    {key} = {value}")
            else:
                print("No profiles configured")

        elif args.config_command == "delete-profile":
            config.delete_profile(args.name)
            print(f"✅ Deleted profile '{args.name}'")

        else:
            config_parser.print_help()

    elif args.command == "history":
        from vm_tool.history import DeploymentHistory

        history = DeploymentHistory()
        deployments = history.get_history(host=args.host, limit=args.limit)

        if not deployments:
            print("No deployment history found")
        else:
            print(
                f"\n📜 Deployment History (showing {len(deployments)} deployments):\n"
            )
            for dep in deployments:
                status_icon = "✅" if dep.get("status") == "success" else "❌"
                print(f"{status_icon} {dep['id']} - {dep['timestamp']}")
                print(f"   Host: {dep['host']}")
                print(f"   Service: {dep.get('service_name', 'default')}")
                print(f"   Compose: {dep['compose_file']}")
                if dep.get("git_commit"):
                    print(f"   Git: {dep['git_commit'][:8]}")
                if dep.get("error"):
                    print(f"   Error: {dep['error']}")
                print()

    elif args.command == "rollback":
        from vm_tool.history import DeploymentHistory
        from vm_tool.runner import SetupRunner, SetupRunnerConfig

        history = DeploymentHistory()
        rollback_info = history.get_rollback_info(args.host, args.to)

        if not rollback_info:
            print(f"❌ No deployment found to rollback to")
            sys.exit(1)

        print(f"\n🔄 Rolling back to deployment: {rollback_info['id']}")
        print(f"   Timestamp: {rollback_info['timestamp']}")
        print(f"   Compose: {rollback_info['compose_file']}")
        if rollback_info.get("git_commit"):
            print(f"   Git commit: {rollback_info['git_commit'][:8]}")

        confirm = input("\nProceed with rollback? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("❌ Rollback cancelled")
            sys.exit(0)

        try:
            config = SetupRunnerConfig(github_project_url="dummy")
            runner = SetupRunner(config)
            runner.run_docker_deploy(
                compose_file=rollback_info["compose_file"],
                inventory_file=args.inventory,
                host=args.host,
                user=None,  # Will use inventory
                force=True,  # Force redeployment
            )
            print("\n✅ Rollback completed successfully")
        except Exception as e:
            print(f"\n❌ Rollback failed: {e}")
            sys.exit(1)

    elif args.command == "drift-check":
        from vm_tool.drift import DriftDetector

        detector = DriftDetector()
        drifts = detector.check_drift(args.host, args.user)

        if not drifts:
            print(f"✅ No drift detected on {args.host}")
        else:
            print(f"\n⚠️  Drift Detected on {args.host}:\n")
            for drift in drifts:
                status_icon = "🔄" if drift["status"] == "modified" else "❌"
                print(f"{status_icon} {drift['file']}")
                print(f"   Status: {drift['status']}")
                print(f"   Expected: {drift['expected'][:16]}...")
                if drift["actual"]:
                    print(f"   Actual: {drift['actual'][:16]}...")
                print()
            print(f"Found {len(drifts)} file(s) with drift")
            sys.exit(1)

    elif args.command == "backup":
        from vm_tool.backup import BackupManager

        manager = BackupManager()

        if args.backup_command == "create":
            try:
                backup_id = manager.create_backup(
                    host=args.host, user=args.user, paths=args.paths
                )
                print(f"✅ Backup created: {backup_id}")
            except Exception as e:
                print(f"❌ Backup failed: {e}")
                sys.exit(1)

        elif args.backup_command == "list":
            backups = manager.list_backups(host=args.host)
            if not backups:
                print("No backups found")
            else:
                print(f"\\n📦 Available Backups ({len(backups)}):\\n")
                for backup in backups:
                    size_mb = backup["size"] / (1024 * 1024)
                    print(f"  {backup['id']}")
                    print(f"    Host: {backup['host']}")
                    print(f"    Time: {backup['timestamp']}")
                    print(f"    Size: {size_mb:.2f} MB")
                    print(f"    Paths: {', '.join(backup['paths'])}")
                    print()

        elif args.backup_command == "restore":
            try:
                manager.restore_backup(args.id, args.host, args.user)
                print(f"✅ Backup restored: {args.id}")
            except Exception as e:
                print(f"❌ Restore failed: {e}")
                sys.exit(1)

    elif args.command == "setup":
        from vm_tool.runner import SetupRunner, SetupRunnerConfig

        config = SetupRunnerConfig(
            github_username=args.github_username,
            github_token=args.github_token,
            github_project_url=args.github_project_url,
            github_branch=args.github_branch,
            docker_compose_file_path=args.docker_compose_file_path,
            dockerhub_username=args.dockerhub_username,
            dockerhub_password=args.dockerhub_password,
        )
        runner = SetupRunner(config)
        runner.run_setup()
        print("✅ VM setup complete!")

    elif args.command == "setup-cloud":
        import json
        from vm_tool.runner import SetupRunner, SetupRunnerConfig, SSHConfig

        config = SetupRunnerConfig(
            github_username=args.github_username,
            github_token=args.github_token,
            github_project_url=args.github_project_url,
            github_branch=args.github_branch,
            docker_compose_file_path=args.docker_compose_file_path,
        )
        runner = SetupRunner(config)

        # Load SSH configs from JSON file
        with open(args.ssh_configs, "r") as f:
            ssh_data = json.load(f)

        ssh_configs = [SSHConfig(**cfg) for cfg in ssh_data]
        runner.run_cloud_setup(ssh_configs)
        print("✅ Cloud setup complete!")

    elif args.command == "setup-k8s":
        try:
            # We need a dummy config to init SetupRunner, or refactor SetupRunner to be more flexible.
            # For now, we pass minimal required args.
            from vm_tool.runner import SetupRunner, SetupRunnerConfig

            config = SetupRunnerConfig(github_project_url="dummy")
            runner = SetupRunner(config)
            runner.run_k8s_setup(inventory_file=args.inventory)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "setup-monitoring":
        try:
            from vm_tool.runner import SetupRunner, SetupRunnerConfig

            config = SetupRunnerConfig(github_project_url="dummy")
            runner = SetupRunner(config)
            runner.run_monitoring_setup(inventory_file=args.inventory)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "deploy-docker":
        try:
            from vm_tool.config import Config
            from vm_tool.runner import SetupRunner, SetupRunnerConfig

            # Load profile if specified
            profile_data = {}
            if args.profile:
                config = Config()
                profile_data = config.get_profile(args.profile) or {}
                if not profile_data:
                    print(f"❌ Profile '{args.profile}' not found")
                    sys.exit(1)
                print(f"📋 Using profile: {args.profile}")

                # Safety check for production deployments
                if profile_data.get("environment") == "production":
                    if not args.force:
                        confirm = (
                            input(
                                "⚠️  You are deploying to PRODUCTION. Type 'yes' to confirm: "
                            )
                            .strip()
                            .lower()
                        )
                        if confirm != "yes":
                            print("❌ Deployment cancelled")
                            sys.exit(0)

            # Merge profile with CLI args (CLI args take precedence)
            host = args.host or profile_data.get("host")
            user = args.user or profile_data.get("user")
            compose_file = args.compose_file or profile_data.get(
                "compose_file", "docker-compose.yml"
            )

            # Dry-run mode: show what would be deployed
            if args.dry_run:
                print("\n🔍 DRY-RUN MODE - No changes will be made\n")
                print(f"📋 Deployment Plan:")
                print(f"   Target Host: {host or 'from inventory'}")
                print(f"   SSH User: {user or 'from inventory'}")
                print(f"   Compose File: {compose_file}")
                print(f"   Inventory: {args.inventory}")
                if args.env_file:
                    print(f"   Env File: {args.env_file}")
                if args.deploy_command:
                    print(f"   Custom Command: {args.deploy_command}")

                # Show compose file contents
                import os

                if os.path.exists(compose_file):
                    print(f"\n📄 Compose File Contents ({compose_file}):")
                    with open(compose_file, "r") as f:
                        for i, line in enumerate(f, 1):
                            print(f"   {i:3d} | {line.rstrip()}")
                else:
                    print(f"\n⚠️  Compose file not found: {compose_file}")

                print(f"\n✅ Dry-run complete. Use without --dry-run to deploy.")
                sys.exit(0)

            # For deployment, we might need github creds if the playbook pulls code
            # But for now we use dummy or env vars
            config = SetupRunnerConfig(github_project_url="dummy")
            runner = SetupRunner(config)
            runner.run_docker_deploy(
                compose_file=compose_file,
                inventory_file=args.inventory,
                host=host,
                user=user,
                env_file=args.env_file,
                deploy_command=args.deploy_command,
                force=args.force,
            )

            # Run health checks if specified
            if host and (args.health_check or args.health_port or args.health_url):
                from vm_tool.health import SmokeTestSuite

                print("\n🏥 Running Health Checks...")
                suite = SmokeTestSuite(host)

                if args.health_port:
                    suite.add_port_check(args.health_port)

                if args.health_url:
                    suite.add_http_check(args.health_url)

                if args.health_check:
                    suite.add_custom_check(args.health_check, "Custom Health Check")

                if not suite.run_all():
                    print(
                        "\n❌ Health checks failed. Deployment may not be working correctly."
                    )
                    sys.exit(1)
                else:
                    print("\n✅ All health checks passed!")

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "completion":
        from vm_tool.completion import print_completion, install_completion

        if args.install:
            try:
                path = install_completion(args.shell)
                print(f"✅ Completion installed: {path}")
                print(f"\nTo activate, run:")
                if args.shell == "bash":
                    print(f"  source {path}")
                elif args.shell == "zsh":
                    print(
                        f"  # Add to ~/.zshrc: fpath=({os.path.dirname(path)} $fpath)"
                    )
                    print(f"  # Then run: compinit")
                elif args.shell == "fish":
                    print(f"  # Restart your shell or run: source {path}")
            except Exception as e:
                print(f"❌ Failed to install completion: {e}")
                sys.exit(1)
        else:
            print_completion(args.shell)

    elif args.command == "generate-pipeline":
        try:
            from vm_tool.generator import PipelineGenerator

            print("🚀 Configuring your CI/CD Pipeline...")

            # Interactive prompts
            branch = (
                input("Enter the branch to trigger deployment [main]: ").strip()
                or "main"
            )
            python_version = input("Enter Python version [3.12]: ").strip() or "3.12"

            enable_linting = (
                input("Include Linting step (flake8)? [y/N]: ").strip().lower()
            )
            run_linting = enable_linting in ("y", "yes")

            enable_tests = (
                input("Include Testing step (pytest)? [y/N]: ").strip().lower()
            )
            run_tests = enable_tests in ("y", "yes")

            enable_monitoring = (
                input("Include Monitoring (Prometheus/Grafana)? [y/N]: ")
                .strip()
                .lower()
            )
            setup_monitoring = enable_monitoring in ("y", "yes")

            dep_type_input = (
                input("Deployment Type (docker/registry/custom) [docker]: ")
                .strip()
                .lower()
            )
            deployment_type = "docker"
            strategy = "docker"

            if dep_type_input in ("custom", "c"):
                deployment_type = "custom"
                strategy = "custom"
            elif dep_type_input in ("registry", "ghcr", "r"):
                deployment_type = "docker"
                strategy = "registry"
            elif dep_type_input in ("kubernetes", "k8s", "k"):
                deployment_type = "kubernetes"
                strategy = "kubernetes"

            docker_compose_file = "docker-compose.yml"
            env_file = None
            deploy_command = None

            if deployment_type == "custom":
                deploy_command = input("Enter custom deployment command: ").strip()

            elif deployment_type == "docker":
                docker_compose_file = (
                    input(
                        "Enter Docker Compose file name [docker-compose.yml]: "
                    ).strip()
                    or "docker-compose.yml"
                )
                env_file_input = input(
                    "Enter Env file path (optional, press Enter to skip): "
                ).strip()
                if env_file_input:
                    env_file = env_file_input

            context = {
                "branch_name": branch,
                "python_version": python_version,
                "run_linting": run_linting,
                "run_tests": run_tests,
                "setup_monitoring": setup_monitoring,
                "deployment_type": deployment_type,
                "docker_compose_file": docker_compose_file,
                "env_file": env_file,
                "deploy_command": deploy_command,
            }

            # Use new generator API
            generator = PipelineGenerator(
                platform=args.platform,
                strategy=strategy,
                enable_monitoring=setup_monitoring,
            )
            generator.set_options(
                run_linting=run_linting,
                run_tests=run_tests,
                python_version=python_version,
                branch=branch,
            )
            output = generator.generate()

            # Save to file
            output_path = generator.save()
            print(f"✅ Deployment pipeline generated: {output_path}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
