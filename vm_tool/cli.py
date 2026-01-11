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

    elif args.command == "generate-pipeline":
        try:
            from vm_tool.generator import PipelineGenerator

            generator = PipelineGenerator()
            generator.generate(platform=args.platform)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
