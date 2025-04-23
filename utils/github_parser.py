"""
GitHub Command Parser
Provides robust parsing for GitHub commands in various formats
"""

import re
from typing import Tuple, Optional, Dict, Any

class GitHubCommandParser:
    """
    Parser for GitHub commands in various formats
    """

    def __init__(self):
        """Initialize the GitHub command parser"""
        # Patterns for different command formats
        self.repo_patterns = [
            # Standard format: github username/repo action
            r"github\s+(?P<user>[\w\-\.]+)/(?P<repo>[\w\-\.]+)\s+(?P<action>\w+)",

            # URL format: github.com/username/repo action
            r"github\.com/(?P<user>[\w\-\.]+)/(?P<repo>[\w\-\.]+).*?(?P<action>info|issues|commit)",

            # Natural language: Show info about github.com/username/repo
            r"(?:show|get|fetch|display).*?(?:information|info|details).*?github\.com/(?P<user>[\w\-\.]+)/(?P<repo>[\w\-\.]+)",

            # Natural language: Show username/repo issues
            r"(?:show|get|fetch|display).*?(?P<user>[\w\-\.]+)/(?P<repo>[\w\-\.]+).*?(?P<action>info|issues|commit)",

            # Action first: List issues for username/repo
            r"(?:list|show)\s+(?P<action>issues).*?(?P<user>[\w\-\.]+)/(?P<repo>[\w\-\.]+)",

            # Commit message: Generate commit for file in username/repo
            r"(?:generate|create).*?(?P<action>commit).*?(?P<user>[\w\-\.]+)/(?P<repo>[\w\-\.]+)"
        ]

        # Action mapping to standardize action names
        self.action_mapping = {
            "info": ["info", "information", "details", "about"],
            "issues": ["issues", "issue", "tickets", "bugs"],
            "commit": ["commit", "commits", "commit message", "commit msg"]
        }

    def parse_command(self, command: str) -> Optional[Dict[str, str]]:
        """
        Parse a GitHub command in various formats

        Args:
            command: The command to parse

        Returns:
            Dictionary with user, repo, and action, or None if not a valid GitHub command
        """
        command = command.lower().strip()

        # Try each pattern
        for pattern in self.repo_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                user = match.group('user')
                repo = match.group('repo')

                # Check if the pattern has an action group
                action = "info"  # Default action
                if 'action' in match.groupdict():
                    action = match.group('action')

                # Standardize the action
                action = self._standardize_action(action)

                # Check for file path in commit commands
                file_path = None
                if action == "commit":
                    file_match = re.search(r"(?:for|file|path)[:\s]+([^\s]+)", command, re.IGNORECASE)
                    if file_match:
                        file_path = file_match.group(1)

                result = {
                    "user": user,
                    "repo": repo,
                    "action": action
                }

                if file_path:
                    result["file_path"] = file_path

                return result

        return None

    def _standardize_action(self, action: str) -> str:
        """
        Standardize action names

        Args:
            action: The action to standardize

        Returns:
            Standardized action name
        """
        action = action.lower()

        for standard, variations in self.action_mapping.items():
            if action in variations:
                return standard

        return action

    def format_repo_url(self, user: str, repo: str) -> str:
        """
        Format a repository URL

        Args:
            user: GitHub username
            repo: Repository name

        Returns:
            Formatted repository URL
        """
        return f"https://github.com/{user}/{repo}"
