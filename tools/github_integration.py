"""
GitHub Integration Tool for General Pulse
Handles interaction with GitHub repositories
"""

import os
import requests
import json
from datetime import datetime
import yaml
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import logger, load_yaml_config, save_json_data, ensure_directory_exists
from skills.optimized_model_interface import OptimizedModelInterface

class GitHubIntegration:
    """Tool for interacting with GitHub repositories."""

    def __init__(self, config_path="configs/agent_config.yaml"):
        """Initialize GitHub integration with configuration."""
        self.config_path = config_path
        self.logger = logger
        self.logger.debug(f"GitHubIntegration initializing with config path: {config_path}")

        try:
            self.config = load_yaml_config(config_path)
            self.github_config = self.config.get('integrations', {}).get('github', {})
            self.enabled = self.github_config.get('enabled', False)
            self.token_env = self.github_config.get('token_env', 'GITHUB_TOKEN')
            self.token = os.environ.get(self.token_env)

            if self.enabled:
                self.logger.info("GitHub integration enabled")
                if not self.token:
                    self.logger.warning(f"GitHub token not found in environment variable: {self.token_env}")
            else:
                self.logger.info("GitHub integration disabled")
        except Exception as e:
            self.logger.error(f"Error initializing GitHub integration: {str(e)}", exc_info=True)
            self.config = {}
            self.github_config = {}
            self.enabled = False
            self.token_env = 'GITHUB_TOKEN'
            self.token = None

    def is_configured(self):
        """Check if GitHub integration is properly configured."""
        # Check for token first (most important)
        if not self.token:
            self.logger.warning("GitHub token not found. Please set GITHUB_TOKEN in your .env file.")
            return False

        # Check if enabled in config (less important, default to True if token exists)
        if not self.github_config:
            self.logger.warning("GitHub configuration not found in config file. Using default settings.")
            # If token exists but no config, assume enabled
            return True

        configured = self.enabled and self.token is not None
        self.logger.debug(f"GitHub integration configured: {configured}")
        return configured

    def get_repo_info(self, owner, repo):
        """Get information about a GitHub repository."""
        try:
            if not owner or not repo:
                self.logger.warning("Missing owner or repo name")
                return {"error": "Missing owner or repo name"}

            if not self.is_configured():
                self.logger.warning("GitHub integration not configured")
                return {"error": "GitHub integration not configured"}

            self.logger.info(f"Getting info for repository: {owner}/{repo}")

            # Use the real GitHub API
            url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}

            # Add request logging
            self.logger.debug(f"Sending request to: {url}")

            # Make the API call
            response = requests.get(url, headers=headers)

            # Check response status
            if response.status_code == 200:
                # Cache the successful response
                repo_data = response.json()
                self._cache_repo_info(owner, repo, repo_data)
                return repo_data
            else:
                self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return {"error": f"GitHub API error: {response.status_code}", "message": response.text}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error for {owner}/{repo}: {str(e)}", exc_info=True)

            # Try to use cached data if available
            cached_data = self._get_cached_repo_info(owner, repo)
            if cached_data:
                self.logger.info(f"Using cached data for {owner}/{repo}")
                cached_data["from_cache"] = True
                return cached_data

            return {"error": f"GitHub API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error getting repo info for {owner}/{repo}: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def _cache_repo_info(self, owner, repo, data):
        """Cache repository information to a local file."""
        try:
            storage_dir = "memory/github"
            os.makedirs(storage_dir, exist_ok=True)

            cache_file = os.path.join(storage_dir, f"{owner}_{repo}_info.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                data_to_cache = data.copy()
                data_to_cache["cache_time"] = datetime.now().isoformat()
                json.dump(data_to_cache, f, indent=2)

            self.logger.debug(f"Cached repo info for {owner}/{repo}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache repo info: {str(e)}", exc_info=True)
            return False

    def _get_cached_repo_info(self, owner, repo):
        """Retrieve cached repository information."""
        try:
            storage_dir = "memory/github"
            cache_file = os.path.join(storage_dir, f"{owner}_{repo}_info.json")

            if not os.path.exists(cache_file):
                return None

            # Check if cache is fresh (less than 1 hour old)
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.total_seconds() > 3600:  # 1 hour in seconds
                self.logger.debug(f"Cache for {owner}/{repo} is too old ({cache_age})")
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error retrieving cached repo info: {str(e)}", exc_info=True)
            return None

    def list_issues(self, owner, repo, state="open"):
        """List issues in a GitHub repository."""
        try:
            if not owner or not repo:
                self.logger.warning("Missing owner or repo name")
                return [{"error": "Missing owner or repo name"}]

            if not self.is_configured():
                self.logger.warning("GitHub integration not configured")
                return [{"error": "GitHub integration not configured"}]

            self.logger.info(f"Listing {state} issues for repository: {owner}/{repo}")

            # Validate state
            if state not in ["open", "closed", "all"]:
                self.logger.warning(f"Invalid issue state: {state}")
                state = "open"
                self.logger.info(f"Using default state: {state}")

            # Real API implementation
            url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}"
            headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}

            self.logger.debug(f"Sending request to: {url}")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                issues_data = response.json()
                # Cache the results
                self._cache_issues(owner, repo, state, issues_data)
                return issues_data
            else:
                self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return [{"error": f"GitHub API error: {response.status_code}", "message": response.text}]

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error for {owner}/{repo}: {str(e)}", exc_info=True)

            # Try to use cached data if available
            cached_data = self._get_cached_issues(owner, repo, state)
            if cached_data:
                self.logger.info(f"Using cached issues data for {owner}/{repo} with state {state}")
                for issue in cached_data:
                    issue["from_cache"] = True
                return cached_data

            return [{"error": f"GitHub API request failed: {str(e)}"}]
        except Exception as e:
            self.logger.error(f"Error listing issues for {owner}/{repo}: {str(e)}", exc_info=True)
            return [{"error": f"Error: {str(e)}"}]

    def _cache_issues(self, owner, repo, state, data):
        """Cache issues data to a local file."""
        try:
            storage_dir = "memory/github"
            os.makedirs(storage_dir, exist_ok=True)

            cache_file = os.path.join(storage_dir, f"{owner}_{repo}_issues_{state}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                data_to_cache = data.copy()
                json.dump(data_to_cache, f, indent=2)

            self.logger.debug(f"Cached issues for {owner}/{repo} with state {state}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache issues: {str(e)}", exc_info=True)
            return False

    def _get_cached_issues(self, owner, repo, state):
        """Retrieve cached issues data."""
        try:
            storage_dir = "memory/github"
            cache_file = os.path.join(storage_dir, f"{owner}_{repo}_issues_{state}.json")

            if not os.path.exists(cache_file):
                return None

            # Check if cache is fresh (less than 15 minutes old for issues)
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.total_seconds() > 900:  # 15 minutes in seconds
                self.logger.debug(f"Cache for {owner}/{repo} issues is too old ({cache_age})")
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error retrieving cached issues: {str(e)}", exc_info=True)
            return None

    def create_issue(self, owner, repo, title, body, labels=None):
        """Create a new issue in a GitHub repository."""
        try:
            if not owner or not repo:
                self.logger.warning("Missing owner or repo name")
                return {"error": "Missing owner or repo name"}

            if not title or not title.strip():
                self.logger.warning("Missing issue title")
                return {"error": "Issue title is required"}

            if not self.is_configured():
                self.logger.warning("GitHub integration not configured")
                return {"error": "GitHub integration not configured"}

            self.logger.info(f"Creating issue in repository {owner}/{repo}: {title}")

            # Real API implementation
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
            data = {"title": title, "body": body, "labels": labels or []}

            self.logger.debug(f"Sending request to: {url}")
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 201:
                issue_data = response.json()
                self.logger.info(f"Issue created successfully: #{issue_data.get('number')}")
                # Update the issues cache to include the new issue
                self._invalidate_issues_cache(owner, repo)
                return issue_data
            else:
                self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return {"error": f"GitHub API error: {response.status_code}", "message": response.text}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error creating issue: {str(e)}", exc_info=True)
            return {"error": f"GitHub API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error creating issue: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def _invalidate_issues_cache(self, owner, repo):
        """Invalidate cached issues for a repository."""
        try:
            storage_dir = "memory/github"
            for state in ["open", "closed", "all"]:
                cache_file = os.path.join(storage_dir, f"{owner}_{repo}_issues_{state}.json")
                if os.path.exists(cache_file):
                    self.logger.debug(f"Removing outdated issues cache for {owner}/{repo} state {state}")
                    os.remove(cache_file)
            return True
        except Exception as e:
            self.logger.error(f"Error invalidating issues cache: {str(e)}", exc_info=True)
            return False

    def get_rate_limit(self):
        """Get current GitHub API rate limit information."""
        try:
            if not self.is_configured():
                self.logger.warning("GitHub integration not configured")
                return {"error": "GitHub integration not configured"}

            self.logger.info("Checking GitHub API rate limit")

            # In a real implementation, this would make an API call
            # For example:
            # url = "https://api.github.com/rate_limit"
            # headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
            # response = requests.get(url, headers=headers)
            # if response.status_code == 200:
            #     return response.json()
            # else:
            #     self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
            #     return {"error": f"GitHub API error: {response.status_code}"}

            # For now, just return simulated data
            return {
                "resources": {
                    "core": {
                        "limit": 5000,
                        "used": 42,
                        "remaining": 4958,
                        "reset": int((datetime.now().timestamp() + 3600))
                    }
                }
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error checking rate limit: {str(e)}", exc_info=True)
            return {"error": f"GitHub API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def get_issue(self, owner, repo, issue_number):
        """Get details about a specific GitHub issue."""
        try:
            if not owner or not repo:
                self.logger.warning("Missing owner or repo name")
                return {"error": "Missing owner or repo name"}

            if not issue_number:
                self.logger.warning("Missing issue number")
                return {"error": "Issue number is required"}

            if not self.is_configured():
                self.logger.warning("GitHub integration not configured")
                return {"error": "GitHub integration not configured"}

            self.logger.info(f"Getting issue #{issue_number} from {owner}/{repo}")

            # Make the API request
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
            headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}

            self.logger.debug(f"Sending request to: {url}")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                issue_data = response.json()
                # Cache the result
                self._cache_issue(owner, repo, issue_number, issue_data)
                return issue_data
            elif response.status_code == 404:
                self.logger.warning(f"Issue #{issue_number} not found in {owner}/{repo}")
                return {"error": "Issue not found", "status_code": 404}
            else:
                self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return {"error": f"GitHub API error: {response.status_code}", "message": response.text}

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error getting issue: {str(e)}", exc_info=True)

            # Try to use cached data if available
            cached_data = self._get_cached_issue(owner, repo, issue_number)
            if cached_data:
                self.logger.info(f"Using cached data for issue #{issue_number}")
                cached_data["from_cache"] = True
                return cached_data

            return {"error": f"GitHub API request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error getting issue details: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def _cache_issue(self, owner, repo, issue_number, data):
        """Cache issue data to a local file."""
        try:
            storage_dir = "memory/github"
            os.makedirs(storage_dir, exist_ok=True)

            cache_file = os.path.join(storage_dir, f"{owner}_{repo}_issue_{issue_number}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                data_to_cache = data.copy()
                data_to_cache["cache_time"] = datetime.now().isoformat()
                json.dump(data_to_cache, f, indent=2)

            self.logger.debug(f"Cached issue #{issue_number} for {owner}/{repo}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache issue: {str(e)}", exc_info=True)
            return False

    def _get_cached_issue(self, owner, repo, issue_number):
        """Retrieve cached issue data."""
        try:
            storage_dir = "memory/github"
            cache_file = os.path.join(storage_dir, f"{owner}_{repo}_issue_{issue_number}.json")

            if not os.path.exists(cache_file):
                return None

            # Check if cache is fresh (less than 15 minutes old)
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.total_seconds() > 900:  # 15 minutes in seconds
                self.logger.debug(f"Cache for issue #{issue_number} is too old ({cache_age})")
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error retrieving cached issue: {str(e)}", exc_info=True)
            return None

    def get_file_content(self, owner, repo, path, ref="main"):
        """Get content of a file in a GitHub repository."""
        try:
            if not owner or not repo or not path:
                self.logger.warning("Missing owner, repo name, or file path")
                return {"error": "Missing required parameters"}

            if not self.is_configured():
                self.logger.warning("GitHub integration not configured")
                return {"error": "GitHub integration not configured"}

            self.logger.info(f"Getting file content for: {owner}/{repo}/{path} at {ref}")

            # Use the GitHub API
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            if ref:
                url += f"?ref={ref}"

            headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}

            self.logger.debug(f"Sending request to: {url}")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                content_data = response.json()

                # GitHub API returns base64 encoded content
                if "content" in content_data and content_data.get("encoding") == "base64":
                    import base64
                    content = base64.b64decode(content_data["content"]).decode("utf-8")
                    return {
                        "content": content,
                        "sha": content_data.get("sha"),
                        "path": content_data.get("path"),
                        "size": content_data.get("size")
                    }
                else:
                    self.logger.warning("File content not found in response")
                    return {"error": "File content not found in response"}
            else:
                self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return {"error": f"GitHub API error: {response.status_code}", "message": response.text}

        except Exception as e:
            self.logger.error(f"Error getting file content for {owner}/{repo}/{path}: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def get_commit_diff(self, owner, repo, commit_sha):
        """Get the diff for a specific commit."""
        try:
            if not owner or not repo or not commit_sha:
                self.logger.warning("Missing owner, repo name, or commit SHA")
                return {"error": "Missing required parameters"}

            if not self.is_configured():
                self.logger.warning("GitHub integration not configured")
                return {"error": "GitHub integration not configured"}

            self.logger.info(f"Getting diff for commit: {owner}/{repo}/{commit_sha}")

            # Use the GitHub API
            url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3.diff"  # Request diff format
            }

            self.logger.debug(f"Sending request to: {url}")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                # Response is the diff text
                return {
                    "diff": response.text,
                    "commit_sha": commit_sha
                }
            else:
                self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return {"error": f"GitHub API error: {response.status_code}", "message": response.text}

        except Exception as e:
            self.logger.error(f"Error getting diff for {owner}/{repo}/{commit_sha}: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def generate_commit_message(self, diff_text, files_changed=None, model="deepseek"):
        """Generate a commit message for changes using AI."""
        try:
            self.logger.info(f"Generating commit message using {model}")

            # Truncate diff if too large (to avoid token limits)
            max_diff_length = 3000
            if len(diff_text) > max_diff_length:
                truncated_diff = diff_text[:max_diff_length] + "\n...[diff truncated]..."
                self.logger.debug(f"Truncated diff from {len(diff_text)} to {len(truncated_diff)} characters")
                diff_text = truncated_diff

            # Create prompt for AI
            prompt = f"""Generate a concise, informative, and slightly snarky commit message based on these code changes.

Files changed: {files_changed if files_changed else 'Not specified'}

Diff:
```
{diff_text}
```

Your commit message should:
1. Be clear about what changed
2. Be 1-2 lines (max 72 chars per line)
3. Have a bit of personality/humor
4. Focus on the 'what' and 'why', not the 'how'

Format: Just return the commit message text, nothing else."""

            # Initialize the model interface
            model_interface = OptimizedModelInterface()

            # Call the AI model (using OpenRouter integration for DeepSeek or Claude)
            response = model_interface.call_model_api(model, prompt)

            if "error" in response:
                self.logger.warning(f"Error generating commit message: {response.get('error')}")
                return "Auto-generated commit via General Pulse"

            # Get the AI-generated commit message
            commit_message = response.get("response", "").strip()

            # Truncate if too long (GitHub has limits)
            if len(commit_message) > 72 * 2:  # 2 lines at 72 chars
                commit_message = commit_message[:140] + "..."

            self.logger.info(f"Generated commit message: {commit_message}")
            return commit_message

        except Exception as e:
            self.logger.error(f"Error generating commit message: {str(e)}", exc_info=True)
            return "Auto-generated commit via General Pulse"

    def commit_changes(self, owner, repo, branch, file_path, content, commit_message=None, sha=None):
        """Commit changes to a file in a GitHub repository."""
        try:
            if not owner or not repo or not branch or not file_path:
                self.logger.warning("Missing required parameters")
                return {"error": "Missing required parameters"}

            if not self.is_configured():
                self.logger.warning("GitHub integration not configured")
                return {"error": "GitHub integration not configured"}

            # If no commit message provided, generate one based on the changes
            if not commit_message:
                # First get the current content to compare
                current_file = self.get_file_content(owner, repo, file_path, branch)

                if "error" not in current_file:
                    # Generate a diff between current content and new content
                    import difflib
                    current_content = current_file.get("content", "")
                    diff = list(difflib.unified_diff(
                        current_content.splitlines(),
                        content.splitlines(),
                        fromfile=f"a/{file_path}",
                        tofile=f"b/{file_path}",
                        lineterm=""
                    ))
                    diff_text = "\n".join(diff)

                    # Generate commit message
                    commit_message = self.generate_commit_message(diff_text, file_path)
                else:
                    commit_message = "Add or update file via General Pulse"

            self.logger.info(f"Committing changes to {owner}/{repo}/{file_path} on {branch}")

            # Use the GitHub API
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}

            # Prepare request data
            import base64
            data = {
                "message": commit_message,
                "branch": branch,
                "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")
            }

            # If we have the file's SHA, it's an update; otherwise, it's a new file
            if sha:
                data["sha"] = sha

            self.logger.debug(f"Sending request to: {url}")
            response = requests.put(url, headers=headers, json=data)

            if response.status_code in (200, 201):
                result = response.json()
                self.logger.info(f"Successfully committed changes with message: {commit_message}")
                return {
                    "success": True,
                    "commit": result.get("commit", {}),
                    "content": result.get("content", {}),
                    "message": commit_message
                }
            else:
                self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return {"error": f"GitHub API error: {response.status_code}", "message": response.text}

        except Exception as e:
            self.logger.error(f"Error committing changes: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

# Global function for easier access from other modules
def is_github_configured():
    """External helper to check if GitHub integration is configured"""
    try:
        github = GitHubIntegration()
        return github.is_configured()
    except Exception as e:
        logger.error(f"Error checking GitHub configuration: {str(e)}")
        return False