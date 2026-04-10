"""Handlers for 'config' subcommands."""
import sys

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def handle_config(args, config_parser) -> None:
    from vm_tool.config.config import Config

    config = Config()

    if args.config_command == "set":
        config.set(args.key, args.value)
        console.print(f"[green]✅ Set[/green] {args.key} = {args.value}")

    elif args.config_command == "get":
        value = config.get(args.key)
        if value is not None:
            console.print(f"[cyan]{args.key}[/cyan] = {value}")
        else:
            console.print(f"[red]❌ Config key '{args.key}' not found[/red]")
            sys.exit(1)

    elif args.config_command == "unset":
        config.unset(args.key)
        console.print(f"[green]✅ Unset[/green] {args.key}")

    elif args.config_command == "list":
        all_config = config.list_all()
        if all_config:
            table = Table(title="Configuration", box=box.ROUNDED)
            table.add_column("Key", style="cyan")
            table.add_column("Value")
            for key, value in all_config.items():
                table.add_row(key, str(value))
            console.print(table)
        else:
            console.print("[yellow]No configuration set[/yellow]")

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
        console.print(f"[green]✅ Created profile[/green] '{args.name}' [dim](environment: {args.environment})[/dim]")

    elif args.config_command == "list-profiles":
        profiles = config.list_profiles()
        if profiles:
            table = Table(title="Profiles", box=box.ROUNDED)
            table.add_column("Profile", style="cyan")
            table.add_column("Key", style="magenta")
            table.add_column("Value")
            for name, data in profiles.items():
                first = True
                for key, value in data.items():
                    table.add_row(name if first else "", key, str(value))
                    first = False
            console.print(table)
        else:
            console.print("[yellow]No profiles configured[/yellow]")

    elif args.config_command == "delete-profile":
        config.delete_profile(args.name)
        console.print(f"[green]✅ Deleted profile[/green] '{args.name}'")

    else:
        config_parser.print_help()
