#!/usr/bin/env python
"""
Unit tests for python_precommit.py

Tests the PreCommitPythonBase class and pre_commit_exception_handler decorator.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess

from pre_commit_hooks.precommit import PreCommitPythonBase, pre_commit_exception_handler
from pre_commit_hooks.hook_utils import HookException


class TestPreCommitExceptionHandler(unittest.TestCase):
    """Test cases for pre_commit_exception_handler decorator"""

    def test_decorator_success(self):
        """Test decorator with successful function execution"""
        @pre_commit_exception_handler
        def successful_function():
            return 0

        result = successful_function()
        self.assertEqual(result, 0)

    def test_decorator_keyboard_interrupt(self):
        """Test decorator handles KeyboardInterrupt"""
        @pre_commit_exception_handler
        def interrupted_function():
            raise KeyboardInterrupt()

        result = interrupted_function()
        self.assertEqual(result, 1)

    def test_decorator_exception(self):
        """Test decorator wraps exceptions in HookException"""
        @pre_commit_exception_handler
        def failing_function():
            raise ValueError("Test error")

        with self.assertRaises(HookException):
            failing_function()


class TestPreCommitPythonBase(unittest.TestCase):
    """Test cases for PreCommitPythonBase class"""

    def setUp(self):
        """Set up test fixtures"""
        self.base = PreCommitPythonBase()
        self.base.venv_path = Path("./test_venv")

    @patch("sys.platform", "darwin")
    def test_get_pip_path_unix(self):
        """Test pip path on Unix-like systems"""
        result = self.base._get_pip_path()  # pylint: disable=protected-access
        self.assertEqual(result, Path("./test_venv/bin/pip"))

    @patch("sys.platform", "win32")
    def test_get_pip_path_windows(self):
        """Test pip path on Windows"""
        result = self.base._get_pip_path()  # pylint: disable=protected-access
        self.assertEqual(result, Path("./test_venv/Scripts/pip.exe"))

    @patch("sys.platform", "darwin")
    def test_get_python_path_unix(self):
        """Test python path on Unix-like systems"""
        result = self.base._get_python_path()  # pylint: disable=protected-access
        self.assertEqual(result, Path("./test_venv/bin/python"))

    @patch("sys.platform", "win32")
    def test_get_python_path_windows(self):
        """Test python path on Windows"""
        result = self.base._get_python_path()  # pylint: disable=protected-access
        self.assertEqual(result, Path("./test_venv/Scripts/python.exe"))

    @patch("pathlib.Path.exists")
    def test_setup_venv_existing(self, mock_exists):
        """Test setup with existing venv"""
        mock_exists.return_value = True

        result = self.base._setup_venv()  # pylint: disable=protected-access

        self.assertTrue(result)
        mock_exists.assert_called_once()

    @patch("venv.create")
    @patch("pathlib.Path.exists")
    def test_setup_venv_create_new(self, mock_exists, mock_venv_create):
        """Test creating new venv"""
        mock_exists.return_value = False
        self.base._read_requirements = Mock(return_value=[])  # pylint: disable=protected-access

        result = self.base._setup_venv()  # pylint: disable=protected-access

        self.assertTrue(result)
        mock_venv_create.assert_called_once_with(self.base.venv_path, with_pip=True)

    @patch("venv.create")
    @patch("pathlib.Path.exists")
    def test_setup_venv_with_requirements(self, mock_exists, mock_venv_create):
        """Test creating venv and installing requirements"""
        mock_exists.return_value = False
        self.base._read_requirements = Mock(return_value=["pytest", "pylint"])  # pylint: disable=protected-access
        self.base._install_package = Mock(return_value=True)  # pylint: disable=protected-access

        result = self.base._setup_venv()  # pylint: disable=protected-access

        self.assertTrue(result)
        mock_venv_create.assert_called_once()
        self.assertEqual(self.base._install_package.call_count, 2)  # pylint: disable=protected-access

    @patch("venv.create")
    @patch("pathlib.Path.exists")
    def test_setup_venv_creation_fails(self, mock_exists, mock_venv_create):
        """Test venv creation failure"""
        mock_exists.return_value = False
        mock_venv_create.side_effect = Exception("Creation failed")

        with self.assertRaises(HookException):
            self.base._setup_venv()  # pylint: disable=protected-access

    @patch("builtins.open", create=True)
    def test_read_requirements_success(self, mock_open):
        """Test reading requirements file successfully"""
        mock_file = MagicMock()
        mock_file.read.return_value = "pytest\npylint\ncoverage"
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.base._read_requirements()  # pylint: disable=protected-access

        self.assertEqual(result, ["pytest", "pylint", "coverage"])

    @patch("builtins.open", side_effect=FileNotFoundError())
    def test_read_requirements_file_not_found(self, mock_open):  # pylint: disable=unused-argument
        """Test reading requirements when file doesn't exist"""
        result = self.base._read_requirements()  # pylint: disable=protected-access

        self.assertEqual(result, [])

    @patch("subprocess.run")
    def test_install_package_success(self, mock_run):
        """Test successful package installation"""
        mock_run.return_value = Mock(returncode=0)

        result = self.base._install_package("pytest")  # pylint: disable=protected-access

        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_install_package_failure(self, mock_run):
        """Test package installation failure"""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "pip", stderr=b"Installation failed"
        )

        result = self.base._install_package("pytest")  # pylint: disable=protected-access

        self.assertFalse(result)
