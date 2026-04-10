"""Handlers for ops subcommands: history, rollback, drift-check, backup."""
import sys

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def handle_history(args) -> None:
    from vm_tool.core.history import DeploymentHistory

    history = DeploymentHistory()
    deployments = history.get_history(host=args.host, limit=args.limit)

    if not deployments:
        console.print("[yellow]No deployment history found[/yellow]")
        return

    table = Table(
        title=f"Deployment History{' — ' + args.host if args.host else ''}",
        box=box.ROUNDED,
        show_header=True,
    )
    table.add_column("ID", style="dim")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Host", style="magenta")
    table.add_column("Service")
    table.add_column("Status", justify="center")
    table.add_column("Git", style="dim")

    for dep in deployments:
        status = dep.get("status", "unknown")
        status_cell = "[green]✅ success[/green]" if status == "success" else "[red]❌ failed[/red]"
        git = dep.get("git_commit", "")[:8] if dep.get("git_commit") else "—"
        table.add_row(
            dep["id"],
            dep["timestamp"],
            dep["host"],
            dep.get("service_name", "default"),
            status_cell,
            git,
        )

    console.print(table)


def handle_rollback(args) -> None:
    from vm_tool.core.history import DeploymentHistory
    from vm_tool.core.runner import SetupRunner, SetupRunnerConfig

    history = DeploymentHistory()
    rollback_info = history.get_rollback_info(args.host, args.to)

    if not rollback_info:
        console.print("[red]❌ No deployment found to rollback to[/red]")
        sys.exit(1)

    console.print(f"\n[cyan]🔄 Rolling back to deployment:[/cyan] [bold]{rollback_info['id']}[/bold]")
    console.print(f"   Timestamp : {rollback_info['timestamp']}")
    console.print(f"   Compose   : {rollback_info['compose_file']}")
    if rollback_info.get("git_commit"):
        console.print(f"   Git commit: {rollback_info['git_commit'][:8]}")

    confirm = console.input("\n[bold yellow]Proceed with rollback? (yes/no):[/bold yellow] ").strip().lower()
    if confirm != "yes":
        console.print("[red]❌ Rollback cancelled[/red]")
        sys.exit(0)

    try:
        runner = SetupRunner(SetupRunnerConfig())
        runner.run_docker_deploy(
            compose_file=rollback_info["compose_file"],
            inventory_file=args.inventory,
            host=args.host,
            user=None,
            force=True,
        )
        console.print("\n[green]✅ Rollback completed successfully[/green]")
    except Exception as e:
        console.print(f"\n[red]❌ Rollback failed:[/red] {e}")
        sys.exit(1)


def handle_drift(args) -> None:
    from vm_tool.deploy.drift import DriftDetector

    detector = DriftDetector()

    with console.status(f"[cyan]Checking drift on {args.host}...[/cyan]"):
        drifts = detector.check_drift(args.host, args.user)

    if not drifts:
        console.print(f"[green]✅ No drift detected on {args.host}[/green]")
        return

    table = Table(
        title=f"Drift Detected — {args.host}",
        box=box.ROUNDED,
        show_header=True,
    )
    table.add_column("File", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Expected", style="dim")
    table.add_column("Actual", style="dim")

    for drift in drifts:
        status_cell = "[yellow]modified[/yellow]" if drift["status"] == "modified" else "[red]deleted[/red]"
        actual = drift["actual"][:16] + "..." if drift["actual"] else "[red]missing[/red]"
        table.add_row(
            drift["file"],
            status_cell,
            drift["expected"][:16] + "...",
            actual,
        )

    console.print(table)
    console.print(f"[bold red]Found {len(drifts)} file(s) with drift[/bold red]")
    sys.exit(1)


def handle_backup(args) -> None:
    from vm_tool.deploy.backup import BackupManager

    manager = BackupManager()

    if args.backup_command == "create":
        try:
            with console.status(f"[cyan]Creating backup on {args.host}...[/cyan]"):
                backup_id = manager.create_backup(
                    host=args.host, user=args.user, paths=args.paths
                )
            console.print(f"[green]✅ Backup created:[/green] {backup_id}")
        except Exception as e:
            console.print(f"[red]❌ Backup failed:[/red] {e}")
            sys.exit(1)

    elif args.backup_command == "list":
        backups = manager.list_backups(host=args.host)
        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            return

        table = Table(title="Available Backups", box=box.ROUNDED)
        table.add_column("ID", style="dim")
        table.add_column("Host", style="magenta")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Paths")

        for backup in backups:
            size_mb = backup["size"] / (1024 * 1024)
            table.add_row(
                backup["id"],
                backup["host"],
                backup["timestamp"],
                f"{size_mb:.2f} MB",
                ", ".join(backup["paths"]),
            )

        console.print(table)

    elif args.backup_command == "restore":
        try:
            with console.status(f"[cyan]Restoring backup {args.id}...[/cyan]"):
                manager.restore_backup(args.id, args.host, args.user)
            console.print(f"[green]✅ Backup restored:[/green] {args.id}")
        except Exception as e:
            console.print(f"[red]❌ Restore failed:[/red] {e}")
            sys.exit(1)


def handle_doctor(args) -> None:
    import shutil
    import subprocess

    from rich.table import Table
    from rich import box

    checks = []

    def _check(name: str, fn):
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, str(e)
        checks.append((name, ok, detail))

    def _cmd_version(cmd, *args_):
        path = shutil.which(cmd)
        if not path:
            return False, f"{cmd} not found in PATH"
        result = subprocess.run([cmd] + list(args_), capture_output=True, text=True, timeout=5)
        version = (result.stdout or result.stderr).strip().splitlines()[0]
        return True, version

    _check("Python ≥ 3.9", lambda: (True, f"{__import__('sys').version.split()[0]}"))
    _check("ansible", lambda: _cmd_version("ansible", "--version"))
    _check("ansible-runner", lambda: (bool(shutil.which("ansible-runner")), shutil.which("ansible-runner") or "not found"))
    _check("docker", lambda: _cmd_version("docker", "--version"))
    _check("docker compose", lambda: _cmd_version("docker", "compose", "version"))
    _check("kubectl", lambda: _cmd_version("kubectl", "version", "--client", "--short"))
    _check("helm", lambda: _cmd_version("helm", "version", "--short"))
    _check("ssh", lambda: _cmd_version("ssh", "-V"))
    _check("git", lambda: _cmd_version("git", "--version"))

    def _check_ssh_key():
        import os
        key_paths = [
            os.path.expanduser("~/.ssh/id_ed25519"),
            os.path.expanduser("~/.ssh/id_rsa"),
            os.path.expanduser("~/.ssh/id_ecdsa"),
        ]
        for p in key_paths:
            if os.path.exists(p):
                return True, p
        return False, "No default SSH key found in ~/.ssh/"

    _check("SSH key", _check_ssh_key)

    def _check_python_pkg(pkg):
        try:
            __import__(pkg)
            version = getattr(__import__(pkg), "__version__", "installed")
            return True, version
        except ImportError:
            return False, f"{pkg} not installed"

    _check("ansible_runner (py)", lambda: _check_python_pkg("ansible_runner"))
    _check("paramiko (py)", lambda: _check_python_pkg("paramiko"))
    _check("rich (py)", lambda: _check_python_pkg("rich"))
    _check("tenacity (py)", lambda: _check_python_pkg("tenacity"))

    table = Table(title="vm_tool Doctor Report", box=box.ROUNDED, show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Detail", style="dim")

    failed = 0
    for name, ok, detail in checks:
        status = "[green]OK[/green]" if ok else "[red]MISSING[/red]"
        if not ok:
            failed += 1
        table.add_row(name, status, detail)

    console.print(table)
    if failed == 0:
        console.print("[green]✅ All checks passed — vm_tool is ready to use.[/green]")
    else:
        console.print(f"[yellow]⚠️  {failed} check(s) failed. Install missing tools to enable full functionality.[/yellow]")


def handle_status(args) -> None:
    from vm_tool.core.state import DeploymentState
    from rich.table import Table
    from rich import box

    state = DeploymentState()
    # _load_state returns {host: {service: {compose_file, status, deployed_at, ...}}}
    all_states = state._load_state()

    if getattr(args, "host", None):
        all_states = {k: v for k, v in all_states.items() if args.host in k}

    if not all_states:
        label = f" for {args.host}" if getattr(args, "host", None) else ""
        console.print(f"[yellow]No deployment state found{label}[/yellow]")
        return

    table = Table(title="Deployment State", box=box.ROUNDED, show_header=True)
    table.add_column("Host", style="magenta")
    table.add_column("Service", style="cyan")
    table.add_column("Compose File", style="dim")
    table.add_column("Last Deployed", style="dim")
    table.add_column("Status", justify="center")

    for host, services in all_states.items():
        if not isinstance(services, dict):
            continue
        first = True
        for service_name, entry in services.items():
            status = entry.get("status", "unknown")
            status_cell = "[green]deployed[/green]" if status == "deployed" else "[red]failed[/red]"
            table.add_row(
                host if first else "",
                service_name,
                entry.get("compose_file", "—"),
                entry.get("deployed_at", "—"),
                status_cell,
            )
            first = False

    console.print(table)
