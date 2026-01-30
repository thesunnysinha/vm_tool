#!/usr/bin/env python3
"""
Script to automate git commits and pushes with version bumping for main branch.
Automatically manages virtual environment and dependencies.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, check=True, shell=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        sys.exit(1)


def get_venv_path():
    """Get the virtual environment path."""
    return Path(__file__).parent / "venv"


def get_python_executable():
    """Get the Python executable path for the virtual environment."""
    venv_path = get_venv_path()
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        return venv_path / "bin" / "python"


def get_pip_executable():
    """Get the pip executable path for the virtual environment."""
    venv_path = get_venv_path()
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/Mac
        return venv_path / "bin" / "pip"


def create_venv():
    """Create a virtual environment if it doesn't exist."""
    venv_path = get_venv_path()
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        run_command(f'"{sys.executable}" -m venv venv')
        print("✅ Virtual environment created!")
        return True
    return False


def install_dependencies():
    """Install required dependencies in the virtual environment."""
    python_exe = get_python_executable()
    
    print("📦 Installing/updating dependencies...")
    # Use python -m pip instead of direct pip executable (Windows compatibility)
    run_command(f'"{python_exe}" -m pip install --upgrade pip')
    run_command(f'"{python_exe}" -m pip install bump-my-version')
    
    # Install project dependencies if requirements.txt exists
    if Path("requirements.txt").exists():
        run_command(f'"{python_exe}" -m pip install -r requirements.txt')
    
    print("✅ Dependencies installed!")


def setup_environment():
    """Setup virtual environment and dependencies."""
    venv_created = create_venv()
    
    # Always install/update dependencies if venv was just created
    if venv_created:
        install_dependencies()
    else:
        # Check if bump-my-version is available
        python_exe = get_python_executable()
        result = run_command(f'"{python_exe}" -m pip show bump-my-version', check=False)
        if result.returncode != 0:
            print("⚠️  bump-my-version not found, installing dependencies...")
            install_dependencies()


def run_in_venv(cmd):
    """Run a command using the virtual environment's Python."""
    python_exe = get_python_executable()
    
    # For bump-my-version, we need to use the venv's Scripts directory
    venv_path = get_venv_path()
    if os.name == 'nt':
        bump_exe = venv_path / "Scripts" / "bump-my-version.exe"
    else:
        bump_exe = venv_path / "bin" / "bump-my-version"
    
    # Replace bump-my-version command with full path
    if cmd.startswith("bump-my-version"):
        cmd = cmd.replace("bump-my-version", f'"{bump_exe}"')
        # Add verbose flag to show what's happening
        if "--verbose" not in cmd and "-v" not in cmd:
            cmd = cmd.replace("bump patch", "bump patch --verbose")
    
    return run_command(cmd)


def get_current_version():
    """Read the current version from pyproject.toml."""
    try:
        with open("pyproject.toml", "r") as f:
            for line in f:
                if line.strip().startswith("version ="):
                    # Extract version from line like: version = "1.0.34"
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    return version
    except Exception as e:
        print(f"Warning: Could not read current version: {e}")
    return "unknown"


def main():
    # Setup virtual environment
    print("🔧 Setting up environment...")
    setup_environment()
    print()
    
    # Ask for the branch name
    branch_name = input("Enter the branch name: ").strip()
    
    if branch_name == "main":
        # Get current version before bump
        current_version = get_current_version()
        
        # Bump version for main branch
        print("\n" + "="*60)
        print(f"🔢 Bumping version from {current_version}...")
        print("="*60)
        run_in_venv("bump-my-version bump patch --allow-dirty")
        
        # Get new version after bump
        new_version = get_current_version()
        print("\n" + "="*60)
        print(f"✅ Version bumped: {current_version} → {new_version}")
        print("="*60 + "\n")
        
        # Add all changes
        print("Adding changes...")
        run_command("git add .")
        
        # Ask for commit message
        commit_message = input("Enter the commit message: ").strip()
        
        # Commit with the entered message
        print("Committing changes...")
        run_command(f'git commit -m "{commit_message}"')
        
        # Push changes directly to the "main" branch
        print("Pushing to main...")
        run_command("git push origin main")
        
        # Pull latest changes
        print("Pulling latest changes...")
        run_command("git pull origin main")
        
        print("✅ Successfully pushed to main with version bump!")
        
    else:
        # Create and switch to the new branch
        print(f"Creating and switching to branch: {branch_name}")
        run_command(f"git checkout -b {branch_name}")
        
        # Add all changes
        print("Adding changes...")
        run_command("git add .")
        
        # Ask for commit message
        commit_message = input("Enter the commit message: ").strip()
        
        # Commit with the entered message
        print("Committing changes...")
        run_command(f'git commit -m "{commit_message}"')
        
        # Push changes to the specified branch
        print(f"Pushing to {branch_name}...")
        run_command(f"git push origin {branch_name}")
        
        # Switch back to main
        print("Switching back to main...")
        run_command("git checkout main")
        
        print(f"✅ Successfully pushed to {branch_name}!")


if __name__ == "__main__":
    main()
