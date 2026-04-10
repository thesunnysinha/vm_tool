"""Handlers for tool subcommands: hydrate-env, completion, generate-pipeline, prepare-release, secrets."""
import os
import sys

from rich.console import Console

console = Console()


def handle_hydrate_env(args) -> None:
    import json
    from vm_tool.core.runner import SetupRunner, SetupRunnerConfig

    try:
        secrets_map = json.loads(args.secrets)
        runner = SetupRunner(SetupRunnerConfig())

        with console.status("[cyan]Hydrating environment files from secrets...[/cyan]"):
            runner.hydrate_env_from_secrets(
                compose_file=args.compose_file,
                secrets_map=secrets_map,
                project_root=args.project_root,
            )
        console.print("[green]✅ Environment files hydrated successfully[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to hydrate env:[/red] {e}")
        sys.exit(1)


def handle_completion(args) -> None:
    from vm_tool.tools.completion import print_completion, install_completion

    if args.install:
        try:
            path = install_completion(args.shell)
            console.print(f"[green]✅ Completion installed:[/green] {path}")
            console.print("\n[cyan]To activate, run:[/cyan]")
            if args.shell == "bash":
                console.print(f"  source {path}")
            elif args.shell == "zsh":
                console.print(f"  [dim]# Add to ~/.zshrc: fpath=({os.path.dirname(path)} $fpath)[/dim]")
                console.print("  [dim]# Then run: compinit[/dim]")
            elif args.shell == "fish":
                console.print(f"  [dim]# Restart your shell or run: source {path}[/dim]")
        except Exception as e:
            console.print(f"[red]❌ Failed to install completion:[/red] {e}")
            sys.exit(1)
    else:
        print_completion(args.shell)


def handle_prepare_release(args) -> None:
    from vm_tool.tools.release import ReleaseManager

    manager = ReleaseManager(verbose=args.verbose)
    try:
        with console.status("[cyan]Preparing release...[/cyan]"):
            manager.prepare_release(
                base_file=args.base_file,
                prod_file=args.prod_file,
                output_file=args.output,
                strip_volumes=args.strip_volumes,
                fix_paths=args.fix_paths,
            )
        console.print(f"[green]✅ Release file prepared:[/green] {args.output}")
    except Exception as e:
        console.print(f"[red]❌ Release preparation failed:[/red] {e}")
        sys.exit(1)


def handle_generate_pipeline(args) -> None:
    try:
        from vm_tool.tools.generator import PipelineGenerator

        console.print("[cyan]🚀 Configuring your CI/CD Pipeline...[/cyan]")

        branch = console.input("[cyan]Enter the branch to trigger deployment [[main]]:[/cyan] ").strip() or "main"
        python_version = console.input("[cyan]Enter Python version [[3.12]]:[/cyan] ").strip() or "3.12"

        enable_linting = console.input("[cyan]Include Linting step (flake8)? [y/N]:[/cyan] ").strip().lower()
        run_linting = enable_linting in ("y", "yes")

        enable_tests = console.input("[cyan]Include Testing step (pytest)? [y/N]:[/cyan] ").strip().lower()
        run_tests = enable_tests in ("y", "yes")

        enable_monitoring = console.input("[cyan]Include Monitoring (Prometheus/Grafana)? [y/N]:[/cyan] ").strip().lower()
        setup_monitoring = enable_monitoring in ("y", "yes")

        dep_type_input = console.input("[cyan]Deployment Type (docker/registry/custom) [[docker]]:[/cyan] ").strip().lower()
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

        deploy_command = None

        if deployment_type == "custom":
            deploy_command = console.input("[cyan]Enter custom deployment command:[/cyan] ").strip()
        elif deployment_type == "docker":
            docker_compose_file = (
                console.input("[cyan]Enter Docker Compose file name [[docker-compose.yml]]:[/cyan] ").strip()
                or "docker-compose.yml"
            )
            env_file_input = console.input(
                "[cyan]Enter Env file path (optional, press Enter to skip):[/cyan] "
            ).strip()

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
        generator.generate()
        output_path = generator.save()
        console.print(f"[green]✅ Deployment pipeline generated:[/green] {output_path}")
    except Exception as e:
        console.print(f"[red]❌ Pipeline generation failed:[/red] {e}")
        sys.exit(1)


def handle_secrets(args) -> None:
    if args.secrets_command == "sync":
        from vm_tool.security.secrets import SecretsManager

        if not os.path.exists(args.env_file):
            console.print(f"[red]❌ Env file not found:[/red] {args.env_file}")
            sys.exit(1)

        try:
            manager = SecretsManager.from_github(repo=args.repo)

            console.print(f"[cyan]Reading secrets from[/cyan] {args.env_file}...")
            try:
                from dotenv import dotenv_values
                secrets_to_sync = dict(dotenv_values(args.env_file))
            except ImportError:
                # Fallback manual parser
                secrets_to_sync = {}
                with open(args.env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            secrets_to_sync[key.strip()] = value.strip().strip("'").strip('"')

            if not secrets_to_sync:
                console.print("[yellow]⚠️  No secrets found to sync.[/yellow]")
                sys.exit(0)

            console.print(f"[cyan]Found {len(secrets_to_sync)} secrets to sync to GitHub[/cyan]")
            confirm = console.input(
                f"[bold yellow]Proceed to upload {len(secrets_to_sync)} secrets? (yes/no):[/bold yellow] "
            ).strip().lower()
            if confirm != "yes":
                console.print("[red]❌ Operation cancelled.[/red]")
                sys.exit(0)

            success_count = 0
            with console.status("[cyan]Uploading secrets...[/cyan]"):
                for key, value in secrets_to_sync.items():
                    if manager.set(key, value):
                        success_count += 1

            console.print(f"[green]✅ Successfully synced {success_count}/{len(secrets_to_sync)} secrets![/green]")

        except Exception as e:
            console.print(f"[red]❌ Error syncing secrets:[/red] {e}")
            sys.exit(1)
