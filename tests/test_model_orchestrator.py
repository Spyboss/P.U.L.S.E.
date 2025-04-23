"""
Unit tests for the model orchestrator
"""

import unittest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from skills.model_orchestrator import ModelOrchestrator

class TestModelOrchestrator(unittest.TestCase):
    """Test cases for the ModelOrchestrator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use simulation mode for testing
        self.orchestrator = ModelOrchestrator(simulate_responses=True)
    
    def test_init(self):
        """Test initialization"""
        # Check if usage stats were initialized
        usage_stats = self.orchestrator.get_usage_stats()
        self.assertIn("gemini", usage_stats)
        self.assertIn("openrouter", usage_stats)
        self.assertIn("local", usage_stats)
        
        # Check if free models were initialized
        self.assertIn("code", self.orchestrator.free_models)
        self.assertIn("docs", self.orchestrator.free_models)
        self.assertIn("troubleshoot", self.orchestrator.free_models)
    
    def test_classify_query(self):
        """Test query classification"""
        # Test code query
        result = asyncio.run(self.orchestrator._classify_query("Help me debug this code"))
        self.assertEqual(result, "code")
        
        # Test documentation query
        result = asyncio.run(self.orchestrator._classify_query("Write documentation for this function"))
        self.assertEqual(result, "docs")
        
        # Test troubleshooting query
        result = asyncio.run(self.orchestrator._classify_query("Help me fix this error"))
        self.assertEqual(result, "troubleshoot")
        
        # Test trends query
        result = asyncio.run(self.orchestrator._classify_query("What are the latest trends in AI?"))
        self.assertEqual(result, "trends")
        
        # Test content query
        result = asyncio.run(self.orchestrator._classify_query("Generate a blog post about Python"))
        self.assertEqual(result, "content")
        
        # Test technical query
        result = asyncio.run(self.orchestrator._classify_query("Explain this complex algorithm"))
        self.assertEqual(result, "technical")
        
        # Test brainstorming query
        result = asyncio.run(self.orchestrator._classify_query("Let's brainstorm some ideas"))
        self.assertEqual(result, "brainstorm")
        
        # Test ethics query
        result = asyncio.run(self.orchestrator._classify_query("Is this AI system biased?"))
        self.assertEqual(result, "ethics")
        
        # Test simple query
        result = asyncio.run(self.orchestrator._classify_query("Hello"))
        self.assertEqual(result, "simple")
        
        # Test general query
        result = asyncio.run(self.orchestrator._classify_query("Tell me about artificial intelligence"))
        self.assertEqual(result, "general")
    
    def test_format_context(self):
        """Test context formatting"""
        # Test with empty context
        result = self.orchestrator._format_context(None)
        self.assertEqual(result, "")
        
        # Test with history
        context = {
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        result = self.orchestrator._format_context(context)
        self.assertIn("Recent conversation:", result)
        self.assertIn("User: Hello", result)
        self.assertIn("Assistant: Hi there!", result)
        
        # Test with user data
        context = {
            "user_data": {
                "projects": ["Project A", "Project B"],
                "interests": ["Interest A", "Interest B"],
                "goals": [{"goal": "Goal A"}, {"goal": "Goal B"}]
            }
        }
        result = self.orchestrator._format_context(context)
        self.assertIn("User projects: Project A, Project B", result)
        self.assertIn("User interests: Interest A, Interest B", result)
        self.assertIn("User goals: Goal A, Goal B", result)
    
    def test_simulate_response(self):
        """Test simulated responses"""
        result = self.orchestrator._simulate_response("Test query")
        
        self.assertTrue(result["success"])
        self.assertIn("Simulated", result["content"])
        self.assertEqual(result["model"], "simulation")
        self.assertEqual(result["model_type"], "simulated")
    
    @patch('skills.model_orchestrator.ModelOrchestrator._classify_query')
    async def test_handle_query_simulation(self, mock_classify):
        """Test handling queries in simulation mode"""
        mock_classify.return_value = "general"
        
        # Test with simulation mode
        result = await self.orchestrator.handle_query("Test query")
        
        self.assertTrue(result["success"])
        self.assertIn("Simulated", result["content"])
        self.assertEqual(result["model"], "simulation")
    
    def test_get_usage_stats(self):
        """Test getting usage statistics"""
        # Get initial stats
        initial_stats = self.orchestrator.get_usage_stats()
        
        # Simulate a query
        asyncio.run(self.orchestrator.handle_query("Test query"))
        
        # Get updated stats
        updated_stats = self.orchestrator.get_usage_stats()
        
        # Stats should be unchanged in simulation mode
        self.assertEqual(initial_stats, updated_stats)
    
    def test_get_available_models(self):
        """Test getting available models"""
        models = self.orchestrator.get_available_models()
        
        self.assertIn("gemini", models)
        self.assertIn("openrouter", models)
        self.assertIn("local", models)

if __name__ == '__main__':
    unittest.main()
