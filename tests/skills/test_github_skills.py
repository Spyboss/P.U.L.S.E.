"""
Unit tests for GitHub skills
"""

import unittest
import asyncio
import os
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime
from utils.github_parser import GitHubCommandParser
from utils.integration_error_handler import handle_github_error, is_retryable_error

# Create a mock for the GitHub module
class MockGitHub:
    def __init__(self, *args, **kwargs):
        pass

    def get_repo(self, repo_name):
        if repo_name == "octocat/Hello-World":
            return MockRepo(repo_name)
        else:
            raise Exception("404 {\"message\": \"Not Found\"}")

    def get_user(self, username=None):
        return MockUser("octocat")

class MockRepo:
    def __init__(self, full_name):
        self.full_name = full_name
        self.description = "This is a test repository"
        self.html_url = f"https://github.com/{full_name}"
        self.stargazers_count = 100
        self.forks_count = 50
        self.open_issues_count = 10
        self.language = "Python"
        self.created_at = "2022-01-01T00:00:00Z"
        self.updated_at = "2022-01-02T00:00:00Z"
        self.owner = MockUser("octocat")

    def get_issues(self, state="open"):
        return [MockIssue(i) for i in range(1, 6)]

    def get_contents(self, path):
        return MockContent(path)

class MockUser:
    def __init__(self, login):
        self.login = login
        self.avatar_url = f"https://github.com/{login}.png"

class MockIssue:
    def __init__(self, number):
        self.number = number
        self.title = f"Test Issue {number}"
        self.html_url = f"https://github.com/octocat/Hello-World/issues/{number}"
        self.created_at = "2022-01-01T00:00:00Z"
        self.updated_at = "2022-01-02T00:00:00Z"
        self.state = "open"
        self.user = MockUser(f"user{number}")

class MockContent:
    def __init__(self, path):
        self.path = path
        self.decoded_content = b"print('Hello, World!')"

# Now we can import and test the GitHub skills
with patch('github.Github', MockGitHub):
    from skills.github_skills import GitHubSkills

class TestGitHubSkills(unittest.TestCase):
    """Test cases for GitHub skills"""

    def setUp(self):
        """Set up test environment"""
        # Create a test instance with a mock token
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            self.github_skills = GitHubSkills()

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_get_repository_info_async_success(self, mock_sleep):
        """Test getting repository info successfully"""
        # Create a mock repository with the expected data
        mock_repo = MagicMock()
        mock_repo.stargazers_count = 100
        mock_repo.forks_count = 50
        mock_repo.open_issues_count = 10
        mock_repo.created_at = datetime(2022, 1, 1)
        mock_repo.updated_at = datetime(2022, 1, 2, 12, 0, 0)
        mock_repo.description = "This is a test repository"
        mock_repo.html_url = "https://github.com/octocat/Hello-World"

        # Mock the asyncio.to_thread call to return our mock repo
        with patch('asyncio.to_thread', return_value=mock_repo):
            # Run the test
            result = asyncio.run(self.github_skills.get_repository_info_async("octocat/Hello-World"))

            # Check the result
            self.assertTrue(result["success"])
            self.assertIn("repository", result)
            self.assertEqual(result["repository"]["owner"], "octocat")
            self.assertEqual(result["repository"]["name"].lower(), "hello-world")  # Case-insensitive comparison
            self.assertEqual(result["repository"]["stars"], 100)
            self.assertEqual(result["repository"]["forks"], 50)
            self.assertEqual(result["repository"]["issues"], 10)

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_get_repository_info_async_not_found(self, mock_sleep):
        """Test getting repository info for non-existent repo"""
        # Create a mock error with 404 status
        error = MagicMock()
        error.status = 404
        error.__str__.return_value = "Not Found"

        # Override the MockGitHub.get_repo method to raise a 404 error
        with patch.object(self.github_skills, 'github_client') as mock_client:
            mock_client.get_repo.side_effect = error

            # Run the test
            result = asyncio.run(self.github_skills.get_repository_info_async("nonexistent/repo"))

            # Check the result
            self.assertFalse(result["success"])
            self.assertEqual(result["error_type"], "github_error")
            self.assertEqual(result["status_code"], 404)
            self.assertIn("not found", result["user_message"].lower())

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_list_repository_issues_async_success(self, mock_sleep):
        """Test listing repository issues successfully"""
        # Create a mock repository
        mock_repo = MagicMock()

        # Create mock issues
        mock_issue1 = MagicMock()
        mock_issue1.number = 1
        mock_issue1.title = "Test Issue 1"
        mock_issue1.created_at = datetime(2022, 1, 1)
        mock_issue1.labels = [MagicMock(name="bug"), MagicMock(name="high-priority")]
        mock_issue1.html_url = "https://github.com/octocat/Hello-World/issues/1"

        mock_issue2 = MagicMock()
        mock_issue2.number = 2
        mock_issue2.title = "Test Issue 2"
        mock_issue2.created_at = datetime(2022, 1, 2)
        mock_issue2.labels = [MagicMock(name="enhancement")]
        mock_issue2.html_url = "https://github.com/octocat/Hello-World/issues/2"

        # Override the GitHub client methods
        with patch.object(self.github_skills, 'github_client') as mock_client:
            # Set up the mock repo
            mock_client.get_repo.return_value = mock_repo
            # Set up the mock repo to return our issues
            mock_repo.get_issues.return_value = [mock_issue1, mock_issue2]

            # Run the test
            result = asyncio.run(self.github_skills.list_repository_issues_async("octocat/Hello-World"))

            # Check the result
            self.assertTrue(result["success"])
            self.assertIn("issues", result)
            self.assertEqual(len(result["issues"]), 2)
            self.assertEqual(result["issues"][0]["number"], 1)
            self.assertEqual(result["issues"][0]["title"], "Test Issue 1")
            self.assertEqual(result["issues"][0]["labels"], ["bug", "high-priority"])
            self.assertEqual(result["issues"][1]["number"], 2)
            self.assertEqual(result["issues"][1]["title"], "Test Issue 2")
            self.assertEqual(result["issues"][1]["labels"], ["enhancement"])

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_list_repository_issues_async_not_found(self, mock_sleep):
        """Test listing issues for non-existent repo"""
        # Create a mock error with 404 status
        error = MagicMock()
        error.status = 404
        error.__str__.return_value = "Not Found"

        # Override the GitHub client methods
        with patch.object(self.github_skills, 'github_client') as mock_client:
            # Set up the mock to raise an error
            mock_client.get_repo.side_effect = error

            # Run the test
            result = asyncio.run(self.github_skills.list_repository_issues_async("nonexistent/repo"))

            # Check the result
            self.assertFalse(result["success"])
            self.assertEqual(result["error_type"], "github_error")
            self.assertEqual(result["status_code"], 404)
            self.assertIn("not found", result["user_message"].lower())

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_generate_commit_message_async_success(self, mock_sleep):
        """Test generating commit message successfully"""
        # Create a mock repository and file content
        mock_repo = MagicMock()
        mock_file_content = MagicMock()
        mock_file_content.decoded_content = b"print('Hello, World!')"

        # Override the GitHub client methods
        with patch.object(self.github_skills, 'github_client') as mock_client:
            # Set up the mock repo
            mock_client.get_repo.return_value = mock_repo
            # Set up the mock repo to return our file content
            mock_repo.get_contents.return_value = mock_file_content

            # Mock the _generate_commit_message method
            with patch.object(self.github_skills, '_generate_commit_message', return_value="Add hello world script"):
                # Create a mock model interface
                mock_model_interface = MagicMock()

                # Run the test
                result = asyncio.run(self.github_skills.generate_commit_message_async(
                    "octocat/Hello-World",
                    "main.py",
                    mock_model_interface
                ))

                # Check the result
                self.assertTrue(result["success"])
                self.assertIn("commit_message", result)
                self.assertEqual(result["commit_message"], "Add hello world script")
                self.assertIn("repository", result)
                self.assertEqual(result["repository"]["owner"], "octocat")
                self.assertEqual(result["repository"]["name"].lower(), "hello-world")  # Case-insensitive comparison
                self.assertEqual(result["repository"]["file_path"], "main.py")

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_generate_commit_message_async_not_found(self, mock_sleep):
        """Test generating commit message for non-existent repo"""
        # Create a mock error with 404 status
        error = MagicMock()
        error.status = 404
        error.__str__.return_value = "Not Found"

        # Override the GitHub client methods
        with patch.object(self.github_skills, 'github_client') as mock_client:
            # Set up the mock to raise an error
            mock_client.get_repo.side_effect = error

            # Create a mock model interface
            mock_model_interface = MagicMock()

            # Run the test
            result = asyncio.run(self.github_skills.generate_commit_message_async(
                "nonexistent/repo",
                "main.py",
                mock_model_interface
            ))

            # Check the result
            self.assertFalse(result["success"])
            self.assertEqual(result["error_type"], "github_error")
            self.assertEqual(result["status_code"], 404)
            self.assertIn("not found", result["user_message"].lower())

    @patch('asyncio.sleep', return_value=None)  # Mock asyncio.sleep to avoid actual waiting
    def test_network_error_with_retry(self, mock_sleep):
        """Test handling a network error with retry"""
        # Create a mock repository for the successful retry
        mock_repo = MagicMock()
        mock_repo.stargazers_count = 100
        mock_repo.forks_count = 50
        mock_repo.open_issues_count = 10
        mock_repo.created_at = datetime(2022, 1, 1)
        mock_repo.updated_at = datetime(2022, 1, 2, 12, 0, 0)
        mock_repo.description = "This is a test repository"
        mock_repo.html_url = "https://github.com/octocat/Hello-World"

        # Create a network error for the first attempt
        network_error = ConnectionError("Connection refused")

        # Override the GitHub client methods
        with patch.object(self.github_skills, 'github_client') as mock_client:
            # Set up the mock to first raise an error, then succeed
            mock_client.get_repo.side_effect = [network_error, mock_repo]

            # Run the test
            result = asyncio.run(self.github_skills.get_repository_info_async("octocat/Hello-World"))

            # Check the result
            self.assertTrue(result["success"])
            self.assertIn("repository", result)
            self.assertEqual(result["repository"]["owner"], "octocat")
            self.assertEqual(result["repository"]["name"].lower(), "hello-world")  # Case-insensitive comparison

            # Verify that asyncio.sleep was called (for the retry)
            mock_sleep.assert_called_once()

    def test_is_retryable_error(self):
        """Test the is_retryable_error function with different error types"""
        # Network error should be retryable
        network_error = {
            "success": False,
            "error_type": "network_error",
            "message": "Connection refused"
        }
        self.assertTrue(is_retryable_error(network_error))

        # Rate limit error should be retryable
        rate_limit_error = {
            "success": False,
            "error_type": "github_error",
            "message": "API rate limit exceeded",
            "status_code": 403
        }
        self.assertTrue(is_retryable_error(rate_limit_error))

        # 404 error should not be retryable
        not_found_error = {
            "success": False,
            "error_type": "github_error",
            "message": "Not Found",
            "status_code": 404
        }
        self.assertFalse(is_retryable_error(not_found_error))


class TestGitHubParser(unittest.TestCase):
    """Test cases for GitHubCommandParser"""

    def setUp(self):
        """Set up test environment"""
        self.parser = GitHubCommandParser()

    def test_parse_command_standard_format(self):
        """Test parsing standard format: github username/repo action"""
        result = self.parser.parse_command("github octocat/Hello-World info")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "info")

    def test_parse_command_url_format(self):
        """Test parsing URL format: github.com/username/repo action"""
        result = self.parser.parse_command("github.com/octocat/Hello-World info")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "info")

    def test_parse_command_natural_language(self):
        """Test parsing natural language: Show info about github.com/username/repo"""
        result = self.parser.parse_command("Show info about github.com/octocat/Hello-World")
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "octocat")
        self.assertEqual(result["repo"].lower(), "hello-world")
        self.assertEqual(result["action"], "info")

if __name__ == '__main__':
    unittest.main()
