#!/usr/bin/env python
"""
Test script for AI-generated commit messages
"""

import os
import sys
import json
from dotenv import load_dotenv
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AICommitTest")

# Import the required modules
try:
    from tools.github_integration import GitHubIntegration
    from skills.model_interface import ModelInterface
    logger.info("Successfully imported required modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    sys.exit(1)

def generate_commit_message_from_diff(diff_text, file_path=None, model="deepseek"):
    """Generate a commit message from the provided diff using AI."""
    # Initialize the GitHub integration
    github = GitHubIntegration()
    
    if not github.is_configured():
        logger.error("GitHub integration is not configured properly")
        return False
    
    # Generate the commit message
    commit_message = github.generate_commit_message(diff_text, file_path, model)
    
    logger.info(f"Generated commit message: {commit_message}")
    return commit_message

def test_with_sample_diff():
    """Test using a sample diff."""
    # A sample diff for demonstration
    sample_diff = """--- a/README.md
+++ b/README.md
@@ -4,7 +4,9 @@
 
 ## Features
 
-* Task tracking and management
+* Comprehensive task tracking and management
+* AI-driven commit message generation
+* OpenRouter integration for multiple AI models
 * GitHub API integration
 * Automated workflows
 """
    
    # Generate a commit message for the sample diff
    logger.info("Generating commit message for a sample diff...")
    commit_message = generate_commit_message_from_diff(sample_diff, "README.md", "deepseek")
    
    if commit_message:
        logger.info(f"✅ Successfully generated commit message using DeepSeek")
        logger.info(f"Commit message: {commit_message}")
    else:
        logger.error("❌ Failed to generate commit message")
    
    # Try with Claude
    logger.info("\nTrying with Claude model...")
    commit_message = generate_commit_message_from_diff(sample_diff, "README.md", "claude")
    
    if commit_message:
        logger.info(f"✅ Successfully generated commit message using Claude")
        logger.info(f"Commit message: {commit_message}")
    else:
        logger.error("❌ Failed to generate commit message")

def test_with_real_repo(owner, repo, file_path, branch="main"):
    """Test with a real GitHub repository."""
    # Initialize the GitHub integration
    github = GitHubIntegration()
    
    if not github.is_configured():
        logger.error("GitHub integration is not configured properly")
        return False
    
    # Get the file content
    logger.info(f"Getting content for {file_path} in {owner}/{repo}...")
    file_info = github.get_file_content(owner, repo, file_path, branch)
    
    if "error" in file_info:
        logger.error(f"Error getting file: {file_info['error']}")
        return False
    
    # Make a fake change to the content
    logger.info("Making a fake change to the content...")
    original_content = file_info["content"]
    sha = file_info["sha"]
    
    # Add a comment line at the top of the file for demonstration
    modified_content = original_content
    if file_path.endswith(".py"):
        modified_content = "# Added by AI Commit Test\n" + original_content
    elif file_path.endswith(".md"):
        modified_content = "<!-- Added by AI Commit Test -->\n" + original_content
    elif file_path.endswith(".js") or file_path.endswith(".ts"):
        modified_content = "// Added by AI Commit Test\n" + original_content
    else:
        modified_content = "/* Added by AI Commit Test */\n" + original_content
    
    # Generate a diff
    import difflib
    diff = list(difflib.unified_diff(
        original_content.splitlines(),
        modified_content.splitlines(),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    ))
    diff_text = "\n".join(diff)
    
    # Generate a commit message
    logger.info("Generating commit message...")
    commit_message = github.generate_commit_message(diff_text, file_path)
    
    logger.info(f"Generated commit message: {commit_message}")
    
    # Ask if user wants to commit the change
    choice = input("\nDo you want to actually commit this change? (y/N): ").strip().lower()
    
    if choice == "y":
        logger.info("Committing changes...")
        result = github.commit_changes(owner, repo, branch, file_path, modified_content, commit_message, sha)
        
        if "error" in result:
            logger.error(f"Error committing changes: {result['error']}")
            return False
        
        logger.info(f"✅ Successfully committed changes with message: {commit_message}")
        if "commit" in result and "html_url" in result["commit"]:
            logger.info(f"Commit URL: {result['commit']['html_url']}")
        return True
    else:
        logger.info("Skipping actual commit.")
        return True

def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test AI-generated commit messages")
    parser.add_argument("--sample", action="store_true", help="Run with sample diff")
    parser.add_argument("--owner", help="Repository owner (username)")
    parser.add_argument("--repo", help="Repository name")
    parser.add_argument("--file", help="File path within the repository")
    parser.add_argument("--branch", default="main", help="Branch name (default: main)")
    parser.add_argument("--model", default="deepseek", help="AI model to use (default: deepseek)")
    
    args = parser.parse_args()
    
    # Check for GitHub token
    if not os.environ.get("GITHUB_TOKEN"):
        logger.error("GITHUB_TOKEN environment variable not set")
        return 1
        
    # Check for OpenRouter API key
    if not os.environ.get("OPENROUTER_API_KEY"):
        logger.warning("OPENROUTER_API_KEY environment variable not set, may use direct APIs or simulation")
    
    # Run tests
    if args.sample:
        test_with_sample_diff()
    elif args.owner and args.repo and args.file:
        test_with_real_repo(args.owner, args.repo, args.file, args.branch)
    else:
        logger.info("No test mode specified. Running with sample diff...")
        test_with_sample_diff()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 