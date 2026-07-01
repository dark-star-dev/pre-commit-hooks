#!/usr/bin/env python
"""
Test Runner with Coverage Validation Script

This script runs unit tests in a virtual environment and validates that
code coverage meets a minimum threshold (default: 60%).

Supports both unittest and pytest frameworks with automatic detection.
"""
import os
import errno
from argparse import ArgumentParser, BooleanOptionalAction ,RawDescriptionHelpFormatter
import json
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, TypedDict, Optional, Iterable
from pre_commit_hooks.hook_utils import TerminalOutput
from pre_commit_hooks.precommit import PreCommitPythonBase, pre_commit_exception_handler

class FileSummary(TypedDict):
    """Coverage summary for a single file."""
    percent_covered: float


class FileData(TypedDict):
    """Coverage data for a single file."""
    summary: FileSummary
    missing_lines: list[int]


class CoverageTotals(TypedDict):
    """Total coverage statistics."""
    percent_covered: float


class CoverageData(TypedDict):
    """Complete coverage report data structure."""
    totals: CoverageTotals
    files: dict[str, FileData]


class FileCoverageInfo(NamedTuple):
    """Coverage information for a single file."""
    filepath: str
    coverage_pct: float
    missing_lines: list[int]

TITLE = "Commit Message Check"
VERSION_NUMBER = "2.0.0"

out = TerminalOutput.of()
class CodeCoverageChecker(PreCommitPythonBase):
    """Test runner class with coverage validation"""

    coverage_score: int = 80
    coverage_threshold: int = 60

    def __init__( #pylint: disable=too-many-positional-arguments,too-many-arguments
        self,
        test_dir: str,
        source_dir: Optional[str],
        venv_path: str,
        threshold: float,
        framework: str,
    ) -> None:
        self.test_dir: Path = Path(test_dir)
        self.source_dir: Optional[Path] = Path(source_dir) if source_dir else None
        self.venv_path: Path = Path(venv_path)
        self.threshold: float = threshold
        self.framework: str = framework
        self.detected_framework: Optional[str] = None

    @pre_commit_exception_handler
    def run(self) -> int:
        """Main execution flow"""
        out.bold("Test Runner with Coverage Validation")
        # Step 1: Setup virtual environment
        if not self._setup_venv():
            return 1
        # Step 2: Detect or validate framework
        if not self._setup_framework():
            return 1
        # Step 3: Run tests with coverage
        if not self._run_tests():
            return 1
        # Step 4: Analyze coverage
        coverage_data = self._analyze_coverage()
        if coverage_data is None:
            return 1
        # Step 5: Validate threshold
        return self._validate_threshold(coverage_data)

    def warn_only(self) -> int:
        """
        Run main execution flow and only 
        warn if threshold is not met,
        Allows hook to pass
        """
        self.run()
        return 0

    def _detect_framework(self) -> str:
        """Detect which test framework to use"""
        # Check for pytest configuration files
        pytest_configs = [
            self.test_dir / "pytest.ini",
            self.test_dir / "pyproject.toml",
            self.test_dir / "setup.cfg",
            Path.cwd() / "pytest.ini",
            Path.cwd() / "pyproject.toml",
        ]

        for config in pytest_configs:
            if config.exists():
                return "pytest"

        # Check for pytest test files (test_*.py or *_test.py)
        if self.test_dir.exists():
            for _ in self.test_dir.rglob("test_*.py"):
                return "pytest"
            for _ in self.test_dir.rglob("*_test.py"):
                return "pytest"

        # Default to unittest
        return "unittest"

    def _setup_framework(self) -> bool:
        """Setup and install dependencies for the test framework"""
        if self.framework == "auto":
            self.detected_framework = self._detect_framework()
            out.blue(f"Detected test framework: {self.detected_framework}")
        else:
            self.detected_framework = self.framework
            out.blue(f"Using specified framework: {self.detected_framework}")

        # Install coverage (required for both frameworks)
        out.blue("Installing coverage...")
        if not self._install_package("coverage"):
            return False

        # Install pytest if needed
        if self.detected_framework == "pytest":
            out.blue("Installing pytest and pytest-cov...")
            if not self._install_package("pytest"):
                return False
            if not self._install_package("pytest-cov"):
                return False

        out.green("✓ Dependencies installed")
        return True

    def _run_tests(self) -> bool:
        """Run tests with coverage"""
        if not self.test_dir.exists():
            out.red(f"✗ Test directory not found: {self.test_dir}")
            return False

        out.bold("Running tests with coverage...")

        python_path = self._get_python_path()

        # Build coverage command
        if self.detected_framework == "pytest":
            cmd = [
                str(python_path),
                "-m",
                "coverage",
                "run",
                "-m",
                "pytest",
                str(self.test_dir),
            ]
        else:
            cmd = [
                str(python_path),
                "-m",
                "coverage",
                "run",
                "-m",
                "unittest",
                "discover",
                "-s",
                str(self.test_dir),
                "-p",
                "test*.py",
            ]

        # Add source directory if specified
        if self.source_dir:
            cmd.insert(4, f"--source={self.source_dir}")

        try:
            result = subprocess.run(cmd, capture_output=False, text=True, check=False)

            if result.returncode != 0:
                out.red("✗ Tests failed")
                return False

            out.green("✓ All tests passed")
            return True

        except subprocess.CalledProcessError as e:
            out.red(f"✗ Error running tests: {e}")
            return False

    def _analyze_coverage(self) -> Optional[CoverageData]:
        """Analyze coverage and return detailed data"""
        python_path = self._get_python_path()

        out.bold("Analyzing coverage...")

        # Generate JSON report
        try:
            subprocess.run(
                [str(python_path), "-m", "coverage", "json", "-o", "coverage.json"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            out.red(f"✗ Failed to generate coverage report: {e.stderr.decode()}")
            return None

        # Read JSON report
        try:
            with open("coverage.json", "r", encoding="utf-8") as f:
                coverage_data = json.load(f)
            #clean-up coverage.json file from file system after reading
            os.remove("coverage.json")
            return coverage_data
        except OSError as e:
            if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                out.red(f"✗ Failed to remove coverage report from file system: {e}")
            return None
        except Exception as e: #pylint: disable=broad-exception-caught
            out.red(f"✗ Failed to read coverage report: {e}")
            return None

    def _validate_threshold(self, coverage_data: CoverageData) -> int:
        """Validate coverage threshold and display results"""
        total_coverage = coverage_data["totals"]["percent_covered"]

        out.bold("Coverage Report")
        out.white(f"{'─' * 50}")
        out.white(f"Overall Coverage: {total_coverage:.1f}%")
        out.white(f"Threshold: {self.threshold}%")
        out.white(f"{'─' * 50}")

        if total_coverage >= self.threshold:
            out.green("✓ Coverage meets threshold!")
            return 0

        # Coverage below threshold - show detailed breakdown
        out.red(f"✗ Coverage below threshold ({self.threshold}%)")
        out.bold("Detailed Breakdown:")
        out.white(f"{'─' * 80}")

        # Sort files by coverage percentage
        files_data: Iterable[FileCoverageInfo] = sorted(
            (FileCoverageInfo(
                filepath,
                file_data["summary"]["percent_covered"],
                file_data["missing_lines"]
            ) for filepath, file_data in coverage_data["files"].items()),
            key=lambda x: x.coverage_pct  # Sort by coverage percentage
        )

        for filepath, coverage_pct, missing_lines in files_data:
            # Format file path (relative to current directory)
            try:
                rel_path = Path(filepath).relative_to(Path.cwd())
            except ValueError:
                rel_path = filepath

            if coverage_pct >= self.threshold:
                out.green(f"✓ {rel_path}: {coverage_pct:.1f}%")
            else:
                out.red(f"✗ {rel_path}: {coverage_pct:.1f}%")

            if missing_lines and coverage_pct < self.threshold:
                # Group consecutive line numbers
                line_groups = self._group_consecutive_lines(missing_lines)
                out.yellow(f"(Missing: {line_groups})")
            else:
                out.white("")

        out.white(f"{'─' * 80}\n")
        return 1

    def _group_consecutive_lines(self, lines: list[int]) -> str:
        """Group consecutive line numbers for better readability"""
        if not lines:
            return ""

        lines = sorted(lines)
        groups = []
        start = lines[0]
        end = lines[0]

        for i in range(1, len(lines)):
            if lines[i] == end + 1:
                end = lines[i]
            else:
                if start == end:
                    groups.append(str(start))
                else:
                    groups.append(f"{start}-{end}")
                start = end = lines[i]

        # Add the last group
        if start == end:
            groups.append(str(start))
        else:
            groups.append(f"{start}-{end}")

        return ", ".join(groups)


def main() -> int:
    """Main entry point"""
    parser = ArgumentParser(
        description="Run unit tests with coverage validation",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect framework and use defaults
  python run_tests_with_coverage.py
  
  # Specify test directory and source directory
  python run_tests_with_coverage.py --test-dir ./tests --source-dir ./src
  
  # Force unittest framework
  python run_tests_with_coverage.py --framework unittest
  
  # Use pytest with custom threshold
  python run_tests_with_coverage.py --framework pytest --threshold 75
  
  # Custom venv path
  python run_tests_with_coverage.py --venv-path ./my_venv
        """,
    )

    parser.add_argument(
        "--test-dir",
        default=".",
        help="Directory containing test files (default: ./tests)",
    )

    parser.add_argument(
        "--warn-only",
        type=bool,
        default=False,
        action=BooleanOptionalAction,
        help="Run in Debug mode Output Data received from request",
    )

    parser.add_argument(
        "--source-dir",
        default=None,
        help="Source code directory to measure coverage (default: auto-detect)",
    )

    parser.add_argument(
        "--venv-path",
        default="./venv",
        help="Path to virtual environment (default: ./venv)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Minimum coverage threshold percentage (default: 80)",
    )

    parser.add_argument(
        "--framework",
        choices=["unittest", "pytest", "auto"],
        default="auto",
        help="Test framework to use (default: auto)",
    )

    args = parser.parse_args()

    # Validate threshold
    if not 0 <= args.threshold <= 100:
        out.red("Error: Threshold must be between 0 and 100")
        return 1

    # Create and run test runner
    runner = CodeCoverageChecker(
        test_dir=args.test_dir,
        source_dir=args.source_dir,
        venv_path=args.venv_path,
        threshold=args.threshold,
        framework=args.framework,
    )

    return runner.run() if not args.warn_only else runner.warn_only()


if __name__ == "__main__":
    sys.exit(main())
