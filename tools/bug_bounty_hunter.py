"""
AI Bug Bounty Hunter for General Pulse
Scans code for potential bugs and issues using AI models
"""

import os
import sys
import re
import json
from pathlib import Path
import tempfile
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import logger, load_yaml_config, save_json_data, ensure_directory_exists
from skills.optimized_model_interface import OptimizedModelInterface

class AIBugBountyHunter:
    """Tool for scanning code to find potential bugs using AI."""

    def __init__(self, config_path="configs/agent_config.yaml"):
        """Initialize the Bug Bounty Hunter with configuration."""
        self.config_path = config_path
        self.logger = logger
        self.logger.debug(f"AIBugBountyHunter initializing with config path: {config_path}")

        try:
            self.config = load_yaml_config(config_path)
            self.bug_hunter_config = self.config.get('tools', {}).get('bug_bounty_hunter', {})
            self.enabled = self.bug_hunter_config.get('enabled', True)

            # Initialize model interface for AI analysis
            self.model_interface = OptimizedModelInterface()

            # Default to DeepSeek for code analysis and Claude for commentary
            self.analysis_model = self.bug_hunter_config.get('analysis_model', 'deepseek')
            self.comment_model = self.bug_hunter_config.get('comment_model', 'claude')

            # Set up supported file extensions for scanning
            self.supported_extensions = self.bug_hunter_config.get('supported_extensions',
                ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rb'])

            if self.enabled:
                self.logger.info("AI Bug Bounty Hunter enabled")
            else:
                self.logger.info("AI Bug Bounty Hunter disabled")
        except Exception as e:
            self.logger.error(f"Error initializing AI Bug Bounty Hunter: {str(e)}", exc_info=True)
            self.config = {}
            self.bug_hunter_config = {}
            self.enabled = False
            self.model_interface = None
            self.analysis_model = 'deepseek'
            self.comment_model = 'claude'
            self.supported_extensions = ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rb']

    def is_configured(self):
        """Check if Bug Bounty Hunter is properly configured."""
        configured = self.enabled and self.model_interface and self.model_interface.get_available_models()
        self.logger.debug(f"Bug Bounty Hunter configured: {configured}")
        return configured

    def analyze_file(self, file_path):
        """Analyze a single file for potential bugs."""
        try:
            if not self.is_configured():
                self.logger.warning("Bug Bounty Hunter not configured")
                return {"error": "Bug Bounty Hunter not configured"}

            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return {"error": f"File not found: {file_path}"}

            file_ext = os.path.splitext(file_path)[1]
            if file_ext not in self.supported_extensions:
                self.logger.warning(f"Unsupported file type: {file_ext}")
                return {"error": f"Unsupported file type: {file_ext}", "supported_extensions": self.supported_extensions}

            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()

            if not code_content.strip():
                self.logger.warning(f"Empty file: {file_path}")
                return {"error": "Empty file", "file": file_path}

            self.logger.info(f"Analyzing file for bugs: {file_path}")

            # Generate the prompt for code analysis
            prompt = self._generate_analysis_prompt(file_path, code_content)

            # Call the AI model to analyze the code
            analysis_response = self.model_interface.call_model_api(
                self.analysis_model,
                prompt
            )

            if "error" in analysis_response:
                self.logger.error(f"Error during code analysis: {analysis_response['error']}")
                return {"error": f"AI analysis failed: {analysis_response['error']}"}

            # Parse the analysis response to extract bugs and issues
            bugs = self._parse_analysis_response(analysis_response['response'], code_content)

            # If bugs were found, generate humorous comments
            if bugs and bugs['total_issues'] > 0:
                self.logger.info(f"Found {bugs['total_issues']} potential issues in {file_path}")

                # Generate humorous comments for the issues
                bugs = self._add_humorous_comments(bugs)

                # Cache the results
                self._cache_analysis_results(file_path, bugs)

                return bugs
            else:
                self.logger.info(f"No issues found in {file_path}")
                return {"total_issues": 0, "issues": [], "file": file_path}

        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def analyze_git_diff(self, diff_text=None, repo_path=None):
        """Analyze changes in a git diff for potential bugs."""
        try:
            if not self.is_configured():
                self.logger.warning("Bug Bounty Hunter not configured")
                return {"error": "Bug Bounty Hunter not configured"}

            # Get the diff if not provided
            if not diff_text and repo_path:
                diff_text = self._get_git_diff(repo_path)

            if not diff_text:
                self.logger.warning("No diff provided or generated")
                return {"error": "No diff provided or generated"}

            self.logger.info("Analyzing git diff for potential issues")

            # Generate prompt for diff analysis
            prompt = self._generate_diff_analysis_prompt(diff_text)

            # Call the AI model to analyze the diff
            analysis_response = self.model_interface.call_model_api(
                self.analysis_model,
                prompt
            )

            if "error" in analysis_response:
                self.logger.error(f"Error during diff analysis: {analysis_response['error']}")
                return {"error": f"AI analysis failed: {analysis_response['error']}"}

            # Parse the analysis response to extract bugs and issues
            issues = self._parse_diff_analysis_response(analysis_response['response'], diff_text)

            # If issues were found, generate humorous comments
            if issues and issues['total_issues'] > 0:
                self.logger.info(f"Found {issues['total_issues']} potential issues in git diff")

                # Generate humorous comments for the issues
                issues = self._add_humorous_comments(issues)

                # Cache the results
                self._cache_diff_analysis_results(issues)

                return issues
            else:
                self.logger.info("No issues found in git diff")
                return {"total_issues": 0, "issues": [], "source": "git_diff"}

        except Exception as e:
            self.logger.error(f"Error analyzing git diff: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def analyze_repo(self, repo_path, max_files=10):
        """Analyze a local repository for potential bugs, limited to max_files."""
        try:
            if not self.is_configured():
                self.logger.warning("Bug Bounty Hunter not configured")
                return {"error": "Bug Bounty Hunter not configured"}

            if not os.path.exists(repo_path):
                self.logger.error(f"Repository path not found: {repo_path}")
                return {"error": f"Repository path not found: {repo_path}"}

            self.logger.info(f"Analyzing repository: {repo_path}")

            # Find files to analyze
            files_to_analyze = self._find_files_to_analyze(repo_path, max_files)

            if not files_to_analyze:
                self.logger.warning(f"No supported files found in: {repo_path}")
                return {"error": "No supported files found", "repository": repo_path}

            self.logger.info(f"Found {len(files_to_analyze)} files to analyze")

            # Analyze each file
            results = {
                "total_issues": 0,
                "repository": repo_path,
                "files_analyzed": len(files_to_analyze),
                "file_results": []
            }

            for file_path in files_to_analyze:
                self.logger.debug(f"Analyzing file: {file_path}")
                file_result = self.analyze_file(file_path)

                if "error" not in file_result:
                    results["total_issues"] += file_result.get("total_issues", 0)
                    results["file_results"].append(file_result)

            # Cache the overall results
            self._cache_repo_analysis_results(repo_path, results)

            return results

        except Exception as e:
            self.logger.error(f"Error analyzing repository {repo_path}: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def _generate_analysis_prompt(self, file_path, code_content):
        """Generate a prompt for AI code analysis."""
        file_ext = os.path.splitext(file_path)[1]
        file_name = os.path.basename(file_path)

        prompt = f"""You are an expert code reviewer and bug hunter. Analyze the following code for potential bugs,
performance issues, security vulnerabilities, and other problems.

File: {file_name}

```{file_ext[1:]}
{code_content}
```

Carefully analyze the code and identify any issues, focusing on:
1. Bugs (logical errors, undefined variables, potential runtime exceptions)
2. Security vulnerabilities
3. Performance problems
4. Code smells and architectural issues
5. Potential edge cases that aren't handled

For each issue you find, indicate:
- The line number
- A description of the problem
- Severity (critical, high, medium, low)
- A suggestion for fixing it

Format your response as JSON with this structure:
{{
  "total_issues": n,
  "issues": [
    {{
      "line": line_number,
      "description": "Description of the issue",
      "severity": "critical|high|medium|low",
      "fix_suggestion": "Suggested fix"
    }},
    ...
  ]
}}

If you find no issues, respond with: {{"total_issues": 0, "issues": []}}
Please ensure your JSON output is valid and properly structured.
"""

        return prompt

    def _generate_diff_analysis_prompt(self, diff_text):
        """Generate a prompt for analyzing a git diff."""
        prompt = f"""You are an expert code reviewer and bug hunter. Analyze the following git diff for potential bugs,
performance issues, security vulnerabilities, and other problems that might have been introduced in these changes.

The git diff:

```
{diff_text}
```

Carefully analyze the changes and identify any issues, focusing on:
1. Bugs (logical errors, undefined variables, potential runtime exceptions)
2. Security vulnerabilities introduced by the changes
3. Performance problems
4. Code smells and architectural issues
5. Potential edge cases that aren't handled

For each issue you find, indicate:
- The file name
- The line number (in the new file)
- A description of the problem
- Severity (critical, high, medium, low)
- A suggestion for fixing it

Format your response as JSON with this structure:
{{
  "total_issues": n,
  "issues": [
    {{
      "file": "filename.ext",
      "line": line_number,
      "description": "Description of the issue",
      "severity": "critical|high|medium|low",
      "fix_suggestion": "Suggested fix"
    }},
    ...
  ]
}}

If you find no issues, respond with: {{"total_issues": 0, "issues": []}}
Please ensure your JSON output is valid and properly structured.
"""

        return prompt

    def _parse_analysis_response(self, response_text, code_content):
        """Parse the AI model's response to extract bug information."""
        try:
            # Try to extract JSON from the response
            # Look for JSON structure
            json_match = re.search(r'({[\s\S]*})', response_text)

            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)

                # Add file metadata
                result["code_size"] = len(code_content)
                result["line_count"] = code_content.count('\n') + 1

                return result
            else:
                # If no JSON found, try to parse the response manually
                self.logger.warning("No JSON found in response, attempting manual parsing")
                issues = []

                # Look for patterns like "Line X: description"
                line_patterns = [
                    r'Line (\d+):\s*(.*?)\s*(?:Severity|$)',
                    r'line (\d+)\s*[-:]\s*(.*?)\s*(?:Severity|$)'
                ]

                for pattern in line_patterns:
                    matches = re.finditer(pattern, response_text, re.IGNORECASE)
                    for match in matches:
                        line_num = int(match.group(1))
                        description = match.group(2).strip()

                        # Try to determine severity
                        severity = "medium"  # Default
                        severity_match = re.search(r'Severity:\s*(critical|high|medium|low)',
                                                   response_text[match.end():match.end()+100],
                                                   re.IGNORECASE)
                        if severity_match:
                            severity = severity_match.group(1).lower()

                        issues.append({
                            "line": line_num,
                            "description": description,
                            "severity": severity,
                            "fix_suggestion": "Not provided"
                        })

                return {
                    "total_issues": len(issues),
                    "issues": issues,
                    "code_size": len(code_content),
                    "line_count": code_content.count('\n') + 1
                }
        except Exception as e:
            self.logger.error(f"Error parsing analysis response: {str(e)}", exc_info=True)
            return {
                "total_issues": 0,
                "issues": [],
                "error": f"Failed to parse analysis: {str(e)}"
            }

    def _parse_diff_analysis_response(self, response_text, diff_text):
        """Parse the AI model's response for diff analysis."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'({[\s\S]*})', response_text)

            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)

                # Add metadata
                result["source"] = "git_diff"
                result["diff_size"] = len(diff_text)

                return result
            else:
                # Manual parsing similar to _parse_analysis_response
                self.logger.warning("No JSON found in response, attempting manual parsing")
                issues = []

                # More complex for diff, look for file and line references
                file_pattern = r'File:\s*([^\n]+)'
                line_pattern = r'Line (\d+):\s*(.*?)(?=\n|$)'

                files = re.finditer(file_pattern, response_text)
                current_file = None

                for file_match in files:
                    current_file = file_match.group(1).strip()
                    file_section = response_text[file_match.end():]

                    # Find the next file section if any
                    next_file = re.search(file_pattern, file_section)
                    if next_file:
                        file_section = file_section[:next_file.start()]

                    # Find issues in this file section
                    lines = re.finditer(line_pattern, file_section)
                    for line_match in lines:
                        line_num = int(line_match.group(1))
                        description = line_match.group(2).strip()

                        # Determine severity if mentioned
                        severity = "medium"  # Default
                        severity_match = re.search(r'Severity:\s*(critical|high|medium|low)',
                                                   file_section[line_match.end():line_match.end()+100],
                                                   re.IGNORECASE)
                        if severity_match:
                            severity = severity_match.group(1).lower()

                        issues.append({
                            "file": current_file,
                            "line": line_num,
                            "description": description,
                            "severity": severity,
                            "fix_suggestion": "Not provided"
                        })

                return {
                    "total_issues": len(issues),
                    "issues": issues,
                    "source": "git_diff",
                    "diff_size": len(diff_text)
                }
        except Exception as e:
            self.logger.error(f"Error parsing diff analysis response: {str(e)}", exc_info=True)
            return {
                "total_issues": 0,
                "issues": [],
                "source": "git_diff",
                "error": f"Failed to parse analysis: {str(e)}"
            }

    def _add_humorous_comments(self, analysis_result):
        """Add humorous comments to the analysis results using Claude."""
        try:
            if not analysis_result or analysis_result.get("total_issues", 0) == 0:
                return analysis_result

            self.logger.info(f"Generating humorous comments for {analysis_result['total_issues']} issues")

            # Create a prompt for generating humorous comments
            issues_text = ""
            for i, issue in enumerate(analysis_result.get("issues", [])):
                issues_text += f"{i+1}. {issue.get('description', 'Unknown issue')} (Severity: {issue.get('severity', 'medium')})\n"

            prompt = f"""You are a witty, sarcastic, but still helpful code reviewer. You need to write humorous, slightly
sassy comments for each of these code issues. Be funny but constructive - like a friend who teases you but still wants to help.

The issues are:

{issues_text}

For each issue, write a one-liner that:
1. Is humorous and a bit snarky
2. References the specific issue
3. Uses creative metaphors or pop culture references when appropriate

Format your response as a JSON array of strings, one for each issue:
[
  "First humorous comment",
  "Second humorous comment",
  ...
]

Keep each comment under 100 characters for readability.
"""

            # Call Claude to generate the comments
            comments_response = self.model_interface.call_model_api(
                self.comment_model,
                prompt
            )

            if "error" in comments_response:
                self.logger.warning(f"Error generating humorous comments: {comments_response['error']}")
                return analysis_result

            # Try to parse the JSON array from the response
            try:
                response_text = comments_response['response']
                json_match = re.search(r'(\[[\s\S]*\])', response_text)

                if json_match:
                    comments = json.loads(json_match.group(1))

                    # Add comments to the analysis result
                    for i, issue in enumerate(analysis_result["issues"]):
                        if i < len(comments):
                            issue["humorous_comment"] = comments[i]

                    return analysis_result
                else:
                    # Manual parsing as fallback
                    self.logger.warning("No JSON array found in comments response, attempting manual parsing")
                    lines = [line.strip() for line in response_text.splitlines() if line.strip()]
                    quotes = [line for line in lines if (line.startswith('"') and line.endswith('"')) or
                                                     (line.startswith('"') and line.endswith('",'))]

                    if quotes:
                        for i, issue in enumerate(analysis_result["issues"]):
                            if i < len(quotes):
                                # Clean up the quote
                                quote = quotes[i].strip('"').strip('",').strip()
                                issue["humorous_comment"] = quote

                    return analysis_result
            except Exception as e:
                self.logger.error(f"Error parsing humorous comments: {str(e)}", exc_info=True)
                return analysis_result

        except Exception as e:
            self.logger.error(f"Error adding humorous comments: {str(e)}", exc_info=True)
            return analysis_result

    def _get_git_diff(self, repo_path):
        """Get the git diff for uncommitted changes in a repository."""
        try:
            if not os.path.exists(repo_path):
                self.logger.error(f"Repository path not found: {repo_path}")
                return None

            self.logger.info(f"Getting git diff for: {repo_path}")

            # Check if it's a git repository
            git_dir = os.path.join(repo_path, ".git")
            if not os.path.exists(git_dir):
                self.logger.error(f"Not a git repository: {repo_path}")
                return None

            # Run git diff to get uncommitted changes
            try:
                # First, get staged changes
                staged_result = subprocess.run(
                    ["git", "diff", "--staged"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=False
                )

                # Then, get unstaged changes
                unstaged_result = subprocess.run(
                    ["git", "diff"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=False
                )

                # Combine the results
                diff_text = staged_result.stdout + unstaged_result.stdout

                if not diff_text.strip():
                    self.logger.warning(f"No changes found in repository: {repo_path}")
                    return None

                return diff_text

            except subprocess.SubprocessError as e:
                self.logger.error(f"Error running git diff: {str(e)}", exc_info=True)
                return None

        except Exception as e:
            self.logger.error(f"Error getting git diff: {str(e)}", exc_info=True)
            return None

    def _find_files_to_analyze(self, repo_path, max_files=10):
        """Find appropriate files to analyze in the repository."""
        supported_files = []

        try:
            for root, _, files in os.walk(repo_path):
                # Skip .git directory
                if ".git" in root.split(os.path.sep):
                    continue

                # Skip virtual environments
                if "venv" in root.split(os.path.sep) or "env" in root.split(os.path.sep):
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1]

                    if ext in self.supported_extensions:
                        supported_files.append(file_path)

                        if len(supported_files) >= max_files:
                            return supported_files

            return supported_files

        except Exception as e:
            self.logger.error(f"Error finding files to analyze: {str(e)}", exc_info=True)
            return []

    def _cache_analysis_results(self, file_path, results):
        """Cache analysis results for a file."""
        try:
            storage_dir = "memory/bug_hunter"
            ensure_directory_exists(storage_dir)

            # Create a cache filename based on the file path
            filename = os.path.basename(file_path)
            cache_file = os.path.join(storage_dir, f"{filename}_analysis.json")

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)

            self.logger.debug(f"Cached analysis results for {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error caching analysis results: {str(e)}", exc_info=True)
            return False

    def _cache_diff_analysis_results(self, results):
        """Cache diff analysis results."""
        try:
            storage_dir = "memory/bug_hunter"
            ensure_directory_exists(storage_dir)

            # Use timestamp for the cache file
            import time
            timestamp = int(time.time())
            cache_file = os.path.join(storage_dir, f"diff_analysis_{timestamp}.json")

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)

            self.logger.debug(f"Cached diff analysis results")
            return True
        except Exception as e:
            self.logger.error(f"Error caching diff analysis results: {str(e)}", exc_info=True)
            return False

    def _cache_repo_analysis_results(self, repo_path, results):
        """Cache repository analysis results."""
        try:
            storage_dir = "memory/bug_hunter"
            ensure_directory_exists(storage_dir)

            # Create a cache filename based on the repository name
            repo_name = os.path.basename(repo_path)
            import time
            timestamp = int(time.time())
            cache_file = os.path.join(storage_dir, f"{repo_name}_repo_analysis_{timestamp}.json")

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)

            self.logger.debug(f"Cached repo analysis results for {repo_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error caching repo analysis results: {str(e)}", exc_info=True)
            return False