import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="VM Tool: Setup, Provision, and Manage VMs"
    )
    parser.add_argument("--version", action="version", version="1.0.30")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

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

    args = parser.parse_args()

    if args.command == "setup-k8s":
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
            from vm_tool.runner import SetupRunner, SetupRunnerConfig

            # For deployment, we might need github creds if the playbook pulls code
            # But for now we use dummy or env vars
            config = SetupRunnerConfig(github_project_url="dummy")
            runner = SetupRunner(config)
            runner.run_docker_deploy(
                compose_file=args.compose_file,
                inventory_file=args.inventory,
                host=args.host,
                user=args.user,
                env_file=args.env_file,
                deploy_command=args.deploy_command,
            )
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
