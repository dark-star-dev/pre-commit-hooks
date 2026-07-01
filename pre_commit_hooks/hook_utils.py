"""Common utilities for pre-commit hooks"""
from typing import Optional

class HookException(Exception):
    """Exception raised by pre-commit hooks."""

    def __init__(self, message: str, details: str) -> None:
        super().__init__(message)
        self.details = details

    def __str__(self) -> str:
        return f"{super().__str__()}\n{self.details}"

class TerminalOutput():
    """An immutable formatter class for terminal output with color and style support."""

    # ANSI color codes
    COLORS = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }

    # ANSI style codes
    STYLES = {
        "bold": "\033[1m",
        "italic": "\033[3m",
        "underline": "\033[4m",
    }

    # Reset code
    RESET = "\033[0m"

    def __init__(self, styles: tuple[str, ...] = ()) -> None:
        self._styles: tuple[str, ...] = styles

    @staticmethod
    def of() -> "TerminalOutput":
        """Return the default instance of TerminalOutput."""
        return _DEFAULT_TERMINAL_OUTPUT  # pylint: disable=protected-access

    def _with_style(self, code: str) -> "TerminalOutput":
        """Create a new instance with an additional style."""
        return self.__class__((*self._styles, code))

    def _format(self, text: str) -> str:
        """Apply all accumulated styles to the text."""
        if not self._styles:
            return text
        return "".join(self._styles) + text + self.RESET

    # Color methods
    def red(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply red color."""
        new_instance = self._with_style(self.COLORS["red"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def green(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply green color."""
        new_instance = self._with_style(self.COLORS["green"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def yellow(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply yellow color."""
        new_instance = self._with_style(self.COLORS["yellow"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def blue(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply blue color."""
        new_instance = self._with_style(self.COLORS["blue"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def magenta(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply magenta color."""
        new_instance = self._with_style(self.COLORS["magenta"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def cyan(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply cyan color."""
        new_instance = self._with_style(self.COLORS["cyan"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def white(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply white color."""
        new_instance = self._with_style(self.COLORS["white"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    # Style methods
    def bold(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply bold style."""
        new_instance = self._with_style(self.STYLES["bold"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def italic(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply italic style."""
        new_instance = self._with_style(self.STYLES["italic"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def underline(self, text: Optional[str] = None) -> "TerminalOutput":
        """Apply underline style."""
        new_instance = self._with_style(self.STYLES["underline"])
        if text is not None:
            return new_instance._output(text) # pylint: disable=protected-access
        return new_instance

    def _output(self, text: str) -> "TerminalOutput":
        """Format and print the text."""
        print(self._format(str(text)))
        return TerminalOutput.of()  # pylint: disable=protected-access


# hidden singleton
_DEFAULT_TERMINAL_OUTPUT = TerminalOutput()
