"""
GitHub integration for General Pulse
Provides functionality for working with GitHub repositories
"""

import os
import re
import json
import asyncio
import time
from datetime import datetime
import structlog
from dotenv import load_dotenv
from utils.github_parser import GitHubCommandParser
from utils.integration_error_handler import with_error_handling, handle_github_error, format_user_friendly_error, is_retryable_error

# Import PyGithub
try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

class GitHubSkills:
    """GitHub skills for General Pulse agent"""

    def __init__(self):
        """Initialize GitHub skills with authentication"""
        load_dotenv()
        self.logger = structlog.get_logger("github_skills")

        # Get GitHub token from environment
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_client = None

        # Initialize GitHub client if token is available
        if self.github_token and GITHUB_AVAILABLE:
            try:
                self.github_client = Github(self.github_token)
                self.user = self.github_client.get_user()
                self.username = self.user.login
                self.logger.info(f"GitHub client initialized for user: {self.username}")
            except Exception as e:
                self.logger.error(f"Error initializing GitHub client: {str(e)}")
        else:
            if not self.github_token:
                self.logger.warning("GitHub token not found in environment variables")
            if not GITHUB_AVAILABLE:
                self.logger.warning("PyGithub package not available")

    def _extract_repo_info(self, repo_url):
        """Extract owner and repo name from URL or owner/repo format"""
        # Use the GitHub command parser
        parser = GitHubCommandParser()

        # Try to parse as a command first
        parsed = parser.parse_command(f"github {repo_url} info")
        if parsed and "user" in parsed and "repo" in parsed:
            return parsed["user"], parsed["repo"]

        # Fall back to regex parsing
        # Extract from URL if it's a URL
        url_pattern = r'github\.com[:/]([^/]+)/([^/\.]+)'
        url_match = re.search(url_pattern, repo_url)
        if url_match:
            return url_match.group(1), url_match.group(2)

        # Extract from owner/repo format
        repo_pattern = r'^([^/]+)/([^/]+)$'
        repo_match = re.search(repo_pattern, repo_url)
        if repo_match:
            return repo_match.group(1), repo_match.group(2)

        return None, None

    @with_error_handling("github", "get_repository_info")
    async def get_repository_info_async(self, repo_url, max_retries=3):
        """
        Get information about a GitHub repository

        Args:
            repo_url: URL or owner/repo string for the repository
            max_retries: Maximum number of retries for retryable errors

        Returns:
            str: Repository information or error message
        """
        if not self.github_client:
            return {
                "success": False,
                "error_type": "configuration_error",
                "message": "GitHub client not initialized",
                "user_message": "GitHub integration is not available. Please check your GitHub token."
            }

        # Extract owner and repo name
        owner, repo_name = self._extract_repo_info(repo_url)
        if not owner or not repo_name:
            return {
                "success": False,
                "error_type": "invalid_input",
                "message": f"Invalid repository reference: {repo_url}",
                "user_message": f"Invalid repository reference: {repo_url}. Use format 'owner/repo' or a GitHub URL."
            }

        # Implement retry logic for retryable errors
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # Get the repo
                repo = await asyncio.to_thread(self.github_client.get_repo, f"{owner}/{repo_name}")

                # Get basic info
                stars = repo.stargazers_count
                forks = repo.forks_count
                issues = repo.open_issues_count
                created = repo.created_at.strftime("%Y-%m-%d")
                last_update = repo.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                description = repo.description or "No description"

                # Format the response
                info = f"Repository: {owner}/{repo_name}\n"
                info += f"Description: {description}\n"
                info += f"Stars: {stars} | Forks: {forks} | Open Issues: {issues}\n"
                info += f"Created: {created} | Last Updated: {last_update}\n"
                info += f"URL: {repo.html_url}"

                self.logger.info(f"Retrieved info for repository {owner}/{repo_name}")
                return {
                    "success": True,
                    "info": info,
                    "repository": {
                        "owner": owner,
                        "name": repo_name,
                        "stars": stars,
                        "forks": forks,
                        "issues": issues,
                        "created": created,
                        "updated": last_update,
                        "description": description,
                        "url": repo.html_url
                    }
                }

            except Exception as e:
                last_error = e
                error_dict = handle_github_error(e, "get_repository_info")

                # Check if the error is retryable
                if is_retryable_error(error_dict) and retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Exponential backoff
                    self.logger.info(f"Retrying get_repository_info ({retry_count}/{max_retries}) after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Not retryable or max retries reached
                    raise

        # This should not be reached due to the raise in the loop, but just in case
        if last_error:
            raise last_error
        return {"success": False, "error_type": "unknown_error", "message": "Unknown error occurred"}

    @with_error_handling("github", "list_repository_issues")
    async def list_repository_issues_async(self, repo_url, state="open", limit=5, max_retries=3):
        """
        List issues for a GitHub repository

        Args:
            repo_url: URL or owner/repo string for the repository
            state: Issue state (open, closed, all)
            limit: Maximum number of issues to return
            max_retries: Maximum number of retries for retryable errors

        Returns:
            dict: Dictionary with issues information or error details
        """
        if not self.github_client:
            return {
                "success": False,
                "error_type": "configuration_error",
                "message": "GitHub client not initialized",
                "user_message": "GitHub integration is not available. Please check your GitHub token."
            }

        # Extract owner and repo name
        owner, repo_name = self._extract_repo_info(repo_url)
        if not owner or not repo_name:
            return {
                "success": False,
                "error_type": "invalid_input",
                "message": f"Invalid repository reference: {repo_url}",
                "user_message": f"Invalid repository reference: {repo_url}. Use format 'owner/repo' or a GitHub URL."
            }

        # Implement retry logic for retryable errors
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # Get the repo
                repo = await asyncio.to_thread(self.github_client.get_repo, f"{owner}/{repo_name}")

                # Get issues
                issues = await asyncio.to_thread(repo.get_issues, state=state)

                # Format the response
                response = f"Issues for {owner}/{repo_name} ({state}):\n\n"

                # Process issues asynchronously
                async def process_issue(issue):
                    created = issue.created_at.strftime("%Y-%m-%d")
                    labels = ", ".join([label.name for label in issue.labels]) or "No labels"
                    return {
                        "number": issue.number,
                        "title": issue.title,
                        "created": created,
                        "labels": [label.name for label in issue.labels],
                        "url": issue.html_url,
                        "formatted": f"#{issue.number}: {issue.title}\n  Created: {created} | Labels: {labels}\n  URL: {issue.html_url}\n"
                    }

                # Convert issues iterator to list to work with it asynchronously
                issues_list = list(issues[:limit])

                # Process all issues concurrently
                tasks = [process_issue(issue) for issue in issues_list]
                issue_data = await asyncio.gather(*tasks)

                # Format the text response
                if not issue_data:
                    response += "No issues found."
                else:
                    response += "\n".join([issue["formatted"] for issue in issue_data])

                self.logger.info(f"Retrieved {len(issue_data)} issues for repository {owner}/{repo_name}")

                return {
                    "success": True,
                    "formatted_response": response,
                    "issues": issue_data,
                    "repository": {
                        "owner": owner,
                        "name": repo_name,
                        "state": state,
                        "issue_count": len(issue_data)
                    }
                }

            except Exception as e:
                last_error = e
                error_dict = handle_github_error(e, "list_repository_issues")

                # Check if the error is retryable
                if is_retryable_error(error_dict) and retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Exponential backoff
                    self.logger.info(f"Retrying list_repository_issues ({retry_count}/{max_retries}) after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Not retryable or max retries reached
                    raise

        # This should not be reached due to the raise in the loop, but just in case
        if last_error:
            raise last_error
        return {"success": False, "error_type": "unknown_error", "message": "Unknown error occurred"}

    @with_error_handling("github", "create_repository")
    async def create_repository_async(self, name, description=None, private=False, max_retries=3):
        """
        Create a new GitHub repository

        Args:
            name: Name of the new repository
            description: Optional description
            private: Whether the repository should be private
            max_retries: Maximum number of retries for retryable errors

        Returns:
            dict: Dictionary with repository information or error details
        """
        if not self.github_client:
            return {
                "success": False,
                "error_type": "configuration_error",
                "message": "GitHub client not initialized",
                "user_message": "GitHub integration is not available. Please check your GitHub token."
            }

        # Implement retry logic for retryable errors
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # Create the repository
                repo = await asyncio.to_thread(
                    self.user.create_repo,
                    name,
                    description=description,
                    private=private
                )

                self.logger.info(f"Created new repository: {repo.full_name}")

                return {
                    "success": True,
                    "message": f"Repository created: {repo.html_url}",
                    "repository": {
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "url": repo.html_url,
                        "description": repo.description,
                        "private": repo.private,
                        "created_at": repo.created_at.isoformat() if repo.created_at else None
                    }
                }

            except Exception as e:
                last_error = e
                error_dict = handle_github_error(e, "create_repository")

                # Check if the error is retryable
                if is_retryable_error(error_dict) and retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Exponential backoff
                    self.logger.info(f"Retrying create_repository ({retry_count}/{max_retries}) after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Not retryable or max retries reached
                    raise

        # This should not be reached due to the raise in the loop, but just in case
        if last_error:
            raise last_error
        return {"success": False, "error_type": "unknown_error", "message": "Unknown error occurred"}

    async def _generate_commit_message(self, owner, repo_name, file_path, content, model_interface):
        """
        Generate a commit message for a file using AI

        Args:
            owner: Repository owner
            repo_name: Repository name
            file_path: Path to the file
            content: File content
            model_interface: ModelInterface instance

        Returns:
            str: Generated commit message
        """
        # Generate commit message using AI
        prompt = f"""
        Generate a clear and concise commit message for the following file:

        Repository: {owner}/{repo_name}
        File: {file_path}

        First few lines of the file:
        {content[:500]}...

        Write a commit message that follows best practices:
        1. Start with a short imperative summary line (max 50 chars)
        2. Optionally add a more detailed explanation after a blank line
        3. Focus on WHY the change was made, not HOW
        4. Be specific and clear

        COMMIT MESSAGE:
        """

        # Call the model
        response = await model_interface.call_model_api_async("claude", prompt)

        if not response or "error" in response:
            return None

        commit_message = response.get("content", "").strip()
        return commit_message

    @with_error_handling("github", "generate_commit_message")
    async def generate_commit_message_async(self, repo_url, file_path, model_interface=None, max_retries=3):
        """
        Generate a commit message for changes in a file

        Args:
            repo_url: URL or owner/repo string for the repository
            file_path: Path to the file in the repository
            model_interface: Optional ModelInterface instance for AI model calls
            max_retries: Maximum number of retries for retryable errors

        Returns:
            dict: Dictionary with commit message or error details
        """
        if not self.github_client:
            return {
                "success": False,
                "error_type": "configuration_error",
                "message": "GitHub client not initialized",
                "user_message": "GitHub integration is not available. Please check your GitHub token."
            }

        if not model_interface:
            # Import here to avoid circular imports
            from skills.optimized_model_interface import OptimizedModelInterface
            model_interface = OptimizedModelInterface()

        # Extract owner and repo name
        owner, repo_name = self._extract_repo_info(repo_url)
        if not owner or not repo_name:
            return {
                "success": False,
                "error_type": "invalid_input",
                "message": f"Invalid repository reference: {repo_url}",
                "user_message": f"Invalid repository reference: {repo_url}. Use format 'owner/repo' or a GitHub URL."
            }

        # Implement retry logic for retryable errors
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # Get the repo
                repo = await asyncio.to_thread(self.github_client.get_repo, f"{owner}/{repo_name}")

                # Try to get the file content
                try:
                    file_content = await asyncio.to_thread(repo.get_contents, file_path)
                    content = file_content.decoded_content.decode('utf-8')
                except Exception as file_error:
                    return {
                        "success": False,
                        "error_type": "file_access_error",
                        "message": f"Could not access file {file_path}: {str(file_error)}",
                        "user_message": f"Could not access file {file_path}. Please check if the file exists and you have permission to access it."
                    }

                # Generate commit message using AI
                commit_message = await self._generate_commit_message(owner, repo_name, file_path, content, model_interface)

                if not commit_message:
                    return {
                        "success": False,
                        "error_type": "ai_generation_error",
                        "message": "Failed to generate commit message using AI",
                        "user_message": "Failed to generate commit message using AI. Please try again later."
                    }

                # Clean up the output
                commit_message = re.sub(r'^COMMIT MESSAGE:\s*', '', commit_message, flags=re.IGNORECASE)
                commit_message = re.sub(r'^```\s*', '', commit_message)
                commit_message = re.sub(r'\s*```$', '', commit_message)

                self.logger.info(f"Generated commit message for {file_path} in {owner}/{repo_name}")

                return {
                    "success": True,
                    "commit_message": commit_message,
                    "formatted_response": f"Suggested commit message:\n\n{commit_message}",
                    "repository": {
                        "owner": owner,
                        "name": repo_name,
                        "file_path": file_path
                    }
                }

            except Exception as e:
                last_error = e
                error_dict = handle_github_error(e, "generate_commit_message")

                # Check if the error is retryable
                if is_retryable_error(error_dict) and retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # Exponential backoff
                    self.logger.info(f"Retrying generate_commit_message ({retry_count}/{max_retries}) after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Not retryable or max retries reached
                    raise

        # This should not be reached due to the raise in the loop, but just in case
        if last_error:
            raise last_error
        return {"success": False, "error_type": "unknown_error", "message": "Unknown error occurred"}