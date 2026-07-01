"""Unit Tests for the commit message hook"""

import unittest
from unittest.mock import patch , mock_open
from pre_commit_hooks.commit_msg import CommitMessageChecker
from pre_commit_hooks.hook_utils import HookException


class TestCommitMsg(unittest.TestCase):
    """Unit Tests for the commit message hook"""

    def test_valid_commit_msg(self):
        """Test a valid commit message"""
        with patch("builtins.open",
                   mock_open(read_data="feat: Add new functionality")) as mock_file:
            checker = CommitMessageChecker(mock_file)
            self.assertIsNone(checker.check_commit())

    def test_invalid_commit_msg(self):
        """Test a invalid commit message reutnrs error"""
        with patch("builtins.open",  mock_open(read_data="Add new functionality")) as mock_file:
            checker = CommitMessageChecker(mock_file)
            with self.assertRaises(HookException) as ex:
                checker.check_commit()
            self.assertIn("Semantic Release tag was not found in the commit message:",
                str(ex.exception))
