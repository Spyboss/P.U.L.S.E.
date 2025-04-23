"""
Unit tests for the AI crew dynamics.
"""

import unittest
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the modules to test
from configs.models import CREW_MANIFEST, MODEL_ROLES
from configs.prompts import get_prompt
from skills.model_orchestrator import ModelOrchestrator


class TestCrewDynamics(unittest.TestCase):
    """Test the AI crew dynamics."""

    def test_crew_manifest(self):
        """Test that the crew manifest is properly defined."""
        # Check that the leader is defined
        self.assertIn("leader", CREW_MANIFEST, "Crew manifest should define a leader")
        self.assertEqual(CREW_MANIFEST["leader"], "gemini", "Gemini should be the leader")

        # Check that members are defined
        self.assertIn("members", CREW_MANIFEST, "Crew manifest should define members")
        self.assertGreater(len(CREW_MANIFEST["members"]), 0, "Crew manifest should have at least one member")

        # Check that relationships are defined
        self.assertIn("relationships", CREW_MANIFEST, "Crew manifest should define relationships")

        # Check that each member has a relationship defined
        for member in CREW_MANIFEST["members"]:
            self.assertIn(member, CREW_MANIFEST["relationships"], f"Member {member} should have a relationship defined")

            # Check that each relationship has the required fields
            relationship = CREW_MANIFEST["relationships"][member]
            required_fields = ["role", "knows_user", "can_delegate", "tone", "suggests"]
            for field in required_fields:
                self.assertIn(field, relationship, f"Relationship for {member} should have {field} defined")

    def test_prompts(self):
        """Test that prompts are properly defined for each model."""
        # Check that each model has a prompt
        for model_key in MODEL_ROLES:
            # Skip paid models
            if MODEL_ROLES[model_key].get("paid", False):
                continue

            prompt = get_prompt(model_key)
            self.assertIsNotNone(prompt, f"Model {model_key} should have a prompt")
            self.assertGreater(len(prompt), 0, f"Prompt for {model_key} should not be empty")

            # Check that the prompt contains the model's name
            model_info = MODEL_ROLES[model_key]
            self.assertIn(model_info["name"], prompt, f"Prompt for {model_key} should contain the model's name")

            # For Gemini, check for 'leader' instead of 'Default Chat'
            if model_key == "gemini":
                self.assertIn("leader", prompt, f"Prompt for {model_key} should contain 'leader'")
            else:
                self.assertIn(model_info["role"], prompt, f"Prompt for {model_key} should contain the model's role")

            # Check that the prompt contains the crew context
            if model_key != "gemini":  # Gemini has a special prompt
                self.assertIn("AI crew", prompt, f"Prompt for {model_key} should contain the crew context")

    @patch('google.generativeai.GenerativeModel')
    @patch('openai.OpenAI')
    def test_model_orchestrator_initialization(self, mock_openai, mock_gemini):
        """Test that the model orchestrator initializes correctly with the crew configuration."""
        # Set up the mocks
        mock_gemini_instance = MagicMock()
        mock_gemini.return_value = mock_gemini_instance

        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance

        # Mock environment variables
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'fake_key',
            'OPENROUTER_API_KEY': 'fake_key'
        }):
            # Initialize the model orchestrator
            orchestrator = ModelOrchestrator()

            # Check that the free models are loaded from the configuration
            for model_key in CREW_MANIFEST["members"]:
                if model_key in MODEL_ROLES:
                    self.assertIn(model_key, orchestrator.free_models, f"Model {model_key} should be in free_models")
                    self.assertEqual(orchestrator.free_models[model_key], MODEL_ROLES[model_key]["model_id"],
                                    f"Model ID for {model_key} should match the configuration")

    @patch('asyncio.to_thread')
    @patch('google.generativeai.GenerativeModel')
    @patch('openai.OpenAI')
    def test_call_gemini_with_prompt(self, mock_openai, mock_gemini, mock_to_thread):
        """Test that the _call_gemini method uses the Gemini-specific prompt."""
        # Set up the mocks
        mock_gemini_instance = MagicMock()
        mock_gemini.return_value = mock_gemini_instance

        mock_response = MagicMock()
        mock_response.text = "This is a test response from Gemini."
        mock_to_thread.return_value = mock_response

        # Mock environment variables
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'fake_key',
            'OPENROUTER_API_KEY': 'fake_key'
        }):
            # Initialize the model orchestrator
            orchestrator = ModelOrchestrator()

            # Call the _call_gemini method
            response = asyncio.run(orchestrator._call_gemini("Test query", "Test context"))

            # Check that the response is correct
            self.assertTrue(response["success"])
            self.assertEqual(response["content"], "This is a test response from Gemini.")
            self.assertEqual(response["model"], "gemini-2.0-flash-thinking-exp-01-21")
            self.assertEqual(response["model_type"], "gemini")

            # Check that the prompt was used
            args, kwargs = mock_to_thread.call_args
            self.assertEqual(args[0], orchestrator.gemini.generate_content)

            # The prompt should contain the Gemini-specific prompt
            prompt = args[1]
            self.assertIn("You are Gemini, the leader of General Pulse's AI crew", prompt)
            self.assertIn("Test context", prompt)
            self.assertIn("Test query", prompt)

    @patch('asyncio.to_thread')
    @patch('openai.OpenAI')
    def test_call_openrouter_model_with_prompt(self, mock_openai, mock_to_thread):
        """Test that the _call_openrouter_model method uses the role-specific prompt."""
        # Set up the mocks
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from OpenRouter."
                    }
                }
            ]
        }
        mock_to_thread.return_value = mock_response

        # Mock environment variables
        with patch.dict('os.environ', {
            'GEMINI_API_KEY': 'fake_key',
            'OPENROUTER_API_KEY': 'fake_key'
        }):
            # Initialize the model orchestrator
            orchestrator = ModelOrchestrator()
            orchestrator.openrouter = mock_openai_instance

            # Call the _call_openrouter_model method with a specific model ID
            model_id = MODEL_ROLES["deepseek"]["model_id"]
            response = asyncio.run(orchestrator._call_openrouter_model(model_id, "Test query", "Test context"))

            # Check that the response is correct
            self.assertTrue(response["success"])
            self.assertEqual(response["content"], "This is a test response from OpenRouter.")
            self.assertEqual(response["model"], model_id)
            self.assertEqual(response["model_type"], "openrouter")

            # Check that the prompt was used
            args, kwargs = mock_to_thread.call_args
            self.assertEqual(args[0], orchestrator.openrouter.chat.completions.create)

            # The messages should contain the DeepSeek-specific prompt
            messages = kwargs["messages"]
            self.assertEqual(len(messages), 3)  # system prompt, context, user message
            self.assertEqual(messages[0]["role"], "system")
            self.assertIn("You are DeepSeek, the Troubleshooting", messages[0]["content"])
            self.assertEqual(messages[1]["role"], "system")
            self.assertIn("Test context", messages[1]["content"])
            self.assertEqual(messages[2]["role"], "user")
            self.assertEqual(messages[2]["content"], "Test query")


if __name__ == '__main__':
    unittest.main()
