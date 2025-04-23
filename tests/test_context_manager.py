"""
Unit tests for the context manager
"""

import unittest
import os
import json
from unittest.mock import patch, MagicMock
from utils.context_manager import PulseContext

class TestPulseContext(unittest.TestCase):
    """Test cases for the PulseContext class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = PulseContext(max_length=5, user_id="test_user")
    
    def test_init(self):
        """Test initialization"""
        self.assertEqual(self.context.user_id, "test_user")
        self.assertEqual(len(self.context.history), 0)
        self.assertEqual(self.context.history.maxlen, 5)
        self.assertIn("session_start", self.context.metadata)
        self.assertEqual(self.context.metadata["interaction_count"], 0)
    
    def test_update(self):
        """Test updating context"""
        self.context.update("Hello", "Hi there!")
        
        # Check history
        self.assertEqual(len(self.context.history), 2)
        self.assertEqual(self.context.history[0]["role"], "user")
        self.assertEqual(self.context.history[0]["content"], "Hello")
        self.assertEqual(self.context.history[1]["role"], "assistant")
        self.assertEqual(self.context.history[1]["content"], "Hi there!")
        
        # Check metadata
        self.assertEqual(self.context.metadata["interaction_count"], 1)
    
    def test_get_context(self):
        """Test getting context"""
        self.context.update("Hello", "Hi there!")
        self.context.update("How are you?", "I'm doing well!")
        
        context = self.context.get_context()
        
        # Check structure
        self.assertIn("history", context)
        self.assertIn("metadata", context)
        
        # Check history
        self.assertEqual(len(context["history"]), 4)
        self.assertEqual(context["history"][0]["content"], "Hello")
        self.assertEqual(context["history"][3]["content"], "I'm doing well!")
        
        # Check metadata
        self.assertEqual(context["metadata"]["interaction_count"], 2)
    
    def test_clear(self):
        """Test clearing context"""
        self.context.update("Hello", "Hi there!")
        self.context.clear()
        
        self.assertEqual(len(self.context.history), 0)
        self.assertEqual(self.context.metadata["interaction_count"], 0)
    
    def test_save_and_load(self):
        """Test saving and loading context"""
        self.context.update("Hello", "Hi there!")
        
        # Save to file
        test_file = "test_context.json"
        self.context.save_to_file(test_file)
        
        # Create a new context
        new_context = PulseContext(max_length=5, user_id="test_user")
        
        # Load from file
        new_context.load_from_file(test_file)
        
        # Check if loaded correctly
        self.assertEqual(len(new_context.history), 2)
        self.assertEqual(new_context.history[0]["content"], "Hello")
        self.assertEqual(new_context.metadata["interaction_count"], 1)
        
        # Clean up
        os.remove(test_file)
    
    def test_max_length(self):
        """Test max length enforcement"""
        # Add more items than max_length
        for i in range(10):
            self.context.update(f"User message {i}", f"Assistant response {i}")
        
        # Should only keep the last 5 interactions (10 messages)
        self.assertEqual(len(self.context.history), 10)
        self.assertEqual(self.context.history[0]["content"], "User message 5")
        self.assertEqual(self.context.history[9]["content"], "Assistant response 9")
    
    def test_infer_mood(self):
        """Test mood inference"""
        self.assertEqual(self.context._infer_mood("I need help with this code"), "hustling")
        self.assertEqual(self.context._infer_mood("Thanks for your help!"), "positive")
        self.assertEqual(self.context._infer_mood("I hate this error"), "negative")
        self.assertEqual(self.context._infer_mood("What is the time?"), "curious")
        self.assertEqual(self.context._infer_mood("Hello"), "neutral")

if __name__ == '__main__':
    unittest.main()
