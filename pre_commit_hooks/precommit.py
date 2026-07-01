"""Base module for precommit modules"""
import sys
import subprocess
import venv
from pathlib import Path

from typing import Sequence

from pre_commit_hooks.hook_utils import HookException, TerminalOutput

out = TerminalOutput.of()

def pre_commit_exception_handler(func):
    '''Decorator wraps run functions with a try catch'''
    def wrapper(*args,**kwargs) -> int:
        try:
            return func(*args,**kwargs)
        except KeyboardInterrupt:
            out.yellow("✗ Interrupted by user")
            return 1
        except Exception as e:
            raise HookException("✗ Unexpected error: ","") from e
    return wrapper

class PreCommitPythonBase(): #pylint: disable=too-few-public-methods
    """ Base class for precommit hooks for python"""
    venv_path: Path

    def _get_pip_path(self) -> Path:
        """Get path to pip executable in venv"""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / "pip.exe"
        return self.venv_path / "bin" / "pip"

    def _get_python_path(self) -> Path:
        """Get path to python executable in venv"""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / "python.exe"
        return self.venv_path / "bin" / "python"

    def _setup_venv(self) -> bool:
        """Create or validate virtual environment"""
        if self.venv_path.exists():
            out.green(f"✓ Virtual environment found at {self.venv_path}")
            return True

        out.blue(f"Creating virtual environment at {self.venv_path}...")

        try:
            venv.create(self.venv_path, with_pip=True)
            out.green("✓ Virtual environment created")
            out.blue("Installing requirements from requirements.txt")
            for requirement in self._read_requirements():
                self._install_package(requirement)
            return True
        except Exception as e:
            raise HookException("✗ Unexpected error: ","") from e

    def _read_requirements(self) -> Sequence[str]:
        """Read Requirements file at top level else return empty list"""
        try:
            with open("./requirements.txt", encoding="utf-8") as requirements_file:
                requirements_list = requirements_file.read().splitlines()
                return requirements_list
        except Exception: #pylint: disable=broad-exception-caught
            # Failed to find requirements, either because
            # they don't exist or they are not in the correct directory
            # as this can be fixed manually leaving to dev to update the venv
            return []

    def _install_package(self, package: str) -> bool:
        """Install a package in the virtual environment"""
        pip_path = self._get_pip_path()
        try:
            subprocess.run(
                [str(pip_path), "install", "-q", package],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            out.red(f"✗ Failed to install {package}: {e.stderr.decode()}")
            return False
