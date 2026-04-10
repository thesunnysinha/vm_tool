#!/usr/bin/env python3
"""Cross-platform build, test, and publish script for vm_tool.

Usage:
    python run.py clean          - Remove build artifacts
    python run.py build          - Build the package
    python run.py upload         - Build and publish to PyPI
    python run.py install        - Install dev dependencies
    python run.py test           - Run the test suite
    python run.py lint           - Run flake8 + black check
    python run.py push           - Commit, bump version, and push to GitHub
    python run.py push --branch  - Push to a feature branch (no version bump)
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
VENV = ROOT / "venv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _python():
    """Return path to the venv Python (creates venv if missing)."""
    exe = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not exe.exists():
        _ensure_venv()
    return str(exe)


def _run(cmd: str | list, *, check=True, cwd=ROOT):
    """Run a command, streaming output. Accepts a string (shell) or list."""
    use_shell = isinstance(cmd, str)
    result = subprocess.run(cmd, shell=use_shell, cwd=cwd, check=check)
    return result


def _run_silent(cmd: str | list, *, check=True, cwd=ROOT):
    """Run a command, capturing output. Returns CompletedProcess."""
    use_shell = isinstance(cmd, str)
    result = subprocess.run(cmd, shell=use_shell, cwd=cwd, check=check,
                            capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result


def _poetry(*args):
    """Run poetry with the given arguments."""
    _run(["poetry"] + list(args))


def _banner(msg: str):
    print("\n" + "=" * 60)
    print(f"  {msg}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Venv helpers (for version bumping)
# ---------------------------------------------------------------------------

def _ensure_venv():
    if not VENV.exists():
        _banner("Creating virtual environment...")
        _run([sys.executable, "-m", "venv", str(VENV)])
    python = _python()
    result = _run_silent([python, "-m", "pip", "show", "bump-my-version"], check=False)
    if result.returncode != 0:
        _banner("Installing bump-my-version...")
        _run([python, "-m", "pip", "install", "--upgrade", "pip"])
        _run([python, "-m", "pip", "install", "bump-my-version"])


def _bump_version():
    """Bump patch version via bump-my-version and return (old, new)."""
    _ensure_venv()
    old = _get_version()
    bump_exe = VENV / ("Scripts/bump-my-version.exe" if os.name == "nt" else "bin/bump-my-version")
    _run([str(bump_exe), "bump", "patch", "--allow-dirty", "--verbose"])
    new = _get_version()
    return old, new


def _get_version() -> str:
    try:
        with open(ROOT / "pyproject.toml") as f:
            for line in f:
                if line.strip().startswith("version ="):
                    return line.split("=", 1)[1].strip().strip('"\'')
    except Exception:
        pass
    return "unknown"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_clean():
    """Remove build artifacts."""
    _banner("Cleaning build artifacts...")
    for target in ["dist", "build"]:
        p = ROOT / target
        if p.exists():
            shutil.rmtree(p)
            print(f"  Removed {target}/")
    for egg in ROOT.glob("*.egg-info"):
        shutil.rmtree(egg)
        print(f"  Removed {egg.name}/")
    print("✅ Clean complete.")


def cmd_build():
    """Build source and wheel distributions."""
    cmd_clean()
    _banner("Building package...")
    _poetry("build")
    print("✅ Build complete.")


def cmd_upload():
    """Build and publish to PyPI."""
    cmd_build()
    _banner("Publishing to PyPI...")
    _poetry("publish")
    print("✅ Published.")


def cmd_install():
    """Install dev dependencies."""
    _banner("Installing dependencies...")
    _poetry("install", "--with", "dev")
    print("✅ Dependencies installed.")


def cmd_test():
    """Run the test suite."""
    _banner("Running tests...")
    _poetry("run", "pytest")


def cmd_lint():
    """Run flake8 and black check."""
    _banner("Running linters...")
    _poetry("run", "flake8", "vm_tool")
    _poetry("run", "black", "--check", "vm_tool")
    print("✅ Lint passed.")


# ---------------------------------------------------------------------------
# Git / GitHub push
# ---------------------------------------------------------------------------

def _git(*args, check=True):
    return _run_silent(["git"] + list(args), check=check)


def _current_branch() -> str:
    r = _git("rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip()


def _branch_exists(name: str) -> bool:
    r = _git("rev-parse", "--verify", name, check=False)
    return r.returncode == 0


def cmd_push(branch: str | None = None, message: str | None = None):
    """Commit changes, bump version (main only), and push to GitHub."""
    if branch is None:
        branch = input("Enter the branch name (or press Enter for current): ").strip()
        if not branch:
            branch = _current_branch()

    is_main = branch.lower() in ("main", "master")

    # Switch / create branch
    current = _current_branch()
    if branch != current:
        if _branch_exists(branch):
            _git("checkout", branch)
        else:
            _git("checkout", "-b", branch)
        print(f"  Switched to branch: {branch}")

    # Stage all changes
    _git("add", ".")

    if message is None:
        message = input("Enter commit message: ").strip()
        if not message:
            message = f"chore: update ({_get_version()})"

    # Commit (allow empty so the script never crashes on clean trees)
    r = _git("commit", "-m", message, check=False)
    if r.returncode != 0 and "nothing to commit" not in r.stdout + r.stderr:
        print(f"❌ Commit failed:\n{r.stderr}")
        sys.exit(1)

    if is_main:
        old, new = _bump_version()
        _banner(f"Version bumped: {old} → {new}")

        _git("push", "origin", "main")
        _git("push", "origin", "--tags")
        _git("pull", "origin", "main")
        print(f"✅ Pushed to main with version bump ({old} → {new})")
    else:
        _git("push", "origin", branch)
        print(f"✅ Pushed to {branch}")

        if _current_branch() != "main" and _branch_exists("main"):
            _git("checkout", "main")
            print("  Switched back to main")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMMANDS = {
    "clean": cmd_clean,
    "build": cmd_build,
    "upload": cmd_upload,
    "install": cmd_install,
    "test": cmd_test,
    "lint": cmd_lint,
}


def main():
    parser = argparse.ArgumentParser(
        description="Cross-platform build / CI / publish script for vm_tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "command",
        choices=list(COMMANDS) + ["push"],
        help="Task to run",
    )
    parser.add_argument("--branch", "-b", default=None, help="Branch name (push command)")
    parser.add_argument("--message", "-m", default=None, help="Commit message (push command)")
    args = parser.parse_args()

    if args.command == "push":
        cmd_push(branch=args.branch, message=args.message)
    else:
        COMMANDS[args.command]()


if __name__ == "__main__":
    main()
