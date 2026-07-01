"""Unit Tests for the commit message hook"""

import unittest
from unittest.mock import patch, call
from pre_commit_hooks.hook_utils import HookException, TerminalOutput


class TestHookException(unittest.TestCase):
    """Unit tests for the HookException class"""

    def test_raise_hook_exception(self):
        """Test that exception raised results in expected format message"""
        exception = HookException("error_message", "error details")
        self.assertEqual(str(exception), "error_message\nerror details")


class TestTerminalOutput(unittest.TestCase):
    """Unit tests for the TerminaOutput class"""

    @patch("builtins.print")
    def test_terminal_output_red_colour(self, mock_print):
        """Test that output contains colour code for red text"""
        text = "I am red text"
        output = TerminalOutput.of()
        output.red(text)
        self.assertEqual(
            mock_print.mock_calls, [call(f"{output.COLORS["red"]}{text}{output.RESET}")]
        )

    @patch("builtins.print")
    def test_terminal_output_default_colour(self, mock_print):
        """Test that output contains colour code for red text"""
        text = "I am red text"
        output = TerminalOutput.of()
        output._output(text) #pylint: disable=protected-access
        self.assertEqual(mock_print.mock_calls, [call(f"{text}")])

    @patch("builtins.print")
    def test_terminal_output_black_bold_colour(self, mock_print):
        """Test that output contains colour code for red text"""
        text = "I am black bold text"
        output = TerminalOutput.of()
        output.blue().bold(text)
        self.assertEqual(mock_print.mock_calls,[call(
            f"{output.COLORS["blue"]}{output.STYLES["bold"]}{text}{output.RESET}")])

    @patch("builtins.print")
    def test_terminal_output_multiple_styles_and_colour(self, mock_print):
        """Test that output contains colour code for red text"""
        text = "I am black bold text"
        output = TerminalOutput.of()
        output.green().italic().yellow().underline().magenta(text)
        self.assertEqual(mock_print.mock_calls,[call(
            f"{output.COLORS["green"]}{output.STYLES["italic"]}{output.COLORS["yellow"]}"
            + f"{output.STYLES["underline"]}{output.COLORS["magenta"]}{text}{output.RESET}")])

    @patch("builtins.print")
    def test_terminal_output_multiple_styles_and_colour_in_string(self, mock_print):
        """Test that output contains colour code for red text"""
        first_text = "I am white text"
        second_text = "I am cyan text"
        output = TerminalOutput.of()
        output.underline().white(first_text).cyan(second_text)
        self.assertEqual(mock_print.mock_calls,[
            call(f"{output.STYLES["underline"]}{output.COLORS["white"]}{first_text}{output.RESET}"),
            call(f"{output.COLORS["cyan"]}{second_text}{output.RESET}")])
