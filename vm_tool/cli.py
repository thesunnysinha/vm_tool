import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="VM Tool: Setup, Provision, and Manage VMs"
    )
    parser.add_argument("--version", action="version", version="1.0.30")

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

    # K8s Setup command
    k8s_parser = subparsers.add_parser(
        "setup-k8s", help="Install K3s Kubernetes cluster"
    )
    k8s_parser.add_argument(
        "--inventory", type=str, default="inventory.yml", help="Inventory file to use"
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
                input(
                    "Deployment Type (docker/custom) [docker] (kubernetes coming soon): "
                )
                .strip()
                .lower()
            )
            deployment_type = "docker"
            if dep_type_input in ("custom", "c"):
                deployment_type = "custom"
            elif dep_type_input in ("kubernetes", "k8s", "k"):
                deployment_type = "kubernetes"

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

            generator = PipelineGenerator()
            generator.generate(platform=args.platform, context=context)
            print(f"✅ Deployment pipeline generated for branch '{branch}'.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
