"""Handlers for deploy subcommands."""
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def handle_docker_deploy(args) -> None:
    import os
    from vm_tool.core.runner import SetupRunner, SetupRunnerConfig

    try:
        profile_data = {}
        if args.profile:
            from vm_tool.config.config import Config
            config = Config()
            profile_data = config.get_profile(args.profile) or {}
            if not profile_data:
                console.print(f"[red]❌ Profile '{args.profile}' not found[/red]")
                sys.exit(1)
            console.print(f"[cyan]📋 Using profile:[/cyan] {args.profile}")

            if profile_data.get("environment") == "production":
                if not args.force:
                    confirm = console.input(
                        "[bold yellow]⚠️  You are deploying to PRODUCTION. Type 'yes' to confirm:[/bold yellow] "
                    ).strip().lower()
                    if confirm != "yes":
                        console.print("[red]❌ Deployment cancelled[/red]")
                        sys.exit(0)

        host = args.host or profile_data.get("host")
        user = args.user or profile_data.get("user")
        compose_file = args.compose_file or profile_data.get("compose_file", "docker-compose.yml")

        project_dir = args.project_dir
        if not project_dir:
            project_dir = f"~/apps/{args.repo_name}" if args.repo_name else "~/app"

        if args.dry_run:
            rows = [
                ("Target Host", host or "from inventory"),
                ("SSH User", user or "from inventory"),
                ("Compose File", compose_file),
                ("Project Dir", project_dir),
                ("Inventory", str(args.inventory)),
            ]
            if args.env_file:
                rows.append(("Env File", args.env_file))
            if args.deploy_command:
                rows.append(("Custom Command", args.deploy_command))

            table = Table(title="Deployment Plan (DRY RUN)", box=box.ROUNDED)
            table.add_column("Setting", style="cyan")
            table.add_column("Value")
            for k, v in rows:
                table.add_row(k, v)
            console.print(table)

            if os.path.exists(compose_file):
                console.print(f"\n[dim]Compose file: {compose_file}[/dim]")
            else:
                console.print(f"\n[yellow]⚠️  Compose file not found: {compose_file}[/yellow]")

            console.print("\n[green]✅ Dry-run complete. Use without --dry-run to deploy.[/green]")
            sys.exit(0)

        runner = SetupRunner(SetupRunnerConfig())
        with console.status(f"[cyan]Deploying to {host or 'inventory hosts'}...[/cyan]"):
            runner.run_docker_deploy(
                compose_file=compose_file,
                inventory_file=args.inventory,
                host=host,
                user=user,
                env_file=args.env_file,
                deploy_command=args.deploy_command,
                force=args.force,
                project_dir=project_dir,
            )

        if host and (args.health_check or args.health_port or args.health_url):
            from vm_tool.deploy.health import SmokeTestSuite

            console.print(f"\n[cyan]🏥 Running health checks (timeout: {args.health_timeout}s)...[/cyan]")
            suite = SmokeTestSuite(host, timeout=args.health_timeout)

            if args.health_port:
                suite.add_port_check(args.health_port)
            if args.health_url:
                suite.add_http_check(args.health_url)
            if args.health_check:
                suite.add_custom_check(args.health_check, "Custom Health Check")

            if not suite.run_all():
                console.print("\n[red]❌ Health checks failed[/red]")
                sys.exit(1)

        console.print(f"\n[green]✅ Deployment to {host or 'all hosts'} complete![/green]")

    except Exception as e:
        console.print(f"[red]❌ Deployment failed:[/red] {e}")
        sys.exit(1)


def handle_k8s_deploy(args) -> None:
    from vm_tool.core.runner import SetupRunner, SetupRunnerConfig

    try:
        if args.dry_run:
            table = Table(title="Kubernetes Deployment Plan (DRY RUN)", box=box.ROUNDED)
            table.add_column("Setting", style="cyan")
            table.add_column("Value")
            table.add_row("Method", args.method)
            table.add_row("Namespace", args.namespace)
            if args.method == "manifest":
                table.add_row("Manifest", str(args.manifest))
            else:
                table.add_row("Helm Chart", str(args.helm_chart))
                table.add_row("Release", str(args.helm_release))
                if args.helm_values:
                    table.add_row("Values File", args.helm_values)
            if args.kubeconfig:
                table.add_row("Kubeconfig", args.kubeconfig)
            if args.host:
                table.add_row("Target Host", args.host)
            table.add_row("Timeout", f"{args.timeout}s")
            console.print(table)

        runner = SetupRunner(SetupRunnerConfig())
        with console.status(f"[cyan]Deploying to Kubernetes namespace '{args.namespace}'...[/cyan]"):
            runner.run_k8s_deploy(
                deploy_method=args.method,
                namespace=args.namespace,
                manifest=args.manifest,
                helm_chart=args.helm_chart,
                helm_release=args.helm_release,
                helm_values=args.helm_values,
                kubeconfig=args.kubeconfig,
                kubeconfig_b64=args.kubeconfig_b64,
                inventory_file=args.inventory,
                host=args.host,
                user=args.user,
                timeout=args.timeout,
                dry_run=args.dry_run,
                force=args.force,
                image_substitutions=args.images,
                k8s_secrets=args.k8s_secrets,
                registry_secrets=args.registry_secrets,
            )

        if not args.dry_run:
            console.print(f"\n[green]✅ Kubernetes deployment to '{args.namespace}' complete![/green]")

    except Exception as e:
        console.print(f"[red]❌ Kubernetes deployment failed:[/red] {e}")
        sys.exit(1)
