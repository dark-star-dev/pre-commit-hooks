#!/usr/bin/env python
"""
Unit tests for pylint_checks.py

Tests the PylintChecker class and its methods for running pylint with score validation.
"""
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import subprocess

from pre_commit_hooks.pylint_checks import PylintChecker, main


class TestPylintCheckerInit(unittest.TestCase):
    """Test cases for PylintChecker initialization"""

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters"""
        checker = PylintChecker(
            target_dir="./src",
            venv_path="./venv",
            threshold=7.5,
            rcfile=".pylintrc"
        )

        self.assertEqual(checker.target_dir, Path("./src"))
        self.assertEqual(checker.venv_path, Path("./venv"))
        self.assertEqual(checker.threshold, 7.5)
        self.assertEqual(checker.rcfile, Path(".pylintrc"))

    def test_init_without_rcfile(self):
        """Test initialization without rcfile"""
        checker = PylintChecker(
            target_dir=".",
            venv_path="./venv",
            threshold=6.0,
            rcfile=None
        )

        self.assertEqual(checker.target_dir, Path("."))
        self.assertEqual(checker.venv_path, Path("./venv"))
        self.assertEqual(checker.threshold, 6.0)
        self.assertIsNone(checker.rcfile)


class TestWarnOnly(unittest.TestCase):
    """Test cases for warn_only method"""

    @patch.object(PylintChecker, 'run')
    def test_warn_only_always_returns_zero(self, mock_run):
        """Test warn_only always returns 0 regardless of run result"""
        mock_run.return_value = 1
        checker = PylintChecker(".", "./venv", 6.0)

        result = checker.warn_only()

        self.assertEqual(result, 0)
        mock_run.assert_called_once()


class TestInstallPylint(unittest.TestCase):
    """Test cases for _install_pylint method"""

    @patch.object(PylintChecker, '_install_package')
    def test_install_pylint_success(self, mock_install):
        """Test successful pylint installation"""
        mock_install.return_value = True
        checker = PylintChecker(".", "./venv", 6.0)

        result = checker._install_pylint()  # pylint: disable=protected-access

        self.assertTrue(result)
        mock_install.assert_called_once_with("pylint")

    @patch.object(PylintChecker, '_install_package')
    def test_install_pylint_failure(self, mock_install):
        """Test pylint installation failure"""
        mock_install.side_effect = subprocess.CalledProcessError(
            1, "pip", stderr=b"Installation failed"
        )
        checker = PylintChecker(".", "./venv", 6.0)

        result = checker._install_pylint()  # pylint: disable=protected-access

        self.assertFalse(result)


class TestExtractScore(unittest.TestCase):
    """Test cases for _extract_score method"""

    def setUp(self):
        """Set up test fixtures"""
        self.checker = PylintChecker(".", "./venv", 6.0)

    def test_extract_score_success(self):
        """Test extracting score from valid output"""
        output = "Your code has been rated at 8.50/10.00"
        result = self.checker._extract_score(output)  # pylint: disable=protected-access

        self.assertEqual(result, 8.50)

    def test_extract_score_negative(self):
        """Test extracting negative score"""
        output = "Your code has been rated at -2.50/10.00"
        result = self.checker._extract_score(output)  # pylint: disable=protected-access

        self.assertEqual(result, -2.50)

    def test_extract_score_perfect(self):
        """Test extracting perfect score"""
        output = "Your code has been rated at 10.00/10.00"
        result = self.checker._extract_score(output)  # pylint: disable=protected-access

        self.assertEqual(result, 10.00)

    def test_extract_score_no_match(self):
        """Test extracting score when pattern doesn't match"""
        output = "No score found in this output"
        result = self.checker._extract_score(output)  # pylint: disable=protected-access

        self.assertIsNone(result)

    def test_extract_score_invalid_format(self):
        """Test extracting score with invalid number format"""
        output = "Your code has been rated at invalid/10.00"
        result = self.checker._extract_score(output)  # pylint: disable=protected-access

        self.assertIsNone(result)


class TestValidateThreshold(unittest.TestCase):
    """Test cases for _validate_threshold method"""

    def test_validate_threshold_above(self):
        """Test validation when score is above threshold"""
        checker = PylintChecker(".", "./venv", 6.0)
        result = checker._validate_threshold(8.5)  # pylint: disable=protected-access

        self.assertEqual(result, 0)

    def test_validate_threshold_exact(self):
        """Test validation when score equals threshold"""
        checker = PylintChecker(".", "./venv", 7.0)
        result = checker._validate_threshold(7.0)  # pylint: disable=protected-access

        self.assertEqual(result, 0)

    def test_validate_threshold_below(self):
        """Test validation when score is below threshold"""
        checker = PylintChecker(".", "./venv", 8.0)
        result = checker._validate_threshold(6.5)  # pylint: disable=protected-access

        self.assertEqual(result, 1)


class TestRunPylint(unittest.TestCase):
    """Test cases for _run_pylint method"""

    @patch("pathlib.Path.exists")
    def test_run_pylint_directory_not_found(self, mock_exists):
        """Test running pylint when target directory doesn't exist"""
        mock_exists.return_value = False
        checker = PylintChecker("./nonexistent", "./venv", 6.0)

        result = checker._run_pylint()  # pylint: disable=protected-access

        self.assertIsNone(result)

    @patch("subprocess.run")
    @patch.object(PylintChecker, '_get_python_path')
    @patch("pathlib.Path.exists")
    def test_run_pylint_success(self, mock_exists, mock_python_path, mock_run):
        """Test successful pylint run"""
        mock_exists.return_value = True
        mock_python_path.return_value = Path("./venv/bin/python")
        mock_result = Mock()
        mock_result.stdout = "Your code has been rated at 8.50/10.00"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        checker = PylintChecker(".", "./venv", 6.0)
        result = checker._run_pylint()  # pylint: disable=protected-access

        self.assertEqual(result, 8.50)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch.object(PylintChecker, '_get_python_path')
    @patch("pathlib.Path.exists")
    def test_run_pylint_with_rcfile(self, mock_exists, mock_python_path, mock_run):
        """Test pylint run with rcfile"""
        mock_exists.return_value = True
        mock_python_path.return_value = Path("./venv/bin/python")
        mock_result = Mock()
        mock_result.stdout = "Your code has been rated at 9.00/10.00"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        checker = PylintChecker(".", "./venv", 6.0, rcfile=".pylintrc")
        result = checker._run_pylint()  # pylint: disable=protected-access

        self.assertEqual(result, 9.00)
        # Verify rcfile was added to command
        call_args = mock_run.call_args[0][0]
        self.assertTrue(any("--rcfile=" in str(arg) for arg in call_args))

    @patch("subprocess.run")
    @patch.object(PylintChecker, '_get_python_path')
    @patch("pathlib.Path.exists")
    def test_run_pylint_no_score_in_output(self, mock_exists, mock_python_path, mock_run):
        """Test pylint run when score cannot be extracted"""
        mock_exists.return_value = True
        mock_python_path.return_value = Path("./venv/bin/python")
        mock_result = Mock()
        mock_result.stdout = "No score in this output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        checker = PylintChecker(".", "./venv", 6.0)
        result = checker._run_pylint()  # pylint: disable=protected-access

        self.assertIsNone(result)

    @patch("subprocess.run")
    @patch.object(PylintChecker, '_get_python_path')
    @patch("pathlib.Path.exists")
    def test_run_pylint_exception(self, mock_exists, mock_python_path, mock_run):
        """Test pylint run with exception"""
        mock_exists.return_value = True
        mock_python_path.return_value = Path("./venv/bin/python")
        mock_run.side_effect = Exception("Unexpected error")

        checker = PylintChecker(".", "./venv", 6.0)
        result = checker._run_pylint()  # pylint: disable=protected-access

        self.assertIsNone(result)


class TestRunMethod(unittest.TestCase):
    """Test cases for run method"""

    @patch.object(PylintChecker, '_validate_threshold')
    @patch.object(PylintChecker, '_run_pylint')
    @patch.object(PylintChecker, '_install_pylint')
    @patch.object(PylintChecker, '_setup_venv')
    def test_run_success(self, mock_setup, mock_install, mock_run_pylint, mock_validate):
        """Test successful run"""
        mock_setup.return_value = True
        mock_install.return_value = True
        mock_run_pylint.return_value = 8.5
        mock_validate.return_value = 0

        checker = PylintChecker(".", "./venv", 6.0)
        result = checker.run()

        self.assertEqual(result, 0)
        mock_setup.assert_called_once()
        mock_install.assert_called_once()
        mock_run_pylint.assert_called_once()
        mock_validate.assert_called_once_with(8.5)

    @patch.object(PylintChecker, '_setup_venv')
    def test_run_setup_venv_fails(self, mock_setup):
        """Test run when venv setup fails"""
        mock_setup.return_value = False

        checker = PylintChecker(".", "./venv", 6.0)
        result = checker.run()

        self.assertEqual(result, 1)

    @patch.object(PylintChecker, '_install_pylint')
    @patch.object(PylintChecker, '_setup_venv')
    def test_run_install_pylint_fails(self, mock_setup, mock_install):
        """Test run when pylint installation fails"""
        mock_setup.return_value = True
        mock_install.return_value = False

        checker = PylintChecker(".", "./venv", 6.0)
        result = checker.run()

        self.assertEqual(result, 1)

    @patch.object(PylintChecker, '_run_pylint')
    @patch.object(PylintChecker, '_install_pylint')
    @patch.object(PylintChecker, '_setup_venv')
    def test_run_pylint_returns_none(self, mock_setup, mock_install, mock_run_pylint):
        """Test run when pylint execution returns None"""
        mock_setup.return_value = True
        mock_install.return_value = True
        mock_run_pylint.return_value = None

        checker = PylintChecker(".", "./venv", 6.0)
        result = checker.run()

        self.assertEqual(result, 1)

    @patch.object(PylintChecker, '_setup_venv')
    def test_run_keyboard_interrupt(self, mock_setup):
        """Test run handles keyboard interrupt"""
        mock_setup.side_effect = KeyboardInterrupt()

        checker = PylintChecker(".", "./venv", 6.0)
        result = checker.run()

        self.assertEqual(result, 1)


class TestMainFunction(unittest.TestCase):
    """Test cases for main function"""

    @patch("pre_commit_hooks.pylint_checks.PylintChecker")
    @patch("sys.argv", ["pylint_checks.py"])
    def test_main_default_arguments(self, mock_checker_class):
        """Test main with default arguments"""
        mock_checker = Mock()
        mock_checker.run.return_value = 0
        mock_checker_class.return_value = mock_checker

        result = main()

        self.assertEqual(result, 0)
        mock_checker_class.assert_called_once_with(
            target_dir=".",
            venv_path="./venv",
            threshold=6.0,
            rcfile=None
        )
        mock_checker.run.assert_called_once()

    @patch("pre_commit_hooks.pylint_checks.PylintChecker")
    @patch("sys.argv", [
        "pylint_checks.py",
        "--target-dir", "./src",
        "--venv-path", "./my_venv",
        "--threshold", "8.0",
        "--rcfile", ".pylintrc"
    ])
    def test_main_custom_arguments(self, mock_checker_class):
        """Test main with custom arguments"""
        mock_checker = Mock()
        mock_checker.run.return_value = 0
        mock_checker_class.return_value = mock_checker

        result = main()

        self.assertEqual(result, 0)
        mock_checker_class.assert_called_once_with(
            target_dir="./src",
            venv_path="./my_venv",
            threshold=8.0,
            rcfile=".pylintrc"
        )

    @patch("pre_commit_hooks.pylint_checks.PylintChecker")
    @patch("sys.argv", ["pylint_checks.py", "--warn-only"])
    def test_main_warn_only(self, mock_checker_class):
        """Test main with warn-only flag"""
        mock_checker = Mock()
        mock_checker.warn_only.return_value = 0
        mock_checker_class.return_value = mock_checker

        result = main()

        self.assertEqual(result, 0)
        mock_checker.warn_only.assert_called_once()
        mock_checker.run.assert_not_called()

    @patch("sys.argv", ["pylint_checks.py", "--threshold", "15.0"])
    def test_main_invalid_threshold_high(self):
        """Test main with threshold above 10"""
        result = main()

        self.assertEqual(result, 1)

    @patch("sys.argv", ["pylint_checks.py", "--threshold", "-1.0"])
    def test_main_invalid_threshold_negative(self):
        """Test main with negative threshold"""
        result = main()

        self.assertEqual(result, 1)

    @patch("pre_commit_hooks.pylint_checks.PylintChecker")
    @patch("sys.argv", ["pylint_checks.py"])
    def test_main_returns_error_code(self, mock_checker_class):
        """Test main returns error code from checker"""
        mock_checker = Mock()
        mock_checker.run.return_value = 1
        mock_checker_class.return_value = mock_checker

        result = main()

        self.assertEqual(result, 1)
