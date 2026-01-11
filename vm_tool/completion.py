"""CLI auto-completion support for bash, zsh, and fish shells."""

import os
import sys


def generate_bash_completion() -> str:
    """Generate bash completion script."""
    return """# vm_tool bash completion

_vm_tool_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    local commands="config history rollback drift-check backup setup setup-cloud setup-k8s setup-monitoring deploy-docker generate-pipeline --help --version --verbose --debug"
    
    # Config subcommands
    local config_commands="set get unset list create-profile list-profiles delete-profile"
    
    # Backup subcommands
    local backup_commands="create list restore"
    
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
    
    case "${prev}" in
        config)
            COMPREPLY=( $(compgen -W "${config_commands}" -- ${cur}) )
            return 0
            ;;
        backup)
            COMPREPLY=( $(compgen -W "${backup_commands}" -- ${cur}) )
            return 0
            ;;
        --profile)
            # Complete with available profiles
            local profiles=$(vm_tool config list-profiles 2>/dev/null | grep -v "^Available" | awk '{print $1}')
            COMPREPLY=( $(compgen -W "${profiles}" -- ${cur}) )
            return 0
            ;;
        --host|--user|--compose-file)
            # File/path completion
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
    esac
}

complete -F _vm_tool_completion vm_tool
"""


def generate_zsh_completion() -> str:
    """Generate zsh completion script."""
    return """#compdef vm_tool

_vm_tool() {
    local -a commands
    commands=(
        'config:Manage configuration'
        'history:Show deployment history'
        'rollback:Rollback to previous deployment'
        'drift-check:Check for configuration drift'
        'backup:Backup and restore operations'
        'setup:Setup VM with Docker and deploy'
        'setup-cloud:Setup cloud VMs'
        'setup-k8s:Install K3s Kubernetes cluster'
        'setup-monitoring:Install Prometheus and Grafana'
        'deploy-docker:Deploy using Docker Compose'
        'generate-pipeline:Generate CI/CD pipeline configuration'
    )
    
    local -a config_commands
    config_commands=(
        'set:Set a config value'
        'get:Get a config value'
        'unset:Unset a config value'
        'list:List all config values'
        'create-profile:Create a deployment profile'
        'list-profiles:List all profiles'
        'delete-profile:Delete a profile'
    )
    
    local -a backup_commands
    backup_commands=(
        'create:Create a backup'
        'list:List backups'
        'restore:Restore a backup'
    )
    
    _arguments -C \\
        '1: :->command' \\
        '*::arg:->args'
    
    case $state in
        command)
            _describe 'vm_tool commands' commands
            ;;
        args)
            case $words[1] in
                config)
                    _describe 'config commands' config_commands
                    ;;
                backup)
                    _describe 'backup commands' backup_commands
                    ;;
            esac
            ;;
    esac
}

_vm_tool "$@"
"""


def generate_fish_completion() -> str:
    """Generate fish completion script."""
    return """# vm_tool fish completion

# Main commands
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'config' -d 'Manage configuration'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'history' -d 'Show deployment history'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'rollback' -d 'Rollback to previous deployment'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'drift-check' -d 'Check for configuration drift'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'backup' -d 'Backup and restore operations'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'setup' -d 'Setup VM with Docker and deploy'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'setup-cloud' -d 'Setup cloud VMs'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'setup-k8s' -d 'Install K3s Kubernetes cluster'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'setup-monitoring' -d 'Install Prometheus and Grafana'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'deploy-docker' -d 'Deploy using Docker Compose'
complete -c vm_tool -f -n '__fish_use_subcommand' -a 'generate-pipeline' -d 'Generate CI/CD pipeline'

# Config subcommands
complete -c vm_tool -f -n '__fish_seen_subcommand_from config' -a 'set' -d 'Set a config value'
complete -c vm_tool -f -n '__fish_seen_subcommand_from config' -a 'get' -d 'Get a config value'
complete -c vm_tool -f -n '__fish_seen_subcommand_from config' -a 'unset' -d 'Unset a config value'
complete -c vm_tool -f -n '__fish_seen_subcommand_from config' -a 'list' -d 'List all config values'
complete -c vm_tool -f -n '__fish_seen_subcommand_from config' -a 'create-profile' -d 'Create a deployment profile'
complete -c vm_tool -f -n '__fish_seen_subcommand_from config' -a 'list-profiles' -d 'List all profiles'
complete -c vm_tool -f -n '__fish_seen_subcommand_from config' -a 'delete-profile' -d 'Delete a profile'

# Backup subcommands
complete -c vm_tool -f -n '__fish_seen_subcommand_from backup' -a 'create' -d 'Create a backup'
complete -c vm_tool -f -n '__fish_seen_subcommand_from backup' -a 'list' -d 'List backups'
complete -c vm_tool -f -n '__fish_seen_subcommand_from backup' -a 'restore' -d 'Restore a backup'

# Global options
complete -c vm_tool -l help -d 'Show help message'
complete -c vm_tool -l version -d 'Show version'
complete -c vm_tool -s v -l verbose -d 'Enable verbose output'
complete -c vm_tool -s d -l debug -d 'Enable debug logging'
"""


def install_completion(shell: str = "bash") -> str:
    """Install completion script for specified shell."""
    if shell == "bash":
        script = generate_bash_completion()
        path = "/etc/bash_completion.d/vm_tool"
        alt_path = os.path.expanduser("~/.bash_completion.d/vm_tool")
    elif shell == "zsh":
        script = generate_zsh_completion()
        path = "/usr/local/share/zsh/site-functions/_vm_tool"
        alt_path = os.path.expanduser("~/.zsh/completion/_vm_tool")
    elif shell == "fish":
        script = generate_fish_completion()
        path = "/usr/share/fish/vendor_completions.d/vm_tool.fish"
        alt_path = os.path.expanduser("~/.config/fish/completions/vm_tool.fish")
    else:
        raise ValueError(f"Unsupported shell: {shell}")

    # Try system path first, fall back to user path
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(script)
        return path
    except PermissionError:
        os.makedirs(os.path.dirname(alt_path), exist_ok=True)
        with open(alt_path, "w") as f:
            f.write(script)
        return alt_path


def print_completion(shell: str = "bash"):
    """Print completion script to stdout."""
    if shell == "bash":
        print(generate_bash_completion())
    elif shell == "zsh":
        print(generate_zsh_completion())
    elif shell == "fish":
        print(generate_fish_completion())
    else:
        print(f"Error: Unsupported shell: {shell}", file=sys.stderr)
        sys.exit(1)
