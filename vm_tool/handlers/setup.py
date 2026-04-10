"""Handlers for setup subcommands."""
import sys

from rich.console import Console

console = Console()


def handle_setup(args) -> None:
    from vm_tool.core.runner import SetupRunner, SetupRunnerConfig

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
    with console.status("[cyan]Running VM setup...[/cyan]"):
        runner.run_setup()
    console.print("[green]✅ VM setup complete![/green]")


def handle_cloud_setup(args) -> None:
    import json
    from vm_tool.core.runner import SetupRunner, SetupRunnerConfig, SSHConfig

    config = SetupRunnerConfig(
        github_username=args.github_username,
        github_token=args.github_token,
        github_project_url=args.github_project_url,
        github_branch=args.github_branch,
        docker_compose_file_path=args.docker_compose_file_path,
    )
    runner = SetupRunner(config)

    with open(args.ssh_configs, "r") as f:
        ssh_data = json.load(f)

    ssh_configs = [SSHConfig(**cfg) for cfg in ssh_data]
    with console.status(f"[cyan]Running cloud setup for {len(ssh_configs)} host(s)...[/cyan]"):
        runner.run_cloud_setup(ssh_configs)
    console.print("[green]✅ Cloud setup complete![/green]")


def handle_k8s_setup(args) -> None:
    from vm_tool.core.runner import SetupRunner, SetupRunnerConfig

    try:
        runner = SetupRunner(SetupRunnerConfig())
        with console.status("[cyan]Running Kubernetes setup...[/cyan]"):
            runner.run_k8s_setup(inventory_file=args.inventory)
        console.print("[green]✅ Kubernetes setup complete![/green]")
    except Exception as e:
        console.print(f"[red]❌ K8s setup failed:[/red] {e}")
        sys.exit(1)


def handle_monitoring_setup(args) -> None:
    from vm_tool.core.runner import SetupRunner, SetupRunnerConfig

    try:
        runner = SetupRunner(SetupRunnerConfig())
        with console.status("[cyan]Deploying monitoring stack (Prometheus + Grafana)...[/cyan]"):
            runner.run_monitoring_setup(inventory_file=args.inventory)
        console.print("[green]✅ Monitoring setup complete![/green]")
    except Exception as e:
        console.print(f"[red]❌ Monitoring setup failed:[/red] {e}")
        sys.exit(1)


def handle_ci_setup(args) -> None:
    from vm_tool.core.runner import SetupRunner

    try:
        with console.status("[cyan]Configuring CI environment...[/cyan]"):
            SetupRunner.setup_ci_environment(provider=args.provider)
        console.print("[green]✅ CI environment configured successfully[/green]")
    except Exception as e:
        console.print(f"[red]❌ CI setup failed:[/red] {e}")
        sys.exit(1)
