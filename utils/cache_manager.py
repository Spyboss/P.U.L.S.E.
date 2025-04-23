"""
SQLite-based cache manager for General Pulse
Provides persistent caching with TTL for API responses
"""

import os
import sqlite3
import json
import hashlib
import time
from datetime import datetime
import logging
from typing import Any, Optional, Dict, Tuple

# Set up logger
logger = logging.getLogger(__name__)

class CacheManager:
    """
    SQLite-based cache manager with TTL support for API responses
    """
    
    def __init__(self, db_path: str = "cache.db", default_ttl: int = 3600):
        """
        Initialize the cache manager
        
        Args:
            db_path: Path to the SQLite database file
            default_ttl: Default time-to-live in seconds for cached items (1 hour)
        """
        self.db_path = db_path
        self.default_ttl = default_ttl
        self._init_db()
        
    def _init_db(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Create the responses table if it doesn't exist
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS responses (
                    hash TEXT PRIMARY KEY,
                    response TEXT,
                    timestamp INTEGER,
                    ttl INTEGER
                )
            ''')
            # Add index on timestamp for faster cleanup
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON responses (timestamp)')
            self.conn.commit()
            logger.info(f"Initialized cache database at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing cache database: {str(e)}")
            # Use in-memory DB as fallback
            self.conn = sqlite3.connect(":memory:")
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS responses (
                    hash TEXT PRIMARY KEY,
                    response TEXT,
                    timestamp INTEGER,
                    ttl INTEGER
                )
            ''')
            self.conn.commit()
            logger.warning("Using in-memory cache as fallback due to database error")
    
    def _generate_hash(self, key_data: Any) -> str:
        """
        Generate a hash from the provided data to use as a cache key
        
        Args:
            key_data: Data to hash (any JSON-serializable object)
            
        Returns:
            SHA-256 hash of the serialized data
        """
        # Convert key_data to a JSON string
        try:
            if isinstance(key_data, str):
                data_str = key_data
            else:
                data_str = json.dumps(key_data, sort_keys=True)
            # Generate SHA-256 hash
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error generating hash: {str(e)}")
            # Fallback to a string representation
            return hashlib.sha256(str(key_data).encode('utf-8')).hexdigest()
    
    def get(self, key: Any) -> Optional[Any]:
        """
        Get a value from the cache if not expired
        
        Args:
            key: Cache key (any JSON-serializable object)
            
        Returns:
            The cached value or None if not found or expired
        """
        hash_key = self._generate_hash(key)
        current_time = int(time.time())
        
        try:
            cursor = self.conn.execute(
                'SELECT response, timestamp, ttl FROM responses WHERE hash = ?', 
                (hash_key,)
            )
            row = cursor.fetchone()
            
            if row:
                response_str, timestamp, ttl = row
                
                # Check if entry is expired
                if current_time - timestamp > ttl:
                    logger.debug(f"Cache entry expired: {hash_key[:8]}...")
                    self.invalidate(key)
                    return None
                
                # Return the cached response
                try:
                    response = json.loads(response_str)
                    logger.debug(f"Cache hit: {hash_key[:8]}...")
                    return response
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in cache: {hash_key[:8]}...")
                    # Return the raw string if we can't parse it
                    return response_str
            
            logger.debug(f"Cache miss: {hash_key[:8]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    def set(self, key: Any, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in the cache
        
        Args:
            key: Cache key (any JSON-serializable object)
            value: Value to store (any JSON-serializable object)
            ttl: Time-to-live in seconds (uses default_ttl if None)
            
        Returns:
            True if successful, False otherwise
        """
        hash_key = self._generate_hash(key)
        timestamp = int(time.time())
        ttl = ttl or self.default_ttl
        
        try:
            # Serialize the value to JSON
            value_str = json.dumps(value)
            
            # Insert or replace the cache entry
            self.conn.execute(
                'INSERT OR REPLACE INTO responses (hash, response, timestamp, ttl) VALUES (?, ?, ?, ?)',
                (hash_key, value_str, timestamp, ttl)
            )
            self.conn.commit()
            logger.debug(f"Cached: {hash_key[:8]}... (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache value: {str(e)}")
            return False
    
    def invalidate(self, key: Any) -> bool:
        """
        Remove an entry from the cache
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        hash_key = self._generate_hash(key)
        
        try:
            self.conn.execute('DELETE FROM responses WHERE hash = ?', (hash_key,))
            self.conn.commit()
            logger.debug(f"Invalidated cache entry: {hash_key[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache entry: {str(e)}")
            return False
    
    def clear(self, prefix: Optional[str] = None) -> int:
        """
        Clear the cache
        
        Args:
            prefix: Optional prefix to selectively clear cache entries
            
        Returns:
            Number of entries cleared
        """
        try:
            if prefix:
                # Convert prefix to hash prefix if it's not already a hash
                if len(prefix) < 64:  # Not a full SHA-256 hash
                    prefix_hash = self._generate_hash(prefix)
                    # Use just the beginning of the hash for prefix matching
                    prefix = prefix_hash[:16]
                
                cursor = self.conn.execute('DELETE FROM responses WHERE hash LIKE ?', (f"{prefix}%",))
            else:
                cursor = self.conn.execute('DELETE FROM responses')
                
            self.conn.commit()
            row_count = cursor.rowcount
            logger.info(f"Cleared {row_count} cache entries{' with prefix ' + prefix if prefix else ''}")
            return row_count
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return 0
    
    def clear_expired(self) -> int:
        """
        Clear expired cache entries
        
        Returns:
            Number of entries cleared
        """
        current_time = int(time.time())
        
        try:
            cursor = self.conn.execute(
                'DELETE FROM responses WHERE (timestamp + ttl) < ?', 
                (current_time,)
            )
            self.conn.commit()
            row_count = cursor.rowcount
            logger.info(f"Cleared {row_count} expired cache entries")
            return row_count
            
        except Exception as e:
            logger.error(f"Error clearing expired cache: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # Get total count
            cursor = self.conn.execute('SELECT COUNT(*) FROM responses')
            total_count = cursor.fetchone()[0]
            
            # Get expired count
            current_time = int(time.time())
            cursor = self.conn.execute(
                'SELECT COUNT(*) FROM responses WHERE (timestamp + ttl) < ?', 
                (current_time,)
            )
            expired_count = cursor.fetchone()[0]
            
            # Get oldest and newest
            cursor = self.conn.execute('SELECT MIN(timestamp), MAX(timestamp) FROM responses')
            min_ts, max_ts = cursor.fetchone()
            
            # Get database size
            if self.db_path != ":memory:":
                db_size = os.path.getsize(self.db_path)
            else:
                db_size = 0
                
            return {
                "total_entries": total_count,
                "expired_entries": expired_count,
                "valid_entries": total_count - expired_count,
                "oldest_entry": datetime.fromtimestamp(min_ts).isoformat() if min_ts else None,
                "newest_entry": datetime.fromtimestamp(max_ts).isoformat() if max_ts else None,
                "db_size_bytes": db_size,
                "db_size_mb": round(db_size / (1024 * 1024), 2) if db_size > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {"error": str(e)}
    
    def close(self):
        """Close the database connection"""
        try:
            self.conn.close()
            logger.debug("Closed cache database connection")
        except Exception as e:
            logger.error(f"Error closing cache database: {str(e)}")

# Global cache instance
_cache_instance = None

def get_cache_manager(db_path: str = "cache.db", default_ttl: int = 3600) -> CacheManager:
    """
    Get the global cache manager instance (singleton pattern)
    
    Args:
        db_path: Path to the SQLite database file
        default_ttl: Default time-to-live in seconds
        
    Returns:
        CacheManager instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager(db_path, default_ttl)
    return _cache_instance 