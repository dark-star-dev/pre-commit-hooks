#!/usr/bin/env python
"""
Pylint Runner with Score Validation Script

This script runs pylint in a virtual environment and validates that
the linting score meets a minimum threshold (default: 6.0/10.0).

Supports checking individual files or entire directories.
"""
from argparse import ArgumentParser, BooleanOptionalAction ,RawDescriptionHelpFormatter
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional
from pre_commit_hooks.hook_utils import TerminalOutput
from pre_commit_hooks.precommit import PreCommitPythonBase,pre_commit_exception_handler

TITLE = "Pylint Score Check"
VERSION_NUMBER = "1.0.0"

out = TerminalOutput.of()


class PylintChecker(PreCommitPythonBase):
    """Pylint runner class with score validation"""

    def __init__(
        self,
        target_dir: str,
        venv_path: str,
        threshold: float,
        rcfile: Optional[str] = None,
    ) -> None:
        self.target_dir: Path = Path(target_dir)
        self.venv_path: Path = Path(venv_path)
        self.threshold: float = threshold
        self.rcfile: Optional[Path] = Path(rcfile) if rcfile else None

    def warn_only(self) -> int:
        """
        Run main execution flow and only 
        warn if threshold is not met,
        Allows hook to pass
        """
        self.run()
        return 0

    @pre_commit_exception_handler
    def run(self) -> int:
        """Main execution flow"""
        out.bold("Pylint Runner with Score Validation")
        # Step 1: Setup virtual environment
        if not self._setup_venv():
            return 1
        # Step 2: Install pylint
        if not self._install_pylint():
            return 1
        # Step 3: Run pylint
        score = self._run_pylint()
        if score is None:
            return 1
        # Step 4: Validate threshold
        return self._validate_threshold(score)

    def _install_pylint(self) -> bool:
        """Install pylint in the virtual environment"""
        out.blue("Installing pylint...")
        try:
            self._install_package("pylint")
            out.green("✓ Pylint installed")
            return True
        except subprocess.CalledProcessError as e:
            out.red(f"✗ Failed to install pylint: {e.stderr.decode()}")
            return False

    def _run_pylint(self) -> Optional[float]:
        """Run pylint and extract the score"""
        if not self.target_dir.exists():
            out.red(f"✗ Target directory not found: {self.target_dir}")
            return None

        out.bold("Running pylint...")

        python_path = self._get_python_path()

        # Build pylint command
        cmd = [
            str(python_path),
            "-m",
            "pylint",
            "--score=y",
            "--reports=n",
            "--ignore-paths",
            "^venv/.*$",
            str(self.target_dir),
        ]

        # Add rcfile if specified
        if self.rcfile and self.rcfile.exists():
            cmd.append(f"--rcfile={self.rcfile}")
            out.blue(f"Using config file: {self.rcfile}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            # Pylint returns non-zero for issues, but we still want to parse the score
            output = result.stdout + result.stderr

            # Extract score from pylint output
            score = self._extract_score(output)

            if score is None:
                out.red("✗ Failed to extract pylint score from output")
                out.yellow("Output:")
                out.white(output)
                return None

            return score

        except Exception as e: #pylint: disable=broad-exception-caught
            out.red(f"✗ Error running pylint: {e}")
            return None

    def _extract_score(self, output: str) -> Optional[float]:
        """Extract the pylint score from output"""
        # Pylint outputs score in format: "Your code has been rated at X.XX/10.00"
        pattern = r"Your code has been rated at ([-\d.]+)/10"
        match = re.search(pattern, output)

        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

        return None

    def _validate_threshold(self, score: float) -> int:
        """Validate pylint score threshold and display results"""
        out.bold("Pylint Report")
        out.white(f"{'─' * 50}")
        out.white(f"Pylint Score: {score:.2f}/10.00")
        out.white(f"Threshold: {self.threshold:.2f}/10.00")
        out.white(f"{'─' * 50}")

        if score >= self.threshold:
            out.green("✓ Pylint score meets threshold!")
            return 0

        # Score below threshold
        out.red(f"✗ Pylint score below threshold ({self.threshold:.2f}/10.00)")
        out.yellow("Please fix the linting issues and try again.")
        return 1


def main() -> int:
    """Main entry point"""
    parser = ArgumentParser(
        description="Run pylint with score validation",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check current directory with default threshold (6.0/10.0)
  python pylint_checks.py
  
  # Check specific directory
  python pylint_checks.py --target-dir ./src
  
  # Use custom threshold
  python pylint_checks.py --threshold 7.0
  
  # Use custom pylint config file
  python pylint_checks.py --rcfile .pylintrc
  
  # Custom venv path
  python pylint_checks.py --venv-path ./my_venv
        """,
    )

    parser.add_argument(
        "--target-dir",
        default=".",
        help="Directory or file to check with pylint (default: current directory)",
    )

    parser.add_argument(
        "--warn-only",
        type=bool,
        default=False,
        action=BooleanOptionalAction,
        help="Run in Debug mode Output Data received from request",
    )

    parser.add_argument(
        "--venv-path",
        default="./venv",
        help="Path to virtual environment (default: ./venv)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=6.0,
        help="Minimum pylint score threshold (default: 6.0/10.0)",
    )

    parser.add_argument(
        "--rcfile",
        default=None,
        help="Path to pylint configuration file (default: None)",
    )

    args = parser.parse_args()

    # Validate threshold
    if not 0 <= args.threshold <= 10:
        out.red("Error: Threshold must be between 0 and 10")
        return 1

    # Create and run pylint checker
    checker = PylintChecker(
        target_dir=args.target_dir,
        venv_path=args.venv_path,
        threshold=args.threshold,
        rcfile=args.rcfile,
    )

    return checker.run() if not args.warn_only else checker.warn_only()


if __name__ == "__main__":
    sys.exit(main())
