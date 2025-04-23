"""
Task Memory Manager for General Pulse

This module provides persistent storage and retrieval of task information,
agent responses, and project context using SQLite.
"""

import os
import sys
import json
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
import anyio

# Add parent directory to path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import default_logger as logger

class TaskMemoryManager:
    """
    Stores and retrieves task information, agent responses, and project context.
    Uses SQLite for persistent storage with methods for task creation, updating,
    querying, and summarizing.
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the task memory manager with database path.
        
        Args:
            db_path (str, optional): Path to SQLite database file.
                If None, defaults to 'tasks.db' in the memory directory.
        """
        if db_path is None:
            # Default to 'tasks.db' in the memory directory
            memory_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory")
            os.makedirs(memory_dir, exist_ok=True)
            db_path = os.path.join(memory_dir, "tasks.db")
        
        self.db_path = db_path
        self.conn = self._initialize_db()
        logger.info(f"Task Memory Manager initialized with database: {db_path}")
    
    def _initialize_db(self):
        """
        Initialize the SQLite database and create necessary tables if they don't exist.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create tasks table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            task_type TEXT DEFAULT 'general',
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 3,
            created_at TEXT,
            updated_at TEXT,
            due_date TEXT,
            created_by TEXT,
            assigned_to TEXT,
            tags TEXT,
            metadata TEXT,
            vibe_score INTEGER DEFAULT 0
        )
        """)
        
        # Create subtasks table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 3,
            created_at TEXT,
            updated_at TEXT,
            due_date TEXT,
            assigned_to TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
        """)
        
        # Create agent responses table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_responses (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            subtask_id TEXT,
            agent TEXT NOT NULL,
            response TEXT NOT NULL,
            response_type TEXT DEFAULT 'text',
            created_at TEXT,
            metadata TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (subtask_id) REFERENCES subtasks(id) ON DELETE CASCADE
        )
        """)
        
        # Create task history table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT,
            created_by TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
        """)
        
        conn.commit()
        return conn
    
    def create_task(self, name, description=None, task_type="general", priority=3, 
                    due_date=None, tags=None, created_by=None, assigned_to=None, metadata=None):
        """
        Create a new task and return its ID.
        
        Args:
            name (str): Task name
            description (str, optional): Task description
            task_type (str, optional): Type of task (e.g., 'code', 'content')
            priority (int, optional): Priority level (1-5, where 1 is highest)
            due_date (str, optional): Due date in ISO format
            tags (list, optional): List of tags
            created_by (str, optional): User who created the task
            assigned_to (str, optional): User the task is assigned to
            metadata (dict, optional): Additional metadata
            
        Returns:
            str: Task ID
        """
        task_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Serialize JSON fields
        tags_json = json.dumps(tags) if tags else None
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.conn.execute(
            """
            INSERT INTO tasks (
                id, name, description, task_type, priority, created_at, updated_at,
                due_date, created_by, assigned_to, tags, metadata, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id, name, description, task_type, priority, created_at, created_at,
                due_date, created_by, assigned_to, tags_json, metadata_json, "pending"
            )
        )
        
        # Log task creation in history
        self._add_task_history(task_id, "created", f"Task '{name}' created", created_by)
        
        self.conn.commit()
        logger.info(f"Created task: {name} (ID: {task_id})")
        
        return task_id
    
    def create_subtask(self, task_id, name, description=None, priority=3, 
                      due_date=None, assigned_to=None):
        """
        Create a subtask for a task.
        
        Args:
            task_id (str): Parent task ID
            name (str): Subtask name
            description (str, optional): Subtask description
            priority (int, optional): Priority level (1-5, where 1 is highest)
            due_date (str, optional): Due date in ISO format
            assigned_to (str, optional): User the subtask is assigned to
            
        Returns:
            str: Subtask ID
        """
        subtask_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        self.conn.execute(
            """
            INSERT INTO subtasks (
                id, task_id, name, description, priority, created_at, updated_at,
                due_date, assigned_to, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                subtask_id, task_id, name, description, priority, created_at, created_at,
                due_date, assigned_to, "pending"
            )
        )
        
        # Log subtask creation in history
        self._add_task_history(task_id, "subtask_created", f"Subtask '{name}' created")
        
        self.conn.commit()
        logger.info(f"Created subtask: {name} (ID: {subtask_id}) for task {task_id}")
        
        return subtask_id
    
    def add_agent_response(self, agent, response, task_id=None, subtask_id=None, 
                          response_type="text", metadata=None):
        """
        Store an agent's response to a task or subtask.
        
        Args:
            agent (str): Name of the agent (e.g., 'claude', 'deepseek')
            response (str): Agent's response
            task_id (str, optional): Task ID (required if subtask_id not provided)
            subtask_id (str, optional): Subtask ID
            response_type (str, optional): Type of response (e.g., 'text', 'code')
            metadata (dict, optional): Additional metadata
            
        Returns:
            str: Response ID
            
        Raises:
            ValueError: If neither task_id nor subtask_id is provided
        """
        if not task_id and not subtask_id:
            raise ValueError("Either task_id or subtask_id must be provided")
        
        response_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # If subtask_id is provided but not task_id, get the task_id
        if subtask_id and not task_id:
            cursor = self.conn.execute(
                "SELECT task_id FROM subtasks WHERE id = ?",
                (subtask_id,)
            )
            result = cursor.fetchone()
            if result:
                task_id = result[0]
        
        # Serialize metadata
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.conn.execute(
            """
            INSERT INTO agent_responses (
                id, task_id, subtask_id, agent, response, response_type,
                created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                response_id, task_id, subtask_id, agent, response, response_type,
                created_at, metadata_json
            )
        )
        
        # Log agent response in history
        action_details = f"Agent '{agent}' provided a {response_type} response"
        self._add_task_history(task_id, "agent_response", action_details)
        
        self.conn.commit()
        logger.debug(f"Added {agent} response for task {task_id or 'unknown'}, subtask {subtask_id or 'none'}")
        
        return response_id
    
    def update_task_status(self, task_id, status, updated_by=None):
        """
        Update the status of a task.
        
        Args:
            task_id (str): Task ID
            status (str): New status (e.g., 'pending', 'in_progress', 'completed')
            updated_by (str, optional): User who updated the task
            
        Returns:
            bool: True if successful, False otherwise
        """
        updated_at = datetime.now().isoformat()
        
        self.conn.execute(
            """
            UPDATE tasks
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, updated_at, task_id)
        )
        
        # Log status update in history
        self._add_task_history(task_id, "status_updated", f"Status changed to '{status}'", updated_by)
        
        self.conn.commit()
        logger.info(f"Updated task {task_id} status to {status}")
        
        return True
    
    def update_subtask_status(self, subtask_id, status, updated_by=None):
        """
        Update the status of a subtask.
        
        Args:
            subtask_id (str): Subtask ID
            status (str): New status (e.g., 'pending', 'in_progress', 'completed')
            updated_by (str, optional): User who updated the subtask
            
        Returns:
            bool: True if successful, False otherwise
        """
        updated_at = datetime.now().isoformat()
        
        # Get task_id for history logging
        cursor = self.conn.execute(
            "SELECT task_id FROM subtasks WHERE id = ?",
            (subtask_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            logger.error(f"Subtask {subtask_id} not found")
            return False
        
        task_id = result[0]
        
        self.conn.execute(
            """
            UPDATE subtasks
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, updated_at, subtask_id)
        )
        
        # Log status update in history
        details = f"Subtask {subtask_id} status changed to '{status}'"
        self._add_task_history(task_id, "subtask_status_updated", details, updated_by)
        
        self.conn.commit()
        logger.info(f"Updated subtask {subtask_id} status to {status}")
        
        return True
    
    def update_task_vibe_score(self, task_id, vibe_score, updated_by=None):
        """
        Update the vibe score of a task (Grok's trend relevance score).
        
        Args:
            task_id (str): Task ID
            vibe_score (int): Score from 1-10
            updated_by (str, optional): User or agent who updated the score
            
        Returns:
            bool: True if successful, False otherwise
        """
        updated_at = datetime.now().isoformat()
        
        self.conn.execute(
            """
            UPDATE tasks
            SET vibe_score = ?, updated_at = ?
            WHERE id = ?
            """,
            (vibe_score, updated_at, task_id)
        )
        
        # Log vibe score update in history
        details = f"Vibe score updated to {vibe_score}/10"
        self._add_task_history(task_id, "vibe_score_updated", details, updated_by)
        
        self.conn.commit()
        logger.info(f"Updated task {task_id} vibe score to {vibe_score}")
        
        return True
    
    def get_task(self, task_id):
        """
        Get detailed information about a task.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            dict: Task details or None if not found
        """
        cursor = self.conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        )
        
        columns = [column[0] for column in cursor.description]
        result = cursor.fetchone()
        
        if not result:
            return None
        
        # Convert to dictionary
        task = dict(zip(columns, result))
        
        # Parse JSON fields
        if task.get('tags'):
            task['tags'] = json.loads(task['tags'])
        
        if task.get('metadata'):
            task['metadata'] = json.loads(task['metadata'])
        
        return task
    
    def get_subtasks(self, task_id):
        """
        Get all subtasks for a task.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            list: List of subtask dictionaries
        """
        cursor = self.conn.execute(
            "SELECT * FROM subtasks WHERE task_id = ? ORDER BY priority, created_at",
            (task_id,)
        )
        
        columns = [column[0] for column in cursor.description]
        subtasks = []
        
        for row in cursor.fetchall():
            subtask = dict(zip(columns, row))
            subtasks.append(subtask)
        
        return subtasks
    
    def get_agent_responses(self, task_id=None, subtask_id=None, agent=None):
        """
        Get agent responses for a task or subtask.
        
        Args:
            task_id (str, optional): Task ID
            subtask_id (str, optional): Subtask ID
            agent (str, optional): Filter by agent name
            
        Returns:
            list: List of response dictionaries
            
        Raises:
            ValueError: If neither task_id nor subtask_id is provided
        """
        if not task_id and not subtask_id:
            raise ValueError("Either task_id or subtask_id must be provided")
        
        query = "SELECT * FROM agent_responses WHERE "
        params = []
        
        if task_id:
            query += "task_id = ? "
            params.append(task_id)
            
            if subtask_id:
                query += "AND subtask_id = ? "
                params.append(subtask_id)
        else:
            query += "subtask_id = ? "
            params.append(subtask_id)
        
        if agent:
            query += "AND agent = ? "
            params.append(agent)
        
        query += "ORDER BY created_at"
        
        cursor = self.conn.execute(query, params)
        
        columns = [column[0] for column in cursor.description]
        responses = []
        
        for row in cursor.fetchall():
            response = dict(zip(columns, row))
            
            # Parse metadata
            if response.get('metadata'):
                response['metadata'] = json.loads(response['metadata'])
                
            responses.append(response)
        
        return responses
    
    def get_task_history(self, task_id):
        """
        Get complete history of a task including all changes and events.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            list: List of history events
        """
        cursor = self.conn.execute(
            "SELECT * FROM task_history WHERE task_id = ? ORDER BY created_at",
            (task_id,)
        )
        
        columns = [column[0] for column in cursor.description]
        history = []
        
        for row in cursor.fetchall():
            event = dict(zip(columns, row))
            history.append(event)
        
        return history
    
    def list_tasks(self, status=None, task_type=None, assigned_to=None, limit=50):
        """
        List tasks with optional filtering.
        
        Args:
            status (str, optional): Filter by status
            task_type (str, optional): Filter by task type
            assigned_to (str, optional): Filter by assigned user
            limit (int, optional): Maximum number of tasks to return
            
        Returns:
            list: List of task dictionaries
        """
        query = "SELECT * FROM tasks WHERE 1=1 "
        params = []
        
        if status:
            query += "AND status = ? "
            params.append(status)
        
        if task_type:
            query += "AND task_type = ? "
            params.append(task_type)
        
        if assigned_to:
            query += "AND assigned_to = ? "
            params.append(assigned_to)
        
        query += "ORDER BY priority, created_at LIMIT ?"
        params.append(limit)
        
        cursor = self.conn.execute(query, params)
        
        columns = [column[0] for column in cursor.description]
        tasks = []
        
        for row in cursor.fetchall():
            task = dict(zip(columns, row))
            
            # Parse JSON fields
            if task.get('tags'):
                task['tags'] = json.loads(task['tags'])
            
            if task.get('metadata'):
                task['metadata'] = json.loads(task['metadata'])
                
            tasks.append(task)
        
        return tasks
    
    def get_task_summary(self, task_id):
        """
        Get a summary of a task including subtasks and recent responses.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            dict: Task summary or None if not found
        """
        task = self.get_task(task_id)
        
        if not task:
            return None
        
        subtasks = self.get_subtasks(task_id)
        
        # Get recent agent responses (limited to 10)
        cursor = self.conn.execute(
            """
            SELECT agent, response, response_type, created_at 
            FROM agent_responses 
            WHERE task_id = ? 
            ORDER BY created_at DESC LIMIT 10
            """,
            (task_id,)
        )
        
        recent_responses = []
        for row in cursor.fetchall():
            recent_responses.append({
                'agent': row[0],
                'response': row[1],
                'response_type': row[2],
                'created_at': row[3]
            })
        
        # Calculate subtask completion stats
        total_subtasks = len(subtasks)
        completed_subtasks = sum(1 for subtask in subtasks if subtask['status'] == 'completed')
        
        completion_percentage = 0
        if total_subtasks > 0:
            completion_percentage = (completed_subtasks / total_subtasks) * 100
        
        return {
            'task': task,
            'subtasks': subtasks,
            'recent_responses': recent_responses,
            'stats': {
                'total_subtasks': total_subtasks,
                'completed_subtasks': completed_subtasks,
                'completion_percentage': completion_percentage,
                'vibe_score': task.get('vibe_score', 0)
            }
        }
    
    def predict_next_actions(self, task_id):
        """
        Based on task history and patterns, predict likely next actions.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            list: List of suggested next actions
        """
        task = self.get_task(task_id)
        
        if not task:
            return []
        
        suggested_actions = []
        
        # Get subtasks
        subtasks = self.get_subtasks(task_id)
        
        # Check for incomplete subtasks
        incomplete_subtasks = [s for s in subtasks if s['status'] != 'completed']
        if incomplete_subtasks:
            for subtask in incomplete_subtasks:
                suggested_actions.append({
                    'type': 'complete_subtask',
                    'id': subtask['id'],
                    'name': subtask['name'],
                    'priority': subtask['priority']
                })
        
        # Check if we need agent responses
        agent_responses = self.get_agent_responses(task_id=task_id)
        agents_used = set(resp['agent'] for resp in agent_responses)
        
        # Suggest missing agents based on task type
        if task['task_type'] == 'code' and 'deepseek' not in agents_used:
            suggested_actions.append({
                'type': 'get_agent_response',
                'agent': 'deepseek',
                'reason': 'Technical expertise needed for code task'
            })
        
        if task['task_type'] in ['content', 'writing'] and 'claude' not in agents_used:
            suggested_actions.append({
                'type': 'get_agent_response',
                'agent': 'claude',
                'reason': 'Content generation recommended for this task type'
            })
        
        if 'grok' not in agents_used:
            suggested_actions.append({
                'type': 'get_agent_response',
                'agent': 'grok',
                'reason': 'Trend analysis and vibe check needed'
            })
        
        # Sort suggested actions by priority
        suggested_actions.sort(key=lambda x: x.get('priority', 5))
        
        return suggested_actions
    
    def search_tasks(self, query):
        """
        Search for tasks by name, description, or tags.
        
        Args:
            query (str): Search query
            
        Returns:
            list: List of matching task dictionaries
        """
        # SQLite doesn't support JSON search directly, so we'll use LIKE for basic search
        search_term = f"%{query}%"
        
        cursor = self.conn.execute(
            """
            SELECT * FROM tasks
            WHERE name LIKE ? OR description LIKE ? OR tags LIKE ?
            ORDER BY updated_at DESC
            """,
            (search_term, search_term, search_term)
        )
        
        columns = [column[0] for column in cursor.description]
        tasks = []
        
        for row in cursor.fetchall():
            task = dict(zip(columns, row))
            
            # Parse JSON fields
            if task.get('tags'):
                task['tags'] = json.loads(task['tags'])
            
            if task.get('metadata'):
                task['metadata'] = json.loads(task['metadata'])
                
            tasks.append(task)
        
        return tasks
    
    def _add_task_history(self, task_id, action, details, created_by=None):
        """
        Add an entry to the task history.
        
        Args:
            task_id (str): Task ID
            action (str): Action performed
            details (str): Action details
            created_by (str, optional): User who performed the action
        """
        history_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        self.conn.execute(
            """
            INSERT INTO task_history (
                id, task_id, action, details, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (history_id, task_id, action, details, created_at, created_by)
        )
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Closed database connection")

    async def create_task_async(self, name, description, task_type="general", priority=1, tags=None, due_date=None):
        """
        Asynchronous version of create_task.
        Creates a new task in the database.
        
        Args:
            name (str): Name of the task
            description (str): Detailed description of the task
            task_type (str): Type of task (code, research, writing, etc.)
            priority (int): Priority level (1-3, where 1 is highest)
            tags (list): List of tags associated with the task
            due_date (str): Due date in ISO format
            
        Returns:
            str: ID of the created task
        """
        task_id = self._generate_id()
        created_at = self._get_timestamp()
        
        task = {
            "id": task_id,
            "name": name,
            "description": description,
            "task_type": task_type,
            "priority": priority,
            "tags": tags or [],
            "status": "pending",
            "created_at": created_at,
            "updated_at": created_at,
            "completed_at": None,
            "due_date": due_date,
            "vibe_score": 0,
            "vibe_analysis": "",
            "subtasks": [],
            "agent_responses": []
        }
        
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(self._async_insert_task, task)
            
            self.logger.info(f"Created task: {name} with ID: {task_id}")
            return task_id
        except Exception as e:
            self.logger.error(f"Error creating task: {str(e)}")
            return None
    
    async def _async_insert_task(self, task):
        """Helper method to insert a task asynchronously."""
        try:
            self.db.tasks.insert_one(task)
        except Exception as e:
            self.logger.error(f"Database error while inserting task: {str(e)}")
            raise e
    
    async def create_subtask_async(self, task_id, name, description, priority=1, due_date=None):
        """
        Asynchronous version of create_subtask.
        Creates a subtask for an existing task.
        
        Args:
            task_id (str): ID of the parent task
            name (str): Name of the subtask
            description (str): Detailed description of the subtask
            priority (int): Priority level (1-3, where 1 is highest)
            due_date (str): Due date in ISO format
            
        Returns:
            str: ID of the created subtask
        """
        subtask_id = self._generate_id()
        created_at = self._get_timestamp()
        
        subtask = {
            "id": subtask_id,
            "name": name,
            "description": description,
            "priority": priority,
            "status": "pending",
            "created_at": created_at,
            "updated_at": created_at,
            "completed_at": None,
            "due_date": due_date
        }
        
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(self._async_add_subtask, task_id, subtask)
            
            self.logger.info(f"Created subtask: {name} with ID: {subtask_id} for task: {task_id}")
            return subtask_id
        except Exception as e:
            self.logger.error(f"Error creating subtask: {str(e)}")
            return None
    
    async def _async_add_subtask(self, task_id, subtask):
        """Helper method to add a subtask asynchronously."""
        try:
            self.db.tasks.update_one(
                {"id": task_id},
                {"$push": {"subtasks": subtask}}
            )
        except Exception as e:
            self.logger.error(f"Database error while adding subtask: {str(e)}")
            raise e
    
    async def add_agent_response_async(self, agent, response, task_id, subtask_id=None, response_type="text"):
        """
        Asynchronous version of add_agent_response.
        Adds a model/agent response to a task or subtask.
        
        Args:
            agent (str): Name of the agent/model (claude, grok, deepseek, etc.)
            response (str): The response content
            task_id (str): ID of the task
            subtask_id (str, optional): ID of the subtask, if applicable
            response_type (str): Type of response (text, json, code, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        timestamp = self._get_timestamp()
        
        agent_response = {
            "id": self._generate_id(),
            "agent": agent,
            "response": response,
            "subtask_id": subtask_id,
            "response_type": response_type,
            "timestamp": timestamp
        }
        
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(self._async_add_agent_response, task_id, agent_response)
            
            self.logger.info(f"Added {agent} response to task: {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding agent response: {str(e)}")
            return False
    
    async def _async_add_agent_response(self, task_id, agent_response):
        """Helper method to add an agent response asynchronously."""
        try:
            self.db.tasks.update_one(
                {"id": task_id},
                {"$push": {"agent_responses": agent_response}}
            )
        except Exception as e:
            self.logger.error(f"Database error while adding agent response: {str(e)}")
            raise e
    
    async def update_task_vibe_score_async(self, task_id, vibe_score, source, vibe_analysis=None):
        """
        Asynchronous version of update_task_vibe_score.
        Updates the vibe score and analysis of a task.
        
        Args:
            task_id (str): ID of the task
            vibe_score (int): The vibe score (1-10)
            source (str): Source of the vibe score (agent name)
            vibe_analysis (str, optional): Analysis explaining the vibe score
            
        Returns:
            bool: True if successful, False otherwise
        """
        updated_at = self._get_timestamp()
        
        update_data = {
            "vibe_score": vibe_score,
            "updated_at": updated_at
        }
        
        if vibe_analysis:
            update_data["vibe_analysis"] = vibe_analysis
        
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(self._async_update_task, task_id, update_data)
            
            self.logger.info(f"Updated vibe score for task {task_id} to {vibe_score} from {source}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating task vibe score: {str(e)}")
            return False
    
    async def _async_update_task(self, task_id, update_data):
        """Helper method to update a task asynchronously."""
        try:
            self.db.tasks.update_one(
                {"id": task_id},
                {"$set": update_data}
            )
        except Exception as e:
            self.logger.error(f"Database error while updating task: {str(e)}")
            raise e
    
    async def update_subtask_status_async(self, subtask_id, status):
        """
        Asynchronous version of update_subtask_status.
        Updates the status of a subtask.
        
        Args:
            subtask_id (str): ID of the subtask
            status (str): New status (pending, in_progress, completed, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        updated_at = self._get_timestamp()
        completed_at = self._get_timestamp() if status == "completed" else None
        
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(self._async_update_subtask, subtask_id, status, updated_at, completed_at)
            
            self.logger.info(f"Updated subtask {subtask_id} status to {status}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating subtask status: {str(e)}")
            return False
    
    async def _async_update_subtask(self, subtask_id, status, updated_at, completed_at):
        """Helper method to update a subtask asynchronously."""
        try:
            update_fields = {
                "subtasks.$.status": status,
                "subtasks.$.updated_at": updated_at
            }
            
            if completed_at:
                update_fields["subtasks.$.completed_at"] = completed_at
            
            self.db.tasks.update_one(
                {"subtasks.id": subtask_id},
                {"$set": update_fields}
            )
        except Exception as e:
            self.logger.error(f"Database error while updating subtask: {str(e)}")
            raise e
    
    async def get_agent_responses_async(self, task_id=None, subtask_id=None, agent=None):
        """
        Asynchronous version of get_agent_responses.
        Gets agent responses for a task or subtask.
        
        Args:
            task_id (str, optional): ID of the task
            subtask_id (str, optional): ID of the subtask
            agent (str, optional): Name of the agent
            
        Returns:
            list: List of agent responses
        """
        try:
            if not task_id:
                return []
            
            task = await self._async_get_task(task_id)
            if not task:
                return []
            
            responses = task.get("agent_responses", [])
            
            # Filter by subtask if provided
            if subtask_id:
                responses = [r for r in responses if r.get("subtask_id") == subtask_id]
                
            # Filter by agent if provided
            if agent:
                responses = [r for r in responses if r.get("agent") == agent]
                
            return responses
        except Exception as e:
            self.logger.error(f"Error getting agent responses: {str(e)}")
            return []
    
    async def _async_get_task(self, task_id):
        """Helper method to get a task asynchronously."""
        try:
            return self.db.tasks.find_one({"id": task_id})
        except Exception as e:
            self.logger.error(f"Database error while getting task: {str(e)}")
            return None

    # Add other async methods as needed for concurrent operations

    def add_task(self, user_input, agent_response):
        """
        Simplified method to quickly add a user query and agent response pair
        
        Args:
            user_input (str): The user's input query
            agent_response (str): The agent's response to the query
            
        Returns:
            str: Task ID of the created task
        """
        # Create a task with the user's input as the name
        task_name = user_input[:100] + "..." if len(user_input) > 100 else user_input
        task_id = self.create_task(
            name=task_name,
            description=user_input,
            task_type="conversation", 
            metadata={"source": "direct_conversation"}
        )
        
        # Add the agent's response
        self.add_agent_response(
            agent="general_pulse",
            response=agent_response,
            task_id=task_id,
            response_type="text"
        )
        
        logger.info(f"Added conversation task with ID: {task_id}")
        return task_id

# Example usage
if __name__ == "__main__":
    # Initialize the task memory manager
    task_manager = TaskMemoryManager()
    
    # Create a sample task
    task_id = task_manager.create_task(
        name="Build Portfolio Website",
        description="Create a modern portfolio website for Alex",
        task_type="code",
        priority=2,
        tags=["portfolio", "website", "frontend"]
    )
    
    # Create subtasks
    task_manager.create_subtask(
        task_id=task_id,
        name="Design mockup",
        description="Create initial design mockup and color scheme",
        priority=1
    )
    
    task_manager.create_subtask(
        task_id=task_id,
        name="Set up Next.js project",
        description="Initialize Next.js with Tailwind CSS and basic structure",
        priority=2
    )
    
    # Add agent responses
    task_manager.add_agent_response(
        agent="deepseek",
        response=json.dumps({
            "framework": "Next.js",
            "technologies": ["React", "Tailwind CSS", "Framer Motion", "Supabase"],
            "styling": "Tailwind CSS with custom theme",
            "animation": "Framer Motion for page transitions"
        }),
        task_id=task_id,
        response_type="json"
    )
    
    # Update vibe score
    task_manager.update_task_vibe_score(task_id, 8, "grok")
    
    # Get task summary
    summary = task_manager.get_task_summary(task_id)
    print(f"Task: {summary['task']['name']}")
    print(f"Description: {summary['task']['description']}")
    print(f"Vibe Score: {summary['stats']['vibe_score']}/10")
    print(f"Completion: {summary['stats']['completion_percentage']}%")
    print("Subtasks:")
    for subtask in summary['subtasks']:
        print(f"- {subtask['name']} ({subtask['status']})")
    
    # Get next actions
    next_actions = task_manager.predict_next_actions(task_id)
    print("\nSuggested Next Actions:")
    for action in next_actions:
        if action['type'] == 'complete_subtask':
            print(f"- Complete subtask: {action['name']}")
        elif action['type'] == 'get_agent_response':
            print(f"- Get input from {action['agent']}: {action['reason']}")
    
    # Close connection
    task_manager.close() 