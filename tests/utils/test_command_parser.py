"""
Unit tests for the command parser
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the command parser
from utils.command_parser import CommandParser

class TestCommandParser(unittest.TestCase):
    """Test cases for the KeywordCommandParser class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a parser
        self.parser = CommandParser()

        # Mock the intent handler to return predictable results
        self.parser.intent_handler = MagicMock()

    def test_parse_task_commands(self):
        """Test parsing of task commands"""
        # Set up the mock to return "task" intent
        self.parser.intent_handler.classify.return_value = "task"

        # Note: The current implementation doesn't have specific task commands
        # These tests are placeholders for when task functionality is implemented

        # Test add task - currently would be handled by the AI model
        result = self.parser.parse_command("add task Buy groceries")
        self.assertIn("command", result)

        # Test show tasks
        result = self.parser.parse_command("show my tasks")
        self.assertIn("command", result)

    def test_parse_time_commands(self):
        """Test parsing of time commands"""
        # Set up the mock to return "time" intent
        self.parser.intent_handler.classify.return_value = "time"

        # Test current time
        result = self.parser.parse_command("what time is it")
        self.assertEqual(result["command"], "time")

        # Test date
        result = self.parser.parse_command("what's today's date")
        self.assertEqual(result["command"], "date")

        # Test timezone
        result = self.parser.parse_command("time in Tokyo")
        self.assertEqual(result["command"], "timezone")
        self.assertEqual(result["location"], "Tokyo")

        # Test time in location
        result = self.parser.parse_command("time in London")
        self.assertEqual(result["command"], "timezone")
        self.assertEqual(result["location"], "London")

    def test_parse_github_commands(self):
        """Test parsing of GitHub commands"""
        # Set up the mock to return "github" intent
        self.parser.intent_handler.classify.return_value = "github"

        # Test info
        result = self.parser.parse_command("show info for github.com/user/repo")
        self.assertEqual(result["command"], "github_info")

        # Test issues
        result = self.parser.parse_command("list issues for github.com/user/repo")
        self.assertEqual(result["command"], "github_issues")

        # Test commit
        result = self.parser.parse_command("generate commit message for main.py in user/repo")
        self.assertEqual(result["command"], "github_commit")
        self.assertEqual(result["file_path"], "main.py")
        self.assertEqual(result["repo"], "user/repo")

    def test_parse_notion_commands(self):
        """Test parsing of Notion commands"""
        # Set up the mock to return "notion" intent
        self.parser.intent_handler.classify.return_value = "notion"

        # Test create
        result = self.parser.parse_command("create notion document called Meeting Notes")
        self.assertEqual(result["command"], "notion_document")
        self.assertEqual(result["title"], "Meeting Notes")

        # Test journal
        result = self.parser.parse_command("add journal entry")
        self.assertEqual(result["command"], "notion_journal")

    def test_parse_ai_query_commands(self):
        """Test parsing of AI query commands"""
        # Set up the mock to return "ai_query" intent
        self.parser.intent_handler.classify.return_value = "ai_query"

        # For AI query commands, we'll just check that the command is processed
        # without checking the specific values, since these are handled by the intent handler
        result = self.parser.parse_command("ask claude about machine learning")
        self.assertIn("command", result)

        result = self.parser.parse_command("tell me about quantum computing")
        self.assertIn("command", result)

        result = self.parser.parse_command("explain how blockchain works")
        self.assertIn("command", result)

        result = self.parser.parse_command("write a blog post about AI ethics")
        self.assertIn("command", result)

    def test_parse_system_commands(self):
        """Test parsing of system commands"""
        # Set up the mock to return "system" intent
        self.parser.intent_handler.classify.return_value = "system"

        # Test help
        result = self.parser.parse_command("help")
        self.assertEqual(result["command"], "help")

        # Test exit
        result = self.parser.parse_command("exit")
        self.assertEqual(result["command"], "exit")

        # Test quit
        result = self.parser.parse_command("quit")
        self.assertEqual(result["command"], "exit")

    def test_context_info(self):
        """Test context information"""
        # Set up the mock to return "task" intent
        self.parser.intent_handler.classify.return_value = "task"

        # Parse a command to add it to the context
        result = self.parser.parse_command("show my tasks")

        # Check that context info is included
        self.assertIn("context", result)
        self.assertIn("previous_intent", result["context"])
        self.assertIn("interaction_count", result["context"])

    def test_suggestions(self):
        """Test suggestions"""
        # Set up the mock to return "task" intent
        self.parser.intent_handler.classify.return_value = "task"

        # Parse a command that will be handled by the intent handler
        result = self.parser.parse_command("unknown command")

        # Check that suggestions are included
        self.assertIn("suggestions", result)

        # Parse another command to test context-aware suggestions
        result = self.parser.parse_command("another unknown command")
        self.assertIn("suggestions", result)

if __name__ == '__main__':
    unittest.main()
