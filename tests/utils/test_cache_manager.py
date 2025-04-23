import unittest
import os
import time
import json
import tempfile
from utils.cache_manager import CacheManager, get_cache_manager

class TestCacheManager(unittest.TestCase):
    """Test suite for CacheManager"""
    
    def setUp(self):
        """Create a temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.cache = CacheManager(db_path=self.temp_db.name, default_ttl=10)  # 10 seconds TTL for testing
    
    def tearDown(self):
        """Clean up temporary database"""
        self.cache.close()
        try:
            if os.path.exists(self.temp_db.name):
                os.unlink(self.temp_db.name)
        except (PermissionError, OSError):
            # On Windows, we may not be able to delete the file immediately
            # due to it being still in use
            pass
    
    def test_set_and_get(self):
        """Test setting and getting values from cache"""
        # Set test data
        test_key = "test_key"
        test_data = {"name": "test", "value": 123}
        
        # Store in cache
        result = self.cache.set(test_key, test_data)
        self.assertTrue(result)
        
        # Retrieve from cache
        cached_data = self.cache.get(test_key)
        self.assertEqual(cached_data, test_data)
    
    def test_key_types(self):
        """Test different key types"""
        # Test with different key types
        keys_and_values = [
            ("string_key", "string_value"),
            (123, "numeric_key"),
            ({"complex": "key"}, "complex_key_value"),
            (["list", "as", "key"], "list_key_value")
        ]
        
        for key, value in keys_and_values:
            # Store
            self.assertTrue(self.cache.set(key, value))
            # Retrieve
            self.assertEqual(self.cache.get(key), value)
    
    def test_ttl_expiration(self):
        """Test that items expire based on TTL"""
        # For this test, we'll manually check the get method's TTL check behavior
        key = "manual_expiration_test"
        
        # Insert directly into the database with an already-expired TTL
        timestamp = int(time.time()) - 10  # 10 seconds in the past
        ttl = 5  # 5 second TTL (already expired)
        
        # Generate hash for our key
        hash_key = self.cache._generate_hash(key)
        
        # Insert data directly
        self.cache.conn.execute(
            'INSERT INTO responses (hash, response, timestamp, ttl) VALUES (?, ?, ?, ?)',
            (hash_key, json.dumps("test_value"), timestamp, ttl)
        )
        self.cache.conn.commit()
        
        # Now when we try to get it, it should return None due to TTL check
        self.assertIsNone(self.cache.get(key))
        
        # Insert a non-expired entry
        fresh_key = "fresh_test"
        self.cache.set(fresh_key, "fresh_value", ttl=30)
        
        # This one should be accessible
        self.assertEqual(self.cache.get(fresh_key), "fresh_value")
    
    def test_invalidate(self):
        """Test invalidating cache entries"""
        # Set test data
        self.cache.set("to_invalidate", "soon_gone")
        
        # Verify it exists
        self.assertEqual(self.cache.get("to_invalidate"), "soon_gone")
        
        # Invalidate
        self.assertTrue(self.cache.invalidate("to_invalidate"))
        
        # Should be gone
        self.assertIsNone(self.cache.get("to_invalidate"))
    
    def test_clear(self):
        """Test clearing the cache"""
        # Add multiple items with explicit keys
        key1 = "test_clear_1"
        key2 = "test_clear_2" 
        key3 = "different_key"
        
        self.cache.set(key1, "value1")
        self.cache.set(key2, "value2")
        self.cache.set(key3, "value3")
        
        # Verify items exist
        self.assertEqual(self.cache.get(key1), "value1")
        self.assertEqual(self.cache.get(key2), "value2")
        
        # Clear specific items directly
        self.cache.invalidate(key1)
        self.cache.invalidate(key2)
        
        # Check that the items are gone
        self.assertIsNone(self.cache.get(key1))
        self.assertIsNone(self.cache.get(key2))
        
        # But the other item should still be there
        self.assertEqual(self.cache.get(key3), "value3")
        
        # Clear everything
        cleared = self.cache.clear()
        self.assertGreaterEqual(cleared, 1)  # At least the remaining key should be cleared
        
        # All should be gone
        self.assertIsNone(self.cache.get(key3))
    
    def test_clear_expired(self):
        """Test clearing expired entries"""
        # Insert an entry directly with expired timestamp
        expired_key = "direct_expired_test"
        hash_key = self.cache._generate_hash(expired_key)
        timestamp = int(time.time()) - 100  # 100 seconds in the past
        ttl = 5  # 5 second TTL (already expired)
        
        # Insert data directly
        self.cache.conn.execute(
            'INSERT INTO responses (hash, response, timestamp, ttl) VALUES (?, ?, ?, ?)',
            (hash_key, json.dumps("expired_value"), timestamp, ttl)
        )
        self.cache.conn.commit()
        
        # Verify the entry exists in the database
        cursor = self.cache.conn.execute(
            'SELECT COUNT(*) FROM responses WHERE hash = ?',
            (hash_key,)
        )
        self.assertEqual(cursor.fetchone()[0], 1)
        
        # Set a non-expired entry
        self.cache.set("expires_slow", "stays", ttl=30)
        
        # Clear expired entries
        cleared = self.cache.clear_expired()
        
        # Should have removed the expired entry
        self.assertGreaterEqual(cleared, 1)
        
        # Check the expected items
        self.assertIsNone(self.cache.get(expired_key))
        self.assertEqual(self.cache.get("expires_slow"), "stays")
    
    def test_get_stats(self):
        """Test getting cache statistics"""
        # Add some items
        self.cache.set("stat_test1", "value1")
        self.cache.set("stat_test2", "value2")
        
        # Get stats
        stats = self.cache.get_stats()
        
        # Verify stats
        self.assertIn("total_entries", stats)
        self.assertIn("valid_entries", stats)
        self.assertGreaterEqual(stats["total_entries"], 2)
        self.assertGreaterEqual(stats["valid_entries"], 2)
    
    def test_singleton(self):
        """Test the singleton pattern of get_cache_manager"""
        # For this test, we need a separate CacheManager that doesn't use our test DB
        # to avoid interfering with other tests (and to prevent file locking issues)
        try:
            # Create a unique temp file name
            temp_filename = os.path.join(tempfile.gettempdir(), f"test_cache_{int(time.time())}.db")
            
            # Get two instances with the same path
            instance1 = get_cache_manager(temp_filename)
            instance2 = get_cache_manager(temp_filename)
            
            # They should be the same object
            self.assertIs(instance1, instance2)
            
            # Use one instance to store data
            instance1.set("singleton_test", "shared_value")
            
            # Access it from the other instance
            self.assertEqual(instance2.get("singleton_test"), "shared_value")
            
            # Clean up
            instance1.close()
            
            # Wait a bit before trying to delete
            time.sleep(0.1)
            
            if os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except (PermissionError, OSError):
                    # May still be locked on Windows
                    pass
                    
        finally:
            # Reset the singleton for other tests
            from utils.cache_manager import _cache_instance
            globals()["_cache_instance"] = None
    
    def test_large_values(self):
        """Test caching of large values"""
        # Create a large string
        large_string = "x" * 100000  # 100KB string
        
        # Cache it
        self.assertTrue(self.cache.set("large_value", large_string))
        
        # Get it back
        retrieved = self.cache.get("large_value")
        self.assertEqual(len(retrieved), len(large_string))
        self.assertEqual(retrieved, large_string)
    
    def test_json_serialization(self):
        """Test caching complex JSON-serializable objects"""
        complex_obj = {
            "string": "value",
            "number": 123.456,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3, "four"],
            "nested": {
                "inner": "value",
                "list": [{"a": 1}, {"b": 2}]
            }
        }
        
        # Cache it
        self.assertTrue(self.cache.set("complex_json", complex_obj))
        
        # Get it back
        retrieved = self.cache.get("complex_json")
        self.assertEqual(retrieved, complex_obj)

if __name__ == '__main__':
    unittest.main() 