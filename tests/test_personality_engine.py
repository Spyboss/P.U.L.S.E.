"""
Unit tests for the personality engine
"""

import unittest
import os
import json
from unittest.mock import patch, MagicMock
from utils.personality_engine import PulsePersonality

class TestPulsePersonality(unittest.TestCase):
    """Test cases for the PulsePersonality class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock memory and context
        self.mock_memory = MagicMock()
        self.mock_memory.recall.return_value = "Uminda H. Aberathne"
        self.mock_memory.get_active_goals.return_value = [{"goal": "Test goal", "priority": 1}]
        self.mock_memory.get_user_data.return_value = ["Test project"]
        
        self.mock_context = MagicMock()
        self.mock_context.get_context.return_value = {
            "history": [{"role": "user", "content": "Hello"}]
        }
        
        # Create personality instance
        self.personality = PulsePersonality(self.mock_memory, self.mock_context)
    
    def test_init(self):
        """Test initialization"""
        # Check if traits were initialized
        traits = self.personality.get_traits()
        self.assertIn("informative", traits)
        self.assertIn("courageous", traits)
        self.assertIn("positive", traits)
        self.assertIn("casual", traits)
        self.assertIn("strict", traits)
        
        # Check default mood
        self.assertEqual(self.personality.current_mood, "positive")
        self.assertAlmostEqual(self.personality.energy_level, 0.7, places=1)
    
    def test_get_system_prompt(self):
        """Test getting system prompt"""
        prompt = self.personality.get_system_prompt()
        
        # Check if prompt contains key elements
        self.assertIn("Uminda", prompt)
        self.assertIn("Test goal", prompt)
        self.assertIn("Test project", prompt)
        self.assertIn("JARVIS", prompt)
        self.assertIn("Core Traits", prompt)
    
    def test_format_response(self):
        """Test formatting responses"""
        # Test successful response
        response = self.personality.format_response("This is a test", context="tech", success=True)
        self.assertIn("This is a test", response)
        
        # Test error response
        response = self.personality.format_response("This is an error", context="tech", success=False)
        self.assertIn("This is an error", response)
    
    def test_remember_interaction(self):
        """Test remembering interactions"""
        self.personality.remember_interaction("Test input", "Test response")
        
        # Check if memory.save_interaction was called
        self.mock_memory.save_interaction.assert_called_once_with("Test input", "Test response")
    
    def test_update_mood(self):
        """Test updating mood"""
        # Test positive mood
        self.personality.update_mood("Thanks for your help!")
        self.assertEqual(self.personality.current_mood, "positive")
        self.assertGreater(self.personality.energy_level, 0.7)
        
        # Test negative mood
        self.personality.update_mood("I hate this error")
        self.assertEqual(self.personality.current_mood, "negative")
        self.assertLess(self.personality.energy_level, 0.7)
        
        # Test technical mood
        self.personality.update_mood("Help me debug this code")
        self.assertEqual(self.personality.current_mood, "technical")
        self.assertAlmostEqual(self.personality.energy_level, 0.7, places=1)
        
        # Test creative mood
        self.personality.update_mood("Let's brainstorm some ideas")
        self.assertEqual(self.personality.current_mood, "creative")
        self.assertGreater(self.personality.energy_level, 0.7)
    
    def test_adjust_traits(self):
        """Test adjusting traits"""
        # Get initial value
        initial_value = self.personality.traits["informative"]
        
        # Adjust trait
        self.personality.adjust_traits("informative", 0.9)
        
        # Check if trait was adjusted
        self.assertEqual(self.personality.traits["informative"], 0.9)
        
        # Check if memory.save_identity was called
        self.mock_memory.save_identity.assert_called_with("trait_informative", "0.9")
        
        # Test invalid trait
        self.personality.adjust_traits("invalid_trait", 0.5)
        self.assertNotIn("invalid_trait", self.personality.traits)
        
        # Test value clamping
        self.personality.adjust_traits("informative", 1.5)
        self.assertEqual(self.personality.traits["informative"], 1.0)
        
        self.personality.adjust_traits("informative", -0.5)
        self.assertEqual(self.personality.traits["informative"], 0.0)
    
    def test_get_traits(self):
        """Test getting traits"""
        traits = self.personality.get_traits()
        
        # Check if traits are returned
        self.assertIsInstance(traits, dict)
        self.assertIn("informative", traits)
        
        # Check if it's a copy (not the original)
        traits["informative"] = 0.1
        self.assertNotEqual(self.personality.traits["informative"], 0.1)
    
    def test_get_current_mood(self):
        """Test getting current mood"""
        mood_info = self.personality.get_current_mood()
        
        # Check structure
        self.assertIn("mood", mood_info)
        self.assertIn("energy_level", mood_info)
        
        # Check values
        self.assertEqual(mood_info["mood"], self.personality.current_mood)
        self.assertEqual(mood_info["energy_level"], self.personality.energy_level)
    
    def test_save_and_load(self):
        """Test saving and loading personality state"""
        # Adjust a trait
        self.personality.adjust_traits("informative", 0.9)
        
        # Set mood
        self.personality.current_mood = "technical"
        self.personality.energy_level = 0.8
        
        # Save to file
        test_file = "test_personality.json"
        self.personality.save_to_file(test_file)
        
        # Create a new personality
        new_personality = PulsePersonality()
        
        # Load from file
        new_personality.load_from_file(test_file)
        
        # Check if loaded correctly
        self.assertEqual(new_personality.traits["informative"], 0.9)
        self.assertEqual(new_personality.current_mood, "technical")
        self.assertEqual(new_personality.energy_level, 0.8)
        
        # Clean up
        os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
