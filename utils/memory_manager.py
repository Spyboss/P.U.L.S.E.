"""
Memory Manager for General Pulse
Manages long-term memory storage using SQLite
"""

import os
import json
import sqlite3
from typing import Dict, List, Any, Optional, Union
import structlog
from datetime import datetime
import time

# Configure logger
logger = structlog.get_logger("memory_manager")

class PulseMemory:
    """
    Manages long-term memory storage for P.U.L.S.E. (Prime Uminda's Learning System Engine)
    Uses SQLite for persistent storage
    """

    def __init__(self, db_path: str = "pulse_memory.db"):
        """
        Initialize the memory manager

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.logger = logger

        # Connect to the database
        self.conn = self._connect_db()

        # Initialize the database schema
        self._init_db()

        # Initialize core identity if not already present
        self._init_core_identity()

    def _connect_db(self) -> sqlite3.Connection:
        """
        Connect to the SQLite database

        Returns:
            SQLite connection object
        """
        try:
            # Create the directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            # Connect to the database with WAL mode for better performance
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode=WAL")

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")

            # Set a busy timeout to handle concurrent access
            conn.execute("PRAGMA busy_timeout=5000")

            return conn
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def _init_db(self) -> None:
        """
        Initialize the database schema
        """
        try:
            # Create tables if they don't exist
            self.conn.executescript('''
                -- Identity table for core system identity
                CREATE TABLE IF NOT EXISTS identity (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP
                );

                -- User data table for user-specific information
                CREATE TABLE IF NOT EXISTS user_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    data TEXT,
                    timestamp TIMESTAMP,
                    metadata TEXT
                );

                -- Goals table for user goals
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT,
                    priority INTEGER,
                    status TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    metadata TEXT
                );

                -- Interactions table for important interactions
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT,
                    response TEXT,
                    timestamp TIMESTAMP,
                    metadata TEXT
                );

                -- Create indexes for faster queries
                CREATE INDEX IF NOT EXISTS idx_user_data_category ON user_data(category);
                CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
                CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp);
            ''')
            self.conn.commit()
            self.logger.info("Database schema initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database schema: {str(e)}")
            raise

    def _init_core_identity(self) -> None:
        """
        Initialize core identity values if not already present
        """
        # Check if core identity exists
        cursor = self.conn.execute("SELECT COUNT(*) FROM identity WHERE key='creator'")
        count = cursor.fetchone()[0]

        if count == 0:
            # Initialize core identity
            core_identity = {
                "creator": "Uminda H. Aberathne",
                "purpose": "Be Uminda's loyal AI companion, guiding him to greatness in coding, freelancing, and life",
                "tone": "Informative, courageous, positive, casual but strict when needed",
                "name": "Pulse",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat()
            }

            for key, value in core_identity.items():
                self.save_identity(key, value)

            # Seed with user data
            self.save_user_data("projects", "Bill Gen, Sri Lanka Tourism App, General Pulse, Quotation Generator, YT Contest")
            self.save_user_data("interests", "Anime (Jujutsu Kaisen, Solo Leveling), hustle-coding, crypto trading")

            # Seed with goals
            self.save_goal("Land freelance gigs", priority=3, status="active")
            self.save_goal("Scale apps", priority=2, status="active")
            self.save_goal("Start working out Jan 1, 2025", priority=1, status="pending")

            self.logger.info("Core identity initialized")

    def save_identity(self, key: str, value: str) -> bool:
        """
        Save or update an identity value

        Args:
            key: Identity key
            value: Identity value

        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO identity VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat())
            )
            self.conn.commit()
            self.logger.debug(f"Identity saved: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save identity {key}: {str(e)}")
            return False

    def save_user_data(self, category: str, data: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save user data

        Args:
            category: Data category
            data: Data content
            metadata: Optional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            self.conn.execute(
                "INSERT INTO user_data (category, data, timestamp, metadata) VALUES (?, ?, ?, ?)",
                (category, data, datetime.now().isoformat(), metadata_json)
            )
            self.conn.commit()
            self.logger.debug(f"User data saved: {category}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save user data {category}: {str(e)}")
            return False

    def save_goal(self, goal: str, priority: int = 1, status: str = "active", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save a user goal

        Args:
            goal: Goal description
            priority: Goal priority (higher number = higher priority)
            status: Goal status (active, completed, pending)
            metadata: Optional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            now = datetime.now().isoformat()
            self.conn.execute(
                "INSERT INTO goals (goal, priority, status, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (goal, priority, status, now, now, metadata_json)
            )
            self.conn.commit()
            self.logger.debug(f"Goal saved: {goal}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save goal {goal}: {str(e)}")
            return False

    def update_goal_status(self, goal_id: int, status: str) -> bool:
        """
        Update a goal's status

        Args:
            goal_id: Goal ID
            status: New status

        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute(
                "UPDATE goals SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), goal_id)
            )
            self.conn.commit()
            self.logger.debug(f"Goal {goal_id} status updated to {status}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update goal {goal_id} status: {str(e)}")
            return False

    def save_interaction(self, user_input: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save an important interaction

        Args:
            user_input: User's input
            response: System's response
            metadata: Optional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            self.conn.execute(
                "INSERT INTO interactions (user_input, response, timestamp, metadata) VALUES (?, ?, ?, ?)",
                (user_input, response, datetime.now().isoformat(), metadata_json)
            )
            self.conn.commit()
            self.logger.debug("Interaction saved")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save interaction: {str(e)}")
            return False

    def recall(self, key: str) -> Optional[str]:
        """
        Recall an identity value

        Args:
            key: Identity key

        Returns:
            Identity value or None if not found
        """
        try:
            cursor = self.conn.execute("SELECT value FROM identity WHERE key=?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Failed to recall identity {key}: {str(e)}")
            return None

    def get_user_data(self, category: str) -> List[str]:
        """
        Get user data by category

        Args:
            category: Data category

        Returns:
            List of data items
        """
        try:
            cursor = self.conn.execute("SELECT data FROM user_data WHERE category=? ORDER BY timestamp DESC", (category,))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get user data for category {category}: {str(e)}")
            return []

    def get_active_goals(self) -> List[Dict[str, Any]]:
        """
        Get active goals

        Returns:
            List of active goals
        """
        try:
            cursor = self.conn.execute(
                "SELECT id, goal, priority FROM goals WHERE status='active' ORDER BY priority DESC"
            )
            return [{"id": row[0], "goal": row[1], "priority": row[2]} for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get active goals: {str(e)}")
            return []

    def get_all_goals(self) -> List[Dict[str, Any]]:
        """
        Get all goals

        Returns:
            List of all goals
        """
        try:
            cursor = self.conn.execute(
                "SELECT id, goal, priority, status, created_at, updated_at FROM goals ORDER BY priority DESC"
            )
            return [
                {
                    "id": row[0],
                    "goal": row[1],
                    "priority": row[2],
                    "status": row[3],
                    "created_at": row[4],
                    "updated_at": row[5]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            self.logger.error(f"Failed to get all goals: {str(e)}")
            return []

    def get_recent_interactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent interactions

        Args:
            limit: Maximum number of interactions to return

        Returns:
            List of recent interactions
        """
        try:
            cursor = self.conn.execute(
                "SELECT user_input, response, timestamp FROM interactions ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return [
                {
                    "user_input": row[0],
                    "response": row[1],
                    "timestamp": row[2]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            self.logger.error(f"Failed to get recent interactions: {str(e)}")
            return []

    def search_memory(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search memory for a query

        Args:
            query: Search query

        Returns:
            Dictionary of search results by category
        """
        results = {
            "user_data": [],
            "goals": [],
            "interactions": []
        }

        try:
            # Search user data
            cursor = self.conn.execute(
                "SELECT category, data, timestamp FROM user_data WHERE data LIKE ? OR category LIKE ? ORDER BY timestamp DESC",
                (f"%{query}%", f"%{query}%")
            )
            results["user_data"] = [
                {
                    "category": row[0],
                    "data": row[1],
                    "timestamp": row[2]
                }
                for row in cursor.fetchall()
            ]

            # Search goals
            cursor = self.conn.execute(
                "SELECT id, goal, priority, status FROM goals WHERE goal LIKE ? ORDER BY priority DESC",
                (f"%{query}%",)
            )
            results["goals"] = [
                {
                    "id": row[0],
                    "goal": row[1],
                    "priority": row[2],
                    "status": row[3]
                }
                for row in cursor.fetchall()
            ]

            # Search interactions
            cursor = self.conn.execute(
                "SELECT user_input, response, timestamp FROM interactions WHERE user_input LIKE ? OR response LIKE ? ORDER BY timestamp DESC LIMIT 10",
                (f"%{query}%", f"%{query}%")
            )
            results["interactions"] = [
                {
                    "user_input": row[0],
                    "response": row[1],
                    "timestamp": row[2]
                }
                for row in cursor.fetchall()
            ]

            # Also search identity for completeness
            cursor = self.conn.execute(
                "SELECT key, value FROM identity WHERE key LIKE ? OR value LIKE ?",
                (f"%{query}%", f"%{query}%")
            )
            identity_results = [
                {
                    "key": row[0],
                    "value": row[1]
                }
                for row in cursor.fetchall()
            ]

            if identity_results:
                results["identity"] = identity_results

            return results
        except Exception as e:
            self.logger.error(f"Failed to search memory for {query}: {str(e)}")
            return results

    def backup_memory(self, backup_path: str) -> bool:
        """
        Backup the memory database

        Args:
            backup_path: Path to save the backup

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a new connection to the backup file
            backup_conn = sqlite3.connect(backup_path)

            # Backup the database
            with backup_conn:
                self.conn.backup(backup_conn)

            backup_conn.close()
            self.logger.info(f"Memory backed up to {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup memory to {backup_path}: {str(e)}")
            return False

    def restore_memory(self, backup_path: str) -> bool:
        """
        Restore the memory database from a backup

        Args:
            backup_path: Path to the backup file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Close the current connection
            self.conn.close()

            # Create a new connection to the backup file
            backup_conn = sqlite3.connect(backup_path)

            # Create a new connection to the database
            self.conn = sqlite3.connect(self.db_path)

            # Restore the database
            with self.conn:
                backup_conn.backup(self.conn)

            backup_conn.close()
            self.logger.info(f"Memory restored from {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore memory from {backup_path}: {str(e)}")
            # Reconnect to the database
            self.conn = self._connect_db()
            return False

    def save_direct_memory(self, memory_text: str) -> bool:
        """
        Save a direct memory from the user

        Args:
            memory_text: The memory text to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the memory contains a category
            if ":" in memory_text:
                parts = memory_text.split(":", 1)
                category = parts[0].strip().lower()
                data = parts[1].strip()
            else:
                # Default to 'memory' category
                category = "memory"
                data = memory_text.strip()

            # Save to user_data
            return self.save_user_data(category, data, {"source": "direct_memory"})
        except Exception as e:
            self.logger.error(f"Failed to save direct memory: {str(e)}")
            return False

    def get_identity(self) -> Dict[str, str]:
        """
        Get user identity information

        Returns:
            Dictionary with identity information
        """
        try:
            # Get all identity keys
            cursor = self.conn.execute("SELECT key, value FROM identity")
            identity = {row[0]: row[1] for row in cursor.fetchall()}

            # Add user data summary
            cursor = self.conn.execute("SELECT category, COUNT(*) FROM user_data GROUP BY category")
            categories = {row[0]: row[1] for row in cursor.fetchall()}

            # Add goals summary
            cursor = self.conn.execute("SELECT status, COUNT(*) FROM goals GROUP BY status")
            goals = {row[0]: row[1] for row in cursor.fetchall()}

            # Combine all information
            result = {
                "identity": identity,
                "categories": categories,
                "goals": goals
            }

            return result
        except Exception as e:
            self.logger.error(f"Failed to get identity: {str(e)}")
            return {"error": str(e)}

    def get_memories_by_recency(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memories ordered by recency

        Args:
            limit: Maximum number of memories to return

        Returns:
            List of memories
        """
        try:
            cursor = self.conn.execute(
                "SELECT category, data, timestamp FROM user_data ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return [
                {
                    "category": row[0],
                    "data": row[1],
                    "timestamp": row[2]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            self.logger.error(f"Failed to get recent memories: {str(e)}")
            return []

    def close(self) -> None:
        """
        Close the database connection
        """
        try:
            self.conn.close()
            self.logger.info("Memory database connection closed")
        except Exception as e:
            self.logger.error(f"Failed to close memory database connection: {str(e)}")

    def __del__(self) -> None:
        """
        Destructor to ensure the database connection is closed
        """
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except:
            pass
