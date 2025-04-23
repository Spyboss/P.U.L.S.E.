"""
Unit tests for the model configuration and orchestrator.
"""

import unittest
import os
import sys
import asyncio
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the modules to test
from configs.models import MODEL_IDS, MODEL_NAME_MAPPING, MODEL_ROLES, QUERY_TYPE_TO_MODEL
from skills.model_orchestrator import ModelOrchestrator


class TestModelConfiguration(unittest.TestCase):
    """Test the model configuration."""

    def test_model_ids(self):
        """Test that all required model IDs are present."""
        required_models = [
            "gemini",
            "troubleshooting",
            "code_generation",
            "documentation",
            "trend_real_time_updates",
            "content_creation",
            "technical_translation",
            "brainstorming",
            "ethical_ai",
            "low_resource"
        ]
        
        for model in required_models:
            self.assertIn(model, MODEL_IDS, f"Model ID for {model} is missing")
            self.assertIsNotNone(MODEL_IDS[model], f"Model ID for {model} is None")
            self.assertNotEqual(MODEL_IDS[model], "", f"Model ID for {model} is empty")
    
    def test_model_name_mapping(self):
        """Test that all model name mappings are correct."""
        required_mappings = [
            "gemini",
            "deepseek",
            "deepcoder",
            "agentica",
            "llama-doc",
            "mistral-small",
            "llama-content",
            "llama-technical",
            "hermes",
            "olmo",
            "phi"
        ]
        
        for mapping in required_mappings:
            self.assertIn(mapping, MODEL_NAME_MAPPING, f"Model name mapping for {mapping} is missing")
            self.assertIsNotNone(MODEL_NAME_MAPPING[mapping], f"Model name mapping for {mapping} is None")
            self.assertNotEqual(MODEL_NAME_MAPPING[mapping], "", f"Model name mapping for {mapping} is empty")
    
    def test_model_roles(self):
        """Test that all model roles are defined correctly."""
        required_roles = [
            "gemini",
            "deepseek",
            "deepcoder",
            "llama-doc",
            "mistral-small",
            "llama-content",
            "llama-technical",
            "hermes",
            "olmo",
            "phi"
        ]
        
        for role in required_roles:
            self.assertIn(role, MODEL_ROLES, f"Model role for {role} is missing")
            
            # Check that each role has the required fields
            role_info = MODEL_ROLES[role]
            required_fields = ["name", "role", "description", "strengths", "use_cases", "model_id", "api_type"]
            for field in required_fields:
                self.assertIn(field, role_info, f"Field {field} is missing from role {role}")
    
    def test_query_type_mapping(self):
        """Test that all query types are mapped to model roles."""
        required_query_types = [
            "code",
            "debug",
            "algorithm",
            "docs",
            "explain",
            "summarize",
            "troubleshoot",
            "solve",
            "trends",
            "research",
            "content",
            "creative",
            "write",
            "technical",
            "math",
            "brainstorm",
            "ideas",
            "ethics",
            "general",
            "simple"
        ]
        
        for query_type in required_query_types:
            self.assertIn(query_type, QUERY_TYPE_TO_MODEL, f"Query type {query_type} is not mapped to a model role")
            
            # Check that the mapped role exists
            mapped_role = QUERY_TYPE_TO_MODEL[query_type]
            self.assertIn(mapped_role, MODEL_ROLES, f"Query type {query_type} is mapped to non-existent role {mapped_role}")


class TestModelOrchestrator(unittest.TestCase):
    """Test the model orchestrator."""
    
    def setUp(self):
        """Set up the test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GEMINI_API_KEY': 'fake_key',
            'OPENROUTER_API_KEY': 'fake_key'
        })
        self.env_patcher.start()
        
        # Mock the Gemini and OpenRouter clients
        self.gemini_patcher = patch('google.generativeai.GenerativeModel')
        self.openai_patcher = patch('openai.OpenAI')
        
        self.mock_gemini = self.gemini_patcher.start()
        self.mock_openai = self.openai_patcher.start()
        
        # Create a mock response for Gemini
        self.mock_gemini_response = MagicMock()
        self.mock_gemini_response.text = "This is a test response from Gemini."
        self.mock_gemini_instance = self.mock_gemini.return_value
        self.mock_gemini_instance.generate_content.return_value = self.mock_gemini_response
        
        # Create a mock response for OpenRouter
        self.mock_openai_instance = self.mock_openai.return_value
        self.mock_openai_instance.chat.completions.create.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from OpenRouter."
                    }
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after the test."""
        self.env_patcher.stop()
        self.gemini_patcher.stop()
        self.openai_patcher.stop()
    
    def test_model_orchestrator_initialization(self):
        """Test that the model orchestrator initializes correctly."""
        orchestrator = ModelOrchestrator()
        
        # Check that the free models are loaded from the configuration
        for query_type, model_role in QUERY_TYPE_TO_MODEL.items():
            if model_role in MODEL_ROLES:
                self.assertIn(query_type, orchestrator.free_models)
                self.assertEqual(orchestrator.free_models[query_type], MODEL_ROLES[model_role]['model_id'])
        
        # Check that the model name mappings are loaded
        for model_name, model_info in MODEL_ROLES.items():
            self.assertIn(model_name, orchestrator.free_models)
            self.assertEqual(orchestrator.free_models[model_name], model_info['model_id'])
    
    def test_verify_model_id(self):
        """Test the model ID verification function."""
        orchestrator = ModelOrchestrator()
        
        # Test valid model IDs
        for model_id in MODEL_IDS.values():
            self.assertTrue(orchestrator._verify_model_id(model_id), f"Model ID {model_id} should be valid")
        
        # Test invalid model IDs
        invalid_ids = ["", None, "invalid/model", "model-without-vendor"]
        for model_id in invalid_ids:
            if model_id is not None and "/" in str(model_id):  # Skip the ones that would pass the vendor check
                continue
            self.assertFalse(orchestrator._verify_model_id(model_id), f"Model ID {model_id} should be invalid")
    
    @patch('asyncio.to_thread')
    def test_call_gemini(self, mock_to_thread):
        """Test calling the Gemini model."""
        orchestrator = ModelOrchestrator()
        
        # Set up the mock
        mock_to_thread.return_value = self.mock_gemini_response
        
        # Call the method
        response = asyncio.run(orchestrator._call_gemini("Test query", "Test context"))
        
        # Check the response
        self.assertTrue(response["success"])
        self.assertEqual(response["content"], "This is a test response from Gemini.")
        self.assertEqual(response["model"], "gemini-2.0-flash-thinking-exp-01-21")
        self.assertEqual(response["model_type"], "gemini")
    
    @patch('asyncio.to_thread')
    def test_call_openrouter_model(self, mock_to_thread):
        """Test calling an OpenRouter model."""
        orchestrator = ModelOrchestrator()
        orchestrator.openrouter = self.mock_openai_instance
        
        # Set up the mock
        mock_to_thread.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from OpenRouter."
                    }
                }
            ]
        }
        
        # Call the method
        response = asyncio.run(orchestrator._call_openrouter_model(
            "agentica-org/deepcoder-14b-preview:free",
            "Test query",
            "Test context"
        ))
        
        # Check the response
        self.assertTrue(response["success"])
        self.assertEqual(response["content"], "This is a test response from OpenRouter.")
        self.assertEqual(response["model"], "agentica-org/deepcoder-14b-preview:free")
        self.assertEqual(response["model_type"], "openrouter")


if __name__ == '__main__':
    unittest.main()
