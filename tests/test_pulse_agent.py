"""
Unit tests for the Pulse Agent
"""

import unittest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from skills.pulse_agent import PulseAgent

class TestPulseAgent(unittest.TestCase):
    """Test cases for the PulseAgent class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use simulation mode for testing
        self.agent = PulseAgent(user_id="test_user", simulate_responses=True)
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.agent.shutdown()
    
    def test_init(self):
        """Test initialization"""
        # Check if components were initialized
        self.assertIsNotNone(self.agent.memory)
        self.assertIsNotNone(self.agent.context)
        self.assertIsNotNone(self.agent.personality)
        self.assertIsNotNone(self.agent.model_orchestrator)
        self.assertIsNotNone(self.agent.intent_handler)
        
        # Check conversation state
        self.assertIn("session_start", self.agent.conversation_state)
        self.assertEqual(self.agent.conversation_state["interaction_count"], 0)
    
    @patch('skills.pulse_agent.PulseAgent._process_with_model')
    async def test_process_input(self, mock_process):
        """Test processing input"""
        # Mock _process_with_model
        mock_process.return_value = "Test response"
        
        # Test normal input
        response = await self.agent.process_input("Hello")
        
        # Check if _process_with_model was called
        mock_process.assert_called_once_with("Hello")
        
        # Check if conversation state was updated
        self.assertEqual(self.agent.conversation_state["last_input"], "Hello")
        self.assertEqual(self.agent.conversation_state["interaction_count"], 1)
        
        # Test system commands
        response = await self.agent.process_input("help")
        self.assertIn("Pulse Help", response)
        
        response = await self.agent.process_input("status")
        self.assertIn("System Status", response)
    
    @patch('skills.pulse_agent.PulseAgent._handle_intent')
    @patch('utils.intent_handler.IntentHandler.parse_command')
    async def test_intent_handling(self, mock_parse, mock_handle):
        """Test intent handling"""
        # Mock intent parsing
        mock_parse.return_value = {"command_type": "test_intent", "param": "value"}
        
        # Mock intent handling
        mock_handle.return_value = "Intent handled"
        
        # Test intent handling
        response = await self.agent.process_input("test intent")
        
        # Check if intent was parsed and handled
        mock_parse.assert_called_once_with("test intent")
        mock_handle.assert_called_once_with({"command_type": "test_intent", "param": "value"}, "test intent")
    
    @patch('skills.model_orchestrator.ModelOrchestrator.handle_query')
    async def test_process_with_model(self, mock_handle_query):
        """Test processing with model"""
        # Mock model response
        mock_handle_query.return_value = {
            "success": True,
            "content": "Model response",
            "model": "test_model",
            "model_type": "test_type"
        }
        
        # Test processing with model
        response = await self.agent._process_with_model("Test query")
        
        # Check if model was called
        mock_handle_query.assert_called_once()
        
        # Check if response was formatted
        self.assertIn("Model response", response)
    
    def test_get_time(self):
        """Test getting time"""
        # Test local time
        response = self.agent._get_time()
        self.assertIn("local time", response)
        
        # Test specific location
        response = self.agent._get_time("London")
        self.assertIn("London", response)
    
    def test_handle_goal(self):
        """Test handling goals"""
        # Test adding a goal
        response = self.agent._handle_goal("add", "Test goal", 1)
        self.assertIn("Goal added", response)
        
        # Test listing goals
        response = self.agent._handle_goal("list")
        self.assertIn("Test goal", response)
        
        # Test completing a goal
        response = self.agent._handle_goal("complete", "Test goal")
        self.assertIn("completed", response)
    
    def test_handle_memory(self):
        """Test handling memory"""
        # Test saving to memory
        response = self.agent._handle_memory("save", "test_category: test_data")
        self.assertIn("Saved to memory", response)
        
        # Test recalling from memory
        response = self.agent._handle_memory("recall", "test_category")
        self.assertIn("test_data", response)
        
        # Test searching memory
        response = self.agent._handle_memory("search", "test")
        self.assertIn("test_data", response)
    
    def test_adjust_personality(self):
        """Test adjusting personality"""
        # Test getting current traits
        response = self.agent._adjust_personality()
        self.assertIn("personality traits", response)
        
        # Test adjusting a trait
        response = self.agent._adjust_personality("informative", 0.9)
        self.assertIn("Adjusted personality trait", response)
        
        # Test invalid trait
        response = self.agent._adjust_personality("invalid_trait", 0.5)
        self.assertIn("Unknown personality trait", response)
    
    def test_format_response(self):
        """Test formatting responses"""
        # Test successful response
        response = self.agent._format_response("Test response")
        self.assertIn("Test response", response)
        
        # Test error response
        response = self.agent._format_response("Error message", success=False)
        self.assertIn("Error message", response)
        
        # Check if conversation state was updated
        self.assertEqual(self.agent.conversation_state["last_response"], "Error message")

if __name__ == '__main__':
    unittest.main()
