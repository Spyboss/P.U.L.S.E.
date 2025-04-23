"""
SQLite Database Manager for General Pulse
Provides centralized database functionality for tasks, conversations, and caching
"""

import os
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from utils.logger import GeneralPulseLogger

class DBManager:
    """Manages SQLite database operations for General Pulse."""
    
    def __init__(self, db_path="memory/general_pulse.db"):
        """Initialize the database manager."""
        self.logger = GeneralPulseLogger("DBManager")
        self.logger.info("Initializing database manager")
        
        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        self.db_path = db_path
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize the database with required tables."""
        self.logger.info(f"Initializing database at {self.db_path}")
        
        # Create tables if they don't exist
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tasks table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                vibe_score REAL DEFAULT 0.0,
                vibe_analysis TEXT,
                priority TEXT DEFAULT 'medium',
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT
            )
            ''')
            
            # Subtasks table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS subtasks (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
            ''')
            
            # Agent responses table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_responses (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                subtask_id TEXT,
                agent TEXT NOT NULL,
                prompt TEXT,
                response TEXT,
                timestamp TEXT,
                metadata TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (subtask_id) REFERENCES subtasks(id)
            )
            ''')
            
            # Conversations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                summary TEXT,
                metadata TEXT
            )
            ''')
            
            # Messages table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT NOT NULL,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
            ''')
            
            # Cache table for model responses
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                model TEXT,
                created_at TEXT,
                expires_at TEXT
            )
            ''')
            
            conn.commit()
            self.logger.info("Database tables created successfully")
            
    def _get_connection(self):
        """Get a connection to the SQLite database."""
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            self.logger.error(f"Error connecting to database: {str(e)}", exc_info=True)
            raise
    
    #
    # Task Management Methods
    #
    
    def create_task(self, task_id, title, description=None, status="pending", metadata=None):
        """Create a new task in the database."""
        try:
            timestamp = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO tasks 
                    (id, title, description, status, created_at, updated_at, metadata) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        task_id, 
                        title, 
                        description, 
                        status, 
                        timestamp, 
                        timestamp, 
                        json.dumps(metadata) if metadata else None
                    )
                )
                conn.commit()
                
            self.logger.info(f"Created task: {task_id} - {title}")
            return {"success": True, "task_id": task_id}
        except Exception as e:
            self.logger.error(f"Error creating task: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def create_subtask(self, subtask_id, task_id, title, description=None, status="pending"):
        """Create a new subtask for a task."""
        try:
            timestamp = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO subtasks 
                    (id, task_id, title, description, status, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        subtask_id, 
                        task_id, 
                        title, 
                        description, 
                        status, 
                        timestamp, 
                        timestamp
                    )
                )
                conn.commit()
                
            self.logger.info(f"Created subtask: {subtask_id} for task {task_id} - {title}")
            return {"success": True, "subtask_id": subtask_id}
        except Exception as e:
            self.logger.error(f"Error creating subtask: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def update_task_status(self, task_id, status):
        """Update the status of a task."""
        try:
            timestamp = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    UPDATE tasks 
                    SET status = ?, updated_at = ? 
                    WHERE id = ?
                    ''',
                    (status, timestamp, task_id)
                )
                conn.commit()
                
            self.logger.info(f"Updated task {task_id} status to {status}")
            return {"success": True}
        except Exception as e:
            self.logger.error(f"Error updating task status: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def update_subtask_status(self, subtask_id, status):
        """Update the status of a subtask."""
        try:
            timestamp = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    UPDATE subtasks 
                    SET status = ?, updated_at = ? 
                    WHERE id = ?
                    ''',
                    (status, timestamp, subtask_id)
                )
                conn.commit()
                
            self.logger.info(f"Updated subtask {subtask_id} status to {status}")
            return {"success": True}
        except Exception as e:
            self.logger.error(f"Error updating subtask status: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def update_task_vibe(self, task_id, vibe_score, vibe_analysis=None):
        """Update the vibe score and analysis of a task."""
        try:
            timestamp = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    UPDATE tasks 
                    SET vibe_score = ?, vibe_analysis = ?, updated_at = ? 
                    WHERE id = ?
                    ''',
                    (vibe_score, vibe_analysis, timestamp, task_id)
                )
                conn.commit()
                
            self.logger.info(f"Updated task {task_id} vibe score to {vibe_score}")
            return {"success": True}
        except Exception as e:
            self.logger.error(f"Error updating task vibe: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def add_agent_response(self, response_id, agent, prompt, response, task_id=None, subtask_id=None, metadata=None):
        """Add an agent response to a task or subtask."""
        try:
            timestamp = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO agent_responses 
                    (id, task_id, subtask_id, agent, prompt, response, timestamp, metadata) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        response_id, 
                        task_id, 
                        subtask_id, 
                        agent, 
                        prompt, 
                        response, 
                        timestamp, 
                        json.dumps(metadata) if metadata else None
                    )
                )
                conn.commit()
                
            self.logger.info(f"Added {agent} response for task {task_id}, subtask {subtask_id}")
            return {"success": True, "response_id": response_id}
        except Exception as e:
            self.logger.error(f"Error adding agent response: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def get_tasks(self, status=None):
        """Get all tasks, optionally filtered by status."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute(
                        '''
                        SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC
                        ''',
                        (status,)
                    )
                else:
                    cursor.execute(
                        '''
                        SELECT * FROM tasks ORDER BY created_at DESC
                        '''
                    )
                    
                columns = [column[0] for column in cursor.description]
                tasks = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Parse JSON metadata
                for task in tasks:
                    if task.get('metadata'):
                        task['metadata'] = json.loads(task['metadata'])
                
                return tasks
        except Exception as e:
            self.logger.error(f"Error getting tasks: {str(e)}", exc_info=True)
            return []
    
    def get_subtasks(self, task_id=None, status=None):
        """Get subtasks, optionally filtered by task_id and/or status."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if task_id and status:
                    cursor.execute(
                        '''
                        SELECT * FROM subtasks WHERE task_id = ? AND status = ? ORDER BY created_at ASC
                        ''',
                        (task_id, status)
                    )
                elif task_id:
                    cursor.execute(
                        '''
                        SELECT * FROM subtasks WHERE task_id = ? ORDER BY created_at ASC
                        ''',
                        (task_id,)
                    )
                elif status:
                    cursor.execute(
                        '''
                        SELECT * FROM subtasks WHERE status = ? ORDER BY created_at ASC
                        ''',
                        (status,)
                    )
                else:
                    cursor.execute(
                        '''
                        SELECT * FROM subtasks ORDER BY created_at ASC
                        '''
                    )
                    
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting subtasks: {str(e)}", exc_info=True)
            return []
    
    def get_agent_responses(self, task_id=None, subtask_id=None, agent=None):
        """Get agent responses, optionally filtered by task_id, subtask_id, and/or agent."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM agent_responses"
                params = []
                
                if task_id or subtask_id or agent:
                    query += " WHERE"
                    conditions = []
                    
                    if task_id:
                        conditions.append("task_id = ?")
                        params.append(task_id)
                    
                    if subtask_id:
                        conditions.append("subtask_id = ?")
                        params.append(subtask_id)
                    
                    if agent:
                        conditions.append("agent = ?")
                        params.append(agent)
                    
                    query += " " + " AND ".join(conditions)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                    
                columns = [column[0] for column in cursor.description]
                responses = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Parse JSON metadata
                for response in responses:
                    if response.get('metadata'):
                        response['metadata'] = json.loads(response['metadata'])
                
                return responses
        except Exception as e:
            self.logger.error(f"Error getting agent responses: {str(e)}", exc_info=True)
            return []
    
    #
    # Conversation Methods
    #
    
    def create_conversation(self, conversation_id, metadata=None):
        """Create a new conversation."""
        try:
            timestamp = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO conversations 
                    (id, start_time, metadata) 
                    VALUES (?, ?, ?)
                    ''',
                    (
                        conversation_id, 
                        timestamp, 
                        json.dumps(metadata) if metadata else None
                    )
                )
                conn.commit()
                
            self.logger.info(f"Created conversation: {conversation_id}")
            return {"success": True, "conversation_id": conversation_id}
        except Exception as e:
            self.logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def add_message(self, message_id, conversation_id, role, content):
        """Add a message to a conversation."""
        try:
            timestamp = datetime.now().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO messages 
                    (id, conversation_id, role, content, timestamp) 
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        message_id, 
                        conversation_id, 
                        role, 
                        content, 
                        timestamp
                    )
                )
                conn.commit()
                
            self.logger.info(f"Added {role} message to conversation {conversation_id}")
            return {"success": True, "message_id": message_id}
        except Exception as e:
            self.logger.error(f"Error adding message: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def get_conversation(self, conversation_id):
        """Get a conversation by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get conversation details
                cursor.execute(
                    '''
                    SELECT * FROM conversations WHERE id = ?
                    ''',
                    (conversation_id,)
                )
                
                conversation_row = cursor.fetchone()
                if not conversation_row:
                    return None
                
                conversation_columns = [column[0] for column in cursor.description]
                conversation = dict(zip(conversation_columns, conversation_row))
                
                # Parse JSON metadata
                if conversation.get('metadata'):
                    conversation['metadata'] = json.loads(conversation['metadata'])
                
                # Get messages
                cursor.execute(
                    '''
                    SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC
                    ''',
                    (conversation_id,)
                )
                
                message_columns = [column[0] for column in cursor.description]
                messages = [dict(zip(message_columns, row)) for row in cursor.fetchall()]
                
                conversation['messages'] = messages
                
                return conversation
        except Exception as e:
            self.logger.error(f"Error getting conversation: {str(e)}", exc_info=True)
            return None
    
    def get_conversations(self, limit=10):
        """Get recent conversations."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    '''
                    SELECT * FROM conversations ORDER BY start_time DESC LIMIT ?
                    ''',
                    (limit,)
                )
                
                columns = [column[0] for column in cursor.description]
                conversations = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Parse JSON metadata
                for conversation in conversations:
                    if conversation.get('metadata'):
                        conversation['metadata'] = json.loads(conversation['metadata'])
                
                return conversations
        except Exception as e:
            self.logger.error(f"Error getting conversations: {str(e)}", exc_info=True)
            return []
    
    #
    # Cache Methods
    #
    
    def cache_set(self, key, value, model=None, expires_after=86400):
        """Set a value in the cache."""
        try:
            created_at = datetime.now().isoformat()
            expires_at = (datetime.now().timestamp() + expires_after)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete existing entry if it exists
                cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                
                # Insert new entry
                cursor.execute(
                    '''
                    INSERT INTO cache 
                    (key, value, model, created_at, expires_at) 
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        key, 
                        value, 
                        model, 
                        created_at, 
                        expires_at
                    )
                )
                conn.commit()
                
            self.logger.debug(f"Cached value for key: {key}")
            return {"success": True}
        except Exception as e:
            self.logger.error(f"Error setting cache: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def cache_get(self, key):
        """Get a value from the cache."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    '''
                    SELECT * FROM cache WHERE key = ? AND expires_at > ?
                    ''',
                    (key, datetime.now().timestamp())
                )
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
        except Exception as e:
            self.logger.error(f"Error getting from cache: {str(e)}", exc_info=True)
            return None
    
    def cache_delete(self, key):
        """Delete a value from the cache."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                
            self.logger.debug(f"Deleted cache entry for key: {key}")
            return {"success": True}
        except Exception as e:
            self.logger.error(f"Error deleting from cache: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def cache_clear_expired(self):
        """Clear expired cache entries."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM cache WHERE expires_at < ?", 
                    (datetime.now().timestamp(),)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                
            self.logger.info(f"Cleared {deleted_count} expired cache entries")
            return {"success": True, "deleted_count": deleted_count}
        except Exception as e:
            self.logger.error(f"Error clearing expired cache: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

# Create a default instance
db_manager = DBManager() 