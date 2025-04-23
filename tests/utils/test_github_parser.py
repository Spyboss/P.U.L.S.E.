"""
Unit tests for GitHub command parser
"""

import unittest
from utils.github_parser import GitHubCommandParser

class TestGitHubCommandParser(unittest.TestCase):
    """Test cases for GitHubCommandParser"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = GitHubCommandParser()

    def test_standard_format(self):
        """Test standard format: github username/repo action"""
        result = self.parser.parse_command("github octocat/Hello-World info")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "info")

    def test_url_format(self):
        """Test URL format: github.com/username/repo action"""
        result = self.parser.parse_command("github.com/octocat/Hello-World info")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "info")

    def test_natural_language(self):
        """Test natural language: Show info about github.com/username/repo"""
        result = self.parser.parse_command("Show info about github.com/octocat/Hello-World")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "info")

    def test_natural_language_username_repo(self):
        """Test natural language: Show username/repo issues"""
        result = self.parser.parse_command("Show octocat/Hello-World issues")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "issues")

    def test_action_first(self):
        """Test action first: List issues for username/repo"""
        result = self.parser.parse_command("List issues for octocat/Hello-World")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "issues")

    def test_commit_message(self):
        """Test commit message: Generate commit for file in username/repo"""
        result = self.parser.parse_command("Generate commit message for README.md in octocat/Hello-World")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "commit")
        self.assertEqual(result.get("file_path").lower(), "readme.md")

    def test_invalid_command(self):
        """Test invalid command"""
        result = self.parser.parse_command("This is not a GitHub command")
        self.assertIsNone(result)

    def test_standardize_action(self):
        """Test action standardization"""
        self.assertEqual(self.parser._standardize_action("info"), "info")
        self.assertEqual(self.parser._standardize_action("information"), "info")
        self.assertEqual(self.parser._standardize_action("details"), "info")
        self.assertEqual(self.parser._standardize_action("issues"), "issues")
        self.assertEqual(self.parser._standardize_action("issue"), "issues")
        self.assertEqual(self.parser._standardize_action("commit"), "commit")
        self.assertEqual(self.parser._standardize_action("commit message"), "commit")

    def test_format_repo_url(self):
        """Test repository URL formatting"""
        url = self.parser.format_repo_url("octocat", "Hello-World")
        self.assertEqual(url, "https://github.com/octocat/Hello-World")

if __name__ == "__main__":
    unittest.main()
