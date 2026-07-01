#!/usr/bin/env python
"""Check the commit message matches one of the semantic release tags"""

import sys
from sys import argv as positional_arguments
import re
from typing import Pattern
from pre_commit_hooks.hook_utils import HookException
from pre_commit_hooks.precommit import pre_commit_exception_handler

VERSION_NUMBER = "2.0.0"
TITLE = "Commit Message Check"
# Argument handling
SEMANTIC_RELEASE_REGEX = r"(chore|test|feat|fix|build|docs|refactor|bump|major): .*"

USAGE = """
Semantic Release Options:
build:    Build script changes/updates
bump:     Bumping a dependency version of the latest release
chore:    updating grunt tasks
docs:     Changes to the documentation
feat:     New feature
fix:      Bug fix
major:    Major change to code base
refactor: Refactoring of code
style:    Formatting, missing semi colons, etc (no production code change)
test:     Creating/Updating tests, refactoring tests (no production code change)
"""


class CommitMessageChecker:
    """Check the commit message matches one of the semantic release tags"""

    def __init__(self, commit_message_file: str) -> None:
        self.semantic_release: Pattern[str] = re.compile(SEMANTIC_RELEASE_REGEX)
        with open(commit_message_file, "r", encoding="utf-8") as cf:
            self.commit_message: str = cf.read()

    def check_commit(self) -> None:
        """Check the commit message matches"""
        message_match = self.semantic_release.findall(self.commit_message)
        if len(message_match) != 1:
            raise HookException(
                f"Semantic Release tag was not found in the commit message: {self.commit_message}",
                USAGE,
            )

    @pre_commit_exception_handler
    def run(self) -> int:
        """ Run the check and return 0 exit code"""
        self.check_commit()
        return 0

def main() -> int:
    """Main entry point for the commit message checker"""
    return CommitMessageChecker(positional_arguments[-1]).run()

if __name__ == "__main__":
    sys.exit(main())
