"""Install pre-commit hooks to repository"""
import sys
import subprocess
import os
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pre_commit_hooks.hook_utils import HookException, TerminalOutput
from pre_commit_hooks.precommit import pre_commit_exception_handler, PreCommitPythonBase

out = TerminalOutput.of()

valid_hooks: list[str] = ["pre-commit", "commit-msg"]


class HookInstaller(PreCommitPythonBase):
    """Install the appropriate hooks"""

    def __init__(self, directory: str ) -> None:
        """
        Initialize the hook installer
        
        Args:
            directory: Path to git directory. If None, uses current directory.
        """
        self.directory = Path(directory) if directory else Path.cwd()
        self.git_dir = self.directory / ".git"
        self.hooks_dir = self.git_dir / "hooks"

        # Validate git directory
        if not self.git_dir.exists():
            raise HookException(
                f"✗ Not a git repository: {self.directory}",
                "Run 'git init' first or specify a valid git repository"
            )

    def _check_pre_commit_installed(self) -> bool:
        """Check if pre-commit is installed in the system"""
        try:
            result = subprocess.run(
                ["pre-commit", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            out.green(f"✓ pre-commit is installed: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _install_pre_commit(self) -> bool:
        """Install pre-commit using pip"""
        out.blue("Installing pre-commit...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pre-commit"],
                check=True,
                capture_output=True
            )
            out.green("✓ pre-commit installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            out.red(f"✗ Failed to install pre-commit: {e.stderr.decode()}")
            return False

    def _check_config_exists(self) -> bool:
        """Check if .pre-commit-config.yaml exists"""
        config_path = self.directory / ".pre-commit-config.yaml"
        if config_path.exists():
            out.green(f"✓ Found .pre-commit-config.yaml at {config_path}")
            return True

        out.yellow(f"⚠ No .pre-commit-config.yaml found at {config_path}")
        return False

    def _install_hooks(self) -> bool:
        """Install pre-commit hooks using pre-commit install"""
        out.blue("Installing pre-commit hooks...")
        original_dir = os.getcwd()
        try:
            # Change to the repository directory
            os.chdir(self.directory)

            # Run pre-commit install
            result = subprocess.run(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
                text=True
            )

            out.green("✓ Pre-commit hooks installed successfully")
            out.blue(result.stdout)

            # Also install commit-msg hook if needed
            subprocess.run(
                ["pre-commit", "install", "--hook-type", "commit-msg"],
                check=False,
                capture_output=True
            )

            os.chdir(original_dir)
            return True
        except subprocess.CalledProcessError as e:
            os.chdir(original_dir)
            out.red(f"✗ Failed to install hooks: {e.stderr}")
            return False
        except Exception as e:
            os.chdir(original_dir)
            raise HookException("✗ Unexpected error: when trying to install hooks"
                        ,str(e)) from e

    @pre_commit_exception_handler
    def run(self) -> int:
        """Run the installation of the hooks"""
        out.blue(f"Installing pre-commit hooks in: {self.directory}")

        # Step 1: Check if pre-commit is installed
        if not self._check_pre_commit_installed():
            out.yellow("⚠ pre-commit not found, installing...")
            if not self._install_pre_commit():
                return 1

        # Step 2: Check if config exists (warning only)
        self._check_config_exists()

        # Step 3: Install the hooks
        if not self._install_hooks():
            return 1

        out.green("✓ All hooks installed successfully!")
        out.blue("You can now commit with pre-commit hooks enabled")
        return 0

    @pre_commit_exception_handler
    def uninstall(self) -> int:
        """Uninstall pre-commit hooks"""
        out.blue("Uninstalling pre-commit hooks...")
        original_dir = os.getcwd()
        try:
            os.chdir(self.directory)

            subprocess.run(
                ["pre-commit", "uninstall"],
                check=True,
                capture_output=True
            )

            subprocess.run(
                ["pre-commit", "uninstall", "--hook-type", "commit-msg"],
                check=False,
                capture_output=True
            )

            os.chdir(original_dir)
            out.green("✓ Pre-commit hooks uninstalled successfully")
            return 0
        except subprocess.CalledProcessError as e:
            os.chdir(original_dir)
            out.red(f"✗ Failed to uninstall hooks: {e.stderr.decode()}")
            return 1


def main() -> int:
    """Main entry point"""
    parser = ArgumentParser(
        description="Install pre-commit hooks to a git repository",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install hooks in current directory
  install-hooks
  
  # Install hooks in specific directory
  install-hooks --directory /path/to/repo
  
  # Uninstall hooks
  install-hooks --uninstall
        """,
    )

    parser.add_argument(
        "--directory",
        default=None,
        help="Path to git directory to install pre-commit hooks (default: current directory)",
    )

    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall pre-commit hooks instead of installing",
    )

    args = parser.parse_args()

    try:
        installer = HookInstaller(args.directory)

        if args.uninstall:
            return installer.uninstall()
        return installer.run()
    except HookException as e:
        out.red(str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
