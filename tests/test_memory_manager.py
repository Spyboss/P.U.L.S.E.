"""
Unit tests for the memory manager
"""

import unittest
import os
import sqlite3
from utils.memory_manager import PulseMemory

class TestPulseMemory(unittest.TestCase):
    """Test cases for the PulseMemory class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use in-memory database for testing
        self.memory = PulseMemory(":memory:")
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.memory.close()
    
    def test_init(self):
        """Test initialization"""
        # Check if core identity was initialized
        creator = self.memory.recall("creator")
        self.assertIsNotNone(creator)
        self.assertEqual(creator, "Uminda H. Aberathne")
        
        # Check if user data was initialized
        projects = self.memory.get_user_data("projects")
        self.assertTrue(len(projects) > 0)
        
        # Check if goals were initialized
        goals = self.memory.get_active_goals()
        self.assertTrue(len(goals) > 0)
    
    def test_save_and_recall_identity(self):
        """Test saving and recalling identity"""
        # Save identity
        self.memory.save_identity("test_key", "test_value")
        
        # Recall identity
        value = self.memory.recall("test_key")
        self.assertEqual(value, "test_value")
        
        # Update identity
        self.memory.save_identity("test_key", "updated_value")
        
        # Recall updated identity
        value = self.memory.recall("test_key")
        self.assertEqual(value, "updated_value")
    
    def test_save_and_get_user_data(self):
        """Test saving and getting user data"""
        # Save user data
        self.memory.save_user_data("test_category", "test_data")
        
        # Get user data
        data = self.memory.get_user_data("test_category")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], "test_data")
        
        # Save more data to same category
        self.memory.save_user_data("test_category", "more_data")
        
        # Get updated user data
        data = self.memory.get_user_data("test_category")
        self.assertEqual(len(data), 2)
        self.assertIn("test_data", data)
        self.assertIn("more_data", data)
    
    def test_save_and_get_goals(self):
        """Test saving and getting goals"""
        # Save goal
        self.memory.save_goal("Test goal", priority=2, status="active")
        
        # Get active goals
        goals = self.memory.get_active_goals()
        test_goals = [g for g in goals if g["goal"] == "Test goal"]
        self.assertEqual(len(test_goals), 1)
        self.assertEqual(test_goals[0]["priority"], 2)
        
        # Update goal status
        goal_id = test_goals[0]["id"]
        self.memory.update_goal_status(goal_id, "completed")
        
        # Get active goals again
        goals = self.memory.get_active_goals()
        test_goals = [g for g in goals if g["goal"] == "Test goal"]
        self.assertEqual(len(test_goals), 0)  # Should no longer be active
        
        # Get all goals
        all_goals = self.memory.get_all_goals()
        test_goals = [g for g in all_goals if g["goal"] == "Test goal"]
        self.assertEqual(len(test_goals), 1)
        self.assertEqual(test_goals[0]["status"], "completed")
    
    def test_save_and_get_interactions(self):
        """Test saving and getting interactions"""
        # Save interaction
        self.memory.save_interaction("Test input", "Test response")
        
        # Get recent interactions
        interactions = self.memory.get_recent_interactions(limit=1)
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0]["user_input"], "Test input")
        self.assertEqual(interactions[0]["response"], "Test response")
    
    def test_search_memory(self):
        """Test searching memory"""
        # Add test data
        self.memory.save_user_data("test_category", "searchable content")
        self.memory.save_goal("Searchable goal", priority=1)
        self.memory.save_interaction("Search for this", "Found it")
        
        # Search for "search"
        results = self.memory.search_memory("search")
        
        # Check user data results
        self.assertTrue(len(results["user_data"]) > 0)
        self.assertTrue(any("searchable content" in item["data"] for item in results["user_data"]))
        
        # Check goal results
        self.assertTrue(len(results["goals"]) > 0)
        self.assertTrue(any("Searchable goal" in item["goal"] for item in results["goals"]))
        
        # Check interaction results
        self.assertTrue(len(results["interactions"]) > 0)
        self.assertTrue(any("Search for this" in item["user_input"] for item in results["interactions"]))
    
    def test_backup_and_restore(self):
        """Test backup and restore functionality"""
        # Add test data
        self.memory.save_identity("backup_test", "backup_value")
        
        # Create a backup file
        backup_file = "test_backup.db"
        self.memory.backup_memory(backup_file)
        
        # Create a new memory instance
        new_memory = PulseMemory(":memory:")
        
        # Restore from backup
        new_memory.restore_memory(backup_file)
        
        # Check if data was restored
        value = new_memory.recall("backup_test")
        self.assertEqual(value, "backup_value")
        
        # Clean up
        new_memory.close()
        os.remove(backup_file)

if __name__ == '__main__':
    unittest.main()
