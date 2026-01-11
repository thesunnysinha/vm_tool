import argparse
import sys
from vm_tool.provision import Provisioner


def main():
    parser = argparse.ArgumentParser(
        description="VM Tool: Setup, Provision, and Manage VMs"
    )
    parser.add_argument("--version", action="version", version="1.0.30")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Provision command
    provision_parser = subparsers.add_parser(
        "provision", help="Provision infrastructure using Terraform"
    )
    provision_parser.add_argument(
        "--provider", type=str, required=True, help="Cloud provider (e.g., aws)"
    )
    provision_parser.add_argument(
        "--action",
        type=str,
        choices=["apply", "destroy"],
        default="apply",
        help="Action to perform",
    )
    provision_parser.add_argument(
        "--vars", type=str, nargs="*", help="Terraform variables (key=value)"
    )

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

    if args.command == "provision":
        try:
            provisioner = Provisioner(args.provider)
            provisioner.init()

            tf_vars = {}
            if args.vars:
                for v in args.vars:
                    key, value = v.split("=")
                    tf_vars[key] = value

            if args.action == "apply":
                provisioner.apply(vars=tf_vars)
            elif args.action == "destroy":
                provisioner.destroy(vars=tf_vars)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

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
                input("Deployment Type (kubernetes/docker) [docker]: ").strip().lower()
            )
            deployment_type = (
                "kubernetes"
                if dep_type_input in ("kubernetes", "k8s", "k")
                else "docker"
            )

            docker_compose_file = "docker-compose.yml"
            if deployment_type == "docker":
                docker_compose_file = (
                    input(
                        "Enter Docker Compose file name [docker-compose.yml]: "
                    ).strip()
                    or "docker-compose.yml"
                )

            context = {
                "branch_name": branch,
                "python_version": python_version,
                "run_linting": run_linting,
                "run_tests": run_tests,
                "setup_monitoring": setup_monitoring,
                "deployment_type": deployment_type,
                "docker_compose_file": docker_compose_file,
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
