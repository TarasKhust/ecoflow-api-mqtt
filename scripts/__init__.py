"""EcoFlow API Linting Scripts Module."""

import argparse
import subprocess
import sys


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔍 {description}...")
    try:
        subprocess.run(cmd, check=True, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        return False


def lint() -> bool:
    """Run ruff linting."""
    return run_command(
        ["python", "-m", "ruff", "check", "custom_components/", "--no-fix"],
        "Running ruff linting",
    )


def format_code() -> bool:
    """Format code with ruff."""
    return run_command(
        ["python", "-m", "ruff", "format", "custom_components/"], "Formatting code with ruff"
    )


def check() -> bool:
    """Run all checks."""
    print("🔍 Running comprehensive checks...")

    if not lint():
        return False

    if not run_command(
        ["python", "-m", "ruff", "format", "custom_components/", "--check"],
        "Checking format",
    ):
        return False

    print("✅ All checks passed!")
    return True


def fix() -> bool:
    """Fix auto-fixable issues."""
    print("🔧 Fixing auto-fixable issues...")

    if not run_command(
        ["python", "-m", "ruff", "check", "custom_components/", "--fix"],
        "Running ruff fix",
    ):
        return False

    if not format_code():
        return False

    print("✅ All issues fixed!")
    return True


def type_check() -> bool:
    """Run mypy type checking."""
    return run_command(["python", "-m", "mypy", "custom_components/"], "Running mypy type checking")


def security() -> bool:
    """Run bandit security check."""
    return run_command(["python", "-m", "bandit", "-r", "custom_components/"], "Running bandit security check")


def install() -> bool:
    """Install linting dependencies."""
    print("📦 Installing linting dependencies...")

    if not run_command(
        ["python", "-m", "pip", "install", "--upgrade", "pip"],
        "Updating pip",
    ):
        return False

    if not run_command(
        ["python", "-m", "pip", "install", "-r", "requirements-lint.txt"],
        "Installing linting dependencies",
    ):
        return False

    if not run_command(
        ["python", "-m", "pre_commit", "install"],
        "Installing pre-commit hooks",
    ):
        return False

    print("✅ Installation complete!")
    return True


def all_checks() -> bool:
    """Run all linting tools."""
    print("🚀 Running all linting tools...")

    # Format check
    print("\n📝 1. Formatting check...")
    if not run_command(
        ["python", "-m", "ruff", "format", "custom_components/", "--check"],
        "Format check",
    ):
        print("❌ Format check failed")
        return False

    # Linting
    print("\n🔍 2. Linting...")
    if not lint():
        print("❌ Linting failed")
        return False

    # Type checking
    print("\n🔍 3. Type checking...")
    if not type_check():
        print("❌ Type checking failed")
        return False

    # Security check
    print("\n🔒 4. Security check...")
    if not security():
        print("❌ Security check failed")
        return False

    print("\n✅ All checks passed!")
    return True


def main() -> None:
    """Main entry point for scripts."""
    parser = argparse.ArgumentParser(
        description="EcoFlow API Linting Scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  lint        - Run ruff linting (check only)
  format      - Format code with ruff
  check       - Run all checks (lint + format check)
  fix         - Fix auto-fixable issues
  type-check  - Run mypy type checking
  security    - Run bandit security check
  all         - Run all linting tools
  install     - Install linting dependencies

Usage examples:
  python -m scripts lint
  python -m scripts fix
  python -m scripts all
        """,
    )

    parser.add_argument(
        "command",
        choices=["lint", "format", "check", "fix", "type-check", "security", "all", "install"],
        help="Command to run",
    )

    args = parser.parse_args()

    # Map commands to functions
    commands = {
        "lint": lint,
        "format": format_code,
        "check": check,
        "fix": fix,
        "type-check": type_check,
        "security": security,
        "all": all_checks,
        "install": install,
    }

    # Execute the command
    success = commands[args.command]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
