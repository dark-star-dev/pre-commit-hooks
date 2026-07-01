"""
Unit tests for coverage_checks.py

Tests the CodeCoverageChecker class and related functionality using unittest.
"""
import json
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch, mock_open
import subprocess

# Import the module under test
from pre_commit_hooks.coverage_checks import (
    CodeCoverageChecker,
    main,
    CoverageData,
    CoverageTotals)
from pre_commit_hooks.hook_utils import HookException


class TestCodeCoverageCheckerInit(TestCase):
    """Tests for CodeCoverageChecker initialization"""

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters"""
        checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="src",
            venv_path=".venv",
            threshold=75.0,
            framework="pytest",
        )

        self.assertEqual(checker.test_dir, Path("tests"))
        self.assertEqual(checker.source_dir, Path("src"))
        self.assertEqual(checker.venv_path, Path(".venv"))
        self.assertEqual(checker.threshold, 75.0)
        self.assertEqual(checker.framework, "pytest")
        self.assertIsNone(checker.detected_framework)

    def test_init_without_source_dir(self):
        """Test initialization without source directory"""
        checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=".venv",
            threshold=80.0,
            framework="auto",
        )

        self.assertIsNone(checker.source_dir)
        self.assertEqual(checker.test_dir, Path("tests"))


class TestVirtualEnvironmentSetup(TestCase):
    """Tests for virtual environment setup methods"""

    def setUp(self):
        """Set up temporary directory for tests"""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_setup_venv_existing(self):
        """Test setup when venv already exists"""
        venv_path = self.tmp_path / "venv"
        venv_path.mkdir()

        checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(venv_path),
            threshold=80.0,
            framework="auto",
        )

        self.assertTrue(checker._setup_venv())#pylint: disable=protected-access

    @patch("pre_commit_hooks.coverage_checks.CodeCoverageChecker._read_requirements")
    @patch("pre_commit_hooks.precommit.venv.create")
    def test_setup_venv_create_new(self, mock_venv_create, mock_read_requirements):
        """Test creating new virtual environment"""
        venv_path = self.tmp_path / "new_venv"
        mock_read_requirements.return_value = []

        checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(venv_path),
            threshold=80.0,
            framework="auto",
        )

        self.assertTrue(checker._setup_venv())#pylint: disable=protected-access
        mock_venv_create.assert_called_once_with(venv_path, with_pip=True)

    @patch("pre_commit_hooks.precommit.venv.create")
    def test_setup_venv_creation_fails(self, mock_venv_create):
        """Test handling of venv creation failure"""
        venv_path = self.tmp_path / "new_venv"
        mock_venv_create.side_effect = Exception("Creation failed")

        checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(venv_path),
            threshold=80.0,
            framework="auto",
        )

        with self.assertRaises(HookException):
            checker._setup_venv()#pylint: disable=protected-access

    def test_get_paths_by_platform_win32(self):
        """Test getting pip and python paths on Windows"""
        checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        with patch("sys.platform", "win32"):
            pip_path = checker._get_pip_path()#pylint: disable=protected-access
            python_path = checker._get_python_path()#pylint: disable=protected-access

            self.assertTrue(
                str(pip_path).endswith(
                    "venv/Scripts/pip.exe".replace("/", str(Path("/")))
                )
            )
            self.assertTrue(
                str(python_path).endswith(
                    "venv/Scripts/python.exe".replace("/", str(Path("/")))
                )
            )

    def test_get_paths_by_platform_linux(self):
        """Test getting pip and python paths on Linux"""
        checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        with patch("sys.platform", "linux"):
            pip_path = checker._get_pip_path()#pylint: disable=protected-access
            python_path = checker._get_python_path()#pylint: disable=protected-access

            self.assertTrue(
                str(pip_path).endswith("venv/bin/pip".replace("/", str(Path("/"))))
            )
            self.assertTrue(
                str(python_path).endswith(
                    "venv/bin/python".replace("/", str(Path("/")))
                )
            )

    def test_get_paths_by_platform_darwin(self):
        """Test getting pip and python paths on macOS"""
        checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        with patch("sys.platform", "darwin"):
            pip_path = checker._get_pip_path()#pylint: disable=protected-access
            python_path = checker._get_python_path()#pylint: disable=protected-access

            self.assertTrue(
                str(pip_path).endswith("venv/bin/pip".replace("/", str(Path("/"))))
            )
            self.assertTrue(
                str(python_path).endswith(
                    "venv/bin/python".replace("/", str(Path("/")))
                )
            )


class TestPackageInstallation(TestCase):
    """Tests for package installation"""

    def setUp(self):
        """Set up temporary directory and checker for tests"""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)
        self.checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_install_package_success(self, mock_run):
        """Test successful package installation"""
        mock_run.return_value = Mock(returncode=0)

        self.assertTrue(self.checker._install_package("pytest"))#pylint: disable=protected-access
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_install_package_failure(self, mock_run):
        """Test package installation failure"""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "pip", stderr=b"Installation failed"
        )

        self.assertFalse(self.checker._install_package("pytest"))#pylint: disable=protected-access


class TestFrameworkDetection(TestCase):
    """Tests for test framework detection"""

    def setUp(self):
        """Set up temporary directory for tests"""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_detect_framework_pytest_ini(self):
        """Test detection with pytest.ini configuration file"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()
        (self.tmp_path / "pytest.ini").touch()

        with patch("pathlib.Path.cwd", return_value=self.tmp_path):
            checker = CodeCoverageChecker(
                test_dir=str(test_dir),
                source_dir="",
                venv_path=str(self.tmp_path / "venv"),
                threshold=80.0,
                framework="auto",
            )

            self.assertEqual(checker._detect_framework(), "pytest")#pylint: disable=protected-access

    def test_detect_framework_pyproject_toml(self):
        """Test detection with pyproject.toml configuration file"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()
        (self.tmp_path / "pyproject.toml").touch()

        with patch("pathlib.Path.cwd", return_value=self.tmp_path):
            checker = CodeCoverageChecker(
                test_dir=str(test_dir),
                source_dir="",
                venv_path=str(self.tmp_path / "venv"),
                threshold=80.0,
                framework="auto",
            )

            self.assertEqual(checker._detect_framework(), "pytest")#pylint: disable=protected-access

    def test_detect_framework_setup_cfg(self):
        """Test detection with setup.cfg configuration file"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "setup.cfg").touch()

        with patch("pathlib.Path.cwd", return_value=self.tmp_path):
            checker = CodeCoverageChecker(
                test_dir=str(test_dir),
                source_dir="",
                venv_path=str(self.tmp_path / "venv"),
                threshold=80.0,
                framework="auto",
            )

            self.assertEqual(checker._detect_framework(), "pytest")#pylint: disable=protected-access

    def test_detect_framework_test_files(self):
        """Test detection with test_*.py files"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_example.py").touch()

        checker = CodeCoverageChecker(
            test_dir=str(test_dir),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="auto",
        )

        self.assertEqual(checker._detect_framework(), "pytest")#pylint: disable=protected-access

    def test_detect_framework_unittest_default(self):
        """Test default to unittest when no pytest indicators found"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()

        with patch("pathlib.Path.cwd", return_value=self.tmp_path):
            checker = CodeCoverageChecker(
                test_dir=str(test_dir),
                source_dir="",
                venv_path=str(self.tmp_path / "venv"),
                threshold=80.0,
                framework="auto",
            )

            self.assertEqual(checker._detect_framework(), "unittest")#pylint: disable=protected-access

    @patch.object(CodeCoverageChecker, "_detect_framework")
    @patch.object(CodeCoverageChecker, "_install_package")
    def test_setup_framework_auto(self, mock_install, mock_detect):
        """Test framework setup with auto detection"""
        mock_detect.return_value = "pytest"
        mock_install.return_value = True

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="auto",
        )

        self.assertTrue(checker._setup_framework())#pylint: disable=protected-access
        mock_detect.assert_called_once()

    @patch.object(CodeCoverageChecker, "_detect_framework")
    @patch.object(CodeCoverageChecker, "_install_package")
    def test_setup_framework_unittest(self, mock_install, mock_detect):
        """Test framework setup with unittest specified"""
        mock_detect.return_value = "pytest"
        mock_install.return_value = True

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="unittest",
        )

        self.assertTrue(checker._setup_framework())#pylint: disable=protected-access
        mock_detect.assert_not_called()

    @patch.object(CodeCoverageChecker, "_detect_framework")
    @patch.object(CodeCoverageChecker, "_install_package")
    def test_setup_framework_pytest(self, mock_install, mock_detect):
        """Test framework setup with pytest specified"""
        mock_detect.return_value = "pytest"
        mock_install.return_value = True

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertTrue(checker._setup_framework())#pylint: disable=protected-access
        mock_detect.assert_not_called()

    @patch.object(CodeCoverageChecker, "_install_package")
    def test_setup_framework_install_failure(self, mock_install):
        """Test framework setup when package installation fails"""
        mock_install.return_value = False

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="unittest",
        )

        self.assertFalse(checker._setup_framework())#pylint: disable=protected-access


class TestRunTests(TestCase):
    """Tests for running tests with coverage"""

    def setUp(self):
        """Set up temporary directory for tests"""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_run_tests_directory_not_found(self):
        """Test handling when test directory doesn't exist"""
        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "nonexistent"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )
        checker.detected_framework = "pytest"

        self.assertFalse(checker._run_tests())#pylint: disable=protected-access

    @patch("subprocess.run")
    def test_run_tests_pytest(self, mock_run):
        """Test running tests with pytest framework"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()

        mock_run.return_value = Mock(returncode=0)

        checker = CodeCoverageChecker(
            test_dir=str(test_dir),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )
        checker.detected_framework = "pytest"

        self.assertTrue(checker._run_tests())#pylint: disable=protected-access

        call_args = mock_run.call_args[0][0]
        self.assertIn("pytest", call_args)

    @patch("subprocess.run")
    def test_run_tests_unittest(self, mock_run):
        """Test running tests with unittest framework"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()

        mock_run.return_value = Mock(returncode=0)

        checker = CodeCoverageChecker(
            test_dir=str(test_dir),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="unittest",
        )
        checker.detected_framework = "unittest"

        self.assertTrue(checker._run_tests())#pylint: disable=protected-access

        call_args = mock_run.call_args[0][0]
        self.assertIn("unittest", call_args)
        self.assertIn("discover", call_args)

    @patch("subprocess.run")
    def test_run_tests_with_source_dir(self, mock_run):
        """Test running tests with source directory specified"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()
        source_dir = self.tmp_path / "src"
        source_dir.mkdir()

        mock_run.return_value = Mock(returncode=0)

        checker = CodeCoverageChecker(
            test_dir=str(test_dir),
            source_dir=str(source_dir),
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )
        checker.detected_framework = "pytest"

        self.assertTrue(checker._run_tests())#pylint: disable=protected-access
        call_args = mock_run.call_args[0][0]
        self.assertTrue(any(f"--source={source_dir}" in arg for arg in call_args))

    @patch("subprocess.run")
    def test_run_tests_failure(self, mock_run):
        """Test handling of test failures"""
        test_dir = self.tmp_path / "tests"
        test_dir.mkdir()

        mock_run.return_value = Mock(returncode=1)

        checker = CodeCoverageChecker(
            test_dir=str(test_dir),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )
        checker.detected_framework = "pytest"

        self.assertFalse(checker._run_tests())#pylint: disable=protected-access


class TestCoverageAnalysis(TestCase):
    """Tests for coverage analysis"""

    def setUp(self):
        """Set up temporary directory and checker for tests"""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)
        self.checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.remove")
    def test_analyze_coverage_success(self, mock_remove, mock_file, mock_run):
        """Test successful coverage analysis"""
        coverage_data = {"totals": {"percent_covered": 85.5}, "files": {}}

        mock_file.return_value.read.return_value = json.dumps(coverage_data)
        mock_run.return_value = Mock(returncode=0)

        result = self.checker._analyze_coverage()#pylint: disable=protected-access

        self.assertEqual(result, coverage_data)
        mock_run.assert_called_once()
        mock_remove.assert_called_once_with("coverage.json")

    @patch("subprocess.run")
    def test_analyze_coverage_generation_fails(self, mock_run):
        """Test handling when coverage report generation fails"""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "coverage", stderr=b"Generation failed"
        )

        self.assertIsNone(self.checker._analyze_coverage())#pylint: disable=protected-access

    @patch("subprocess.run")
    def test_analyze_coverage_read_fails(self, mock_run):
        """Test handling when reading coverage report fails"""
        mock_run.return_value = Mock(returncode=0)

        self.assertIsNone(self.checker._analyze_coverage())#pylint: disable=protected-access


class TestThresholdValidation(TestCase):
    """Tests for coverage threshold validation"""

    def setUp(self):
        """Set up temporary directory for tests"""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_validate_threshold_above(self):
        """Test validation with coverage above threshold"""
        coverage_data = CoverageData(
            totals=CoverageTotals(percent_covered=85.0),
            files={})

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertEqual(checker._validate_threshold(coverage_data), 0)#pylint: disable=protected-access

    def test_validate_threshold_exact(self):
        """Test validation with coverage exactly at threshold"""
        coverage_data = CoverageData(
            totals=CoverageTotals(percent_covered=80.0),
            files={})

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertEqual(checker._validate_threshold(coverage_data), 0)#pylint: disable=protected-access

    def test_validate_threshold_below(self):
        """Test validation with coverage below threshold"""
        coverage_data = CoverageData(
            totals=CoverageTotals(percent_covered=55.0),
            files={
                "src/module1.py": {
                    "summary": {"percent_covered": 45.0},
                    "missing_lines": [10, 11, 12, 20],
                }
            })
        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=60.0,
            framework="pytest",
        )

        self.assertEqual(checker._validate_threshold(coverage_data), 1)#pylint: disable=protected-access


class TestHelperMethods(TestCase):
    """Tests for helper methods"""

    def setUp(self):
        """Set up checker for tests"""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)
        self.checker = CodeCoverageChecker(
            test_dir="tests",
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_group_consecutive_lines_empty(self):
        """Test grouping empty list"""
        self.assertEqual(self.checker._group_consecutive_lines([]), "")#pylint: disable=protected-access

    def test_group_consecutive_lines_single(self):
        """Test grouping single line"""
        self.assertEqual(self.checker._group_consecutive_lines([5]), "5")#pylint: disable=protected-access

    def test_group_consecutive_lines_consecutive(self):
        """Test grouping consecutive lines"""
        self.assertEqual(self.checker._group_consecutive_lines([1, 2, 3, 4, 5]), "1-5")#pylint: disable=protected-access

    def test_group_consecutive_lines_mixed(self):
        """Test grouping mixed consecutive and non-consecutive lines"""
        self.assertEqual(
            self.checker._group_consecutive_lines([1, 2, 3, 7, 8, 10, 15, 16, 17]),#pylint: disable=protected-access
            "1-3, 7-8, 10, 15-17",
        )

    def test_group_consecutive_lines_unsorted(self):
        """Test grouping unsorted input"""
        self.assertEqual(
            self.checker._group_consecutive_lines([10, 2, 3, 1, 8, 7]), "1-3, 7-8, 10"#pylint: disable=protected-access
        )


class TestMainFunction(TestCase):
    """Tests for main function"""

    @patch("pre_commit_hooks.coverage_checks.CodeCoverageChecker")
    @patch("sys.argv", ["coverage_checks.py"])
    def test_main_default_arguments(self, mock_checker_class):
        """Test main with default arguments"""
        mock_instance = Mock()
        mock_instance.run.return_value = 0
        mock_checker_class.return_value = mock_instance

        self.assertEqual(main(), 0)
        mock_checker_class.assert_called_once()

    @patch("pre_commit_hooks.coverage_checks.CodeCoverageChecker")
    @patch(
        "sys.argv",
        [
            "coverage_checks.py",
            "--test-dir",
            "my_tests",
            "--source-dir",
            "my_src",
            "--threshold",
            "75",
            "--framework",
            "pytest",
        ],
    )
    def test_main_custom_arguments(self, mock_checker_class):
        """Test main with custom arguments"""
        mock_instance = Mock()
        mock_instance.run.return_value = 0
        mock_checker_class.return_value = mock_instance

        self.assertEqual(main(), 0)

        call_kwargs = mock_checker_class.call_args[1]
        self.assertEqual(call_kwargs["test_dir"], "my_tests")
        self.assertEqual(call_kwargs["source_dir"], "my_src")
        self.assertEqual(call_kwargs["threshold"], 75.0)
        self.assertEqual(call_kwargs["framework"], "pytest")

    @patch("sys.argv", ["coverage_checks.py", "--threshold", "150"])
    def test_main_invalid_threshold_high(self):
        """Test main with threshold value too high"""
        self.assertEqual(main(), 1)

    @patch("sys.argv", ["coverage_checks.py", "--threshold", "-10"])
    def test_main_invalid_threshold_negative(self):
        """Test main with negative threshold value"""
        self.assertEqual(main(), 1)


class TestRunMethod(TestCase):
    """Tests for the main run method"""

    def setUp(self):
        """Set up temporary directory for tests"""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    @patch.object(CodeCoverageChecker, "_setup_venv")
    def test_run_failure_setup_venv(self, mock_venv):
        """Test run method when venv setup fails"""
        mock_venv.return_value = False

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertEqual(checker.run(), 1)

    @patch.object(CodeCoverageChecker, "_setup_framework")
    @patch.object(CodeCoverageChecker, "_setup_venv")
    def test_run_failure_setup_framework(
        self, mock_venv, mock_framework):
        """Test run method when framework setup fails"""
        mock_venv.return_value = True
        mock_framework.return_value = False

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertEqual(checker.run(), 1)

    @patch.object(CodeCoverageChecker, "_run_tests")
    @patch.object(CodeCoverageChecker, "_setup_framework")
    @patch.object(CodeCoverageChecker, "_setup_venv")
    def test_run_failure_run_tests(
        self, mock_venv, mock_framework, mock_tests):
        """Test run method when running tests fails"""
        mock_venv.return_value = True
        mock_framework.return_value = True
        mock_tests.return_value = False

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertEqual(checker.run(), 1)

    @patch.object(CodeCoverageChecker, "_analyze_coverage")
    @patch.object(CodeCoverageChecker, "_run_tests")
    @patch.object(CodeCoverageChecker, "_setup_framework")
    @patch.object(CodeCoverageChecker, "_setup_venv")
    def test_run_failure_analyze_coverage(
        self, mock_venv, mock_framework, mock_tests, mock_analyze):
        """Test run method when coverage analysis fails"""
        mock_venv.return_value = True
        mock_framework.return_value = True
        mock_tests.return_value = True
        mock_analyze.return_value = None

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertEqual(checker.run(), 1)

    @patch.object(CodeCoverageChecker, "_validate_threshold")
    @patch.object(CodeCoverageChecker, "_analyze_coverage")
    @patch.object(CodeCoverageChecker, "_run_tests")
    @patch.object(CodeCoverageChecker, "_setup_framework")
    @patch.object(CodeCoverageChecker, "_setup_venv")
    def test_run_success( #pylint: disable=too-many-positional-arguments,too-many-arguments
        self, mock_venv, mock_framework, mock_tests, mock_analyze, mock_validate
    ):
        """Test successful run"""
        mock_venv.return_value = True
        mock_framework.return_value = True
        mock_tests.return_value = True
        mock_analyze.return_value = {"totals": {"percent_covered": 85.0}}
        mock_validate.return_value = 0

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertEqual(checker.run(), 0)

    @patch.object(CodeCoverageChecker, "_setup_venv")
    def test_run_keyboard_interrupt(self, mock_setup_venv):
        """Test run handles KeyboardInterrupt"""
        mock_setup_venv.side_effect = KeyboardInterrupt("Error")

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        self.assertEqual(checker.run(), 1)

    @patch.object(CodeCoverageChecker, "_setup_venv")
    def test_run_runtime_error(self, mock_setup_venv):
        """Test run handles RuntimeError"""
        mock_setup_venv.side_effect = RuntimeError("Error")

        checker = CodeCoverageChecker(
            test_dir=str(self.tmp_path / "tests"),
            source_dir="",
            venv_path=str(self.tmp_path / "venv"),
            threshold=80.0,
            framework="pytest",
        )

        with self.assertRaises(HookException):
            checker.run()
