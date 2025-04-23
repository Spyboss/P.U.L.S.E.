"""
Task Manager Skill for General Pulse
Handles reading and updating tasks in the tasks.md file
"""

import os
import re
from datetime import datetime
from utils import logger

class TaskManager:
    """Skill for managing tasks in the tasks.md file."""
    
    def __init__(self, tasks_file_path="tasks.md"):
        """Initialize the task manager with the path to the tasks file."""
        self.tasks_file_path = tasks_file_path
        self.logger = logger
        self.logger.debug(f"TaskManager initialized with file: {tasks_file_path}")
        
    def read_tasks(self):
        """Read all tasks from the tasks file."""
        try:
            if not os.path.exists(self.tasks_file_path):
                self.logger.warning(f"Tasks file not found: {self.tasks_file_path}")
                return {
                    "completed": [],
                    "in_progress": [],
                    "pending": []
                }
                
            self.logger.debug(f"Reading tasks from {self.tasks_file_path}")
            with open(self.tasks_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Parse the tasks using regex
            completed = re.findall(r'## ✅ Completed\n\n((?:- .*\n)*)', content)
            in_progress = re.findall(r'## 🛠️ In Progress\n\n((?:- .*\n)*)', content)
            pending = re.findall(r'## ⏳ Pending\n\n((?:- .*\n)*)', content)
            
            # Process the matches
            tasks = {
                "completed": self._parse_task_items(completed[0] if completed else ""),
                "in_progress": self._parse_task_items(in_progress[0] if in_progress else ""),
                "pending": self._parse_task_items(pending[0] if pending else "")
            }
            
            self.logger.debug(f"Found {len(tasks['completed'])} completed, {len(tasks['in_progress'])} in progress, {len(tasks['pending'])} pending tasks")
            return tasks
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error when reading tasks file: {str(e)}", exc_info=True)
            self.logger.info("Attempting to read file with different encoding...")
            try:
                with open(self.tasks_file_path, "r", encoding="latin-1") as f:
                    content = f.read()
                # Continue processing with the content...
                self.logger.info("Successfully read file with alternative encoding")
                # Re-implement parsing logic here
                return self._parse_with_content(content)
            except Exception as inner_e:
                self.logger.error(f"Failed to read tasks with alternative encoding: {str(inner_e)}", exc_info=True)
                return {"completed": [], "in_progress": [], "pending": []}
        except Exception as e:
            self.logger.error(f"Error reading tasks: {str(e)}", exc_info=True)
            return {"completed": [], "in_progress": [], "pending": []}
    
    def _parse_with_content(self, content):
        """Parse tasks from content string with error handling."""
        try:
            # Parse the tasks using regex
            completed = re.findall(r'## ✅ Completed\n\n((?:- .*\n)*)', content)
            in_progress = re.findall(r'## 🛠️ In Progress\n\n((?:- .*\n)*)', content)
            pending = re.findall(r'## ⏳ Pending\n\n((?:- .*\n)*)', content)
            
            # Process the matches
            return {
                "completed": self._parse_task_items(completed[0] if completed else ""),
                "in_progress": self._parse_task_items(in_progress[0] if in_progress else ""),
                "pending": self._parse_task_items(pending[0] if pending else "")
            }
        except Exception as e:
            self.logger.error(f"Error parsing task content: {str(e)}", exc_info=True)
            return {"completed": [], "in_progress": [], "pending": []}
    
    def _parse_task_items(self, text):
        """Parse task items from text."""
        try:
            if not text:
                return []
            return [line[2:].strip() for line in text.split('\n') if line.strip().startswith('- ')]
        except Exception as e:
            self.logger.error(f"Error parsing task items: {str(e)}", exc_info=True)
            return []
    
    def add_task(self, task, status="pending"):
        """Add a new task with the specified status."""
        try:
            if not task or not task.strip():
                self.logger.warning("Attempted to add empty task")
                return False
                
            self.logger.info(f"Adding task to '{status}': {task}")
            tasks = self.read_tasks()
            
            # Validate status
            if status not in tasks:
                self.logger.error(f"Invalid task status: {status}")
                return False
                
            # Add the task if it doesn't exist
            if task not in tasks[status]:
                tasks[status].append(task)
                success = self._write_tasks(tasks)
                if success:
                    self.logger.info(f"Task added successfully: {task}")
                return success
            else:
                self.logger.info(f"Task already exists in '{status}': {task}")
                return False
        except Exception as e:
            self.logger.error(f"Error adding task: {str(e)}", exc_info=True)
            return False
    
    def update_task_status(self, task, new_status):
        """Update the status of a task."""
        try:
            if not task or not task.strip():
                self.logger.warning("Attempted to update empty task")
                return False
                
            self.logger.info(f"Updating task to '{new_status}': {task}")
            tasks = self.read_tasks()
            
            # Validate status
            if new_status not in tasks:
                self.logger.error(f"Invalid task status: {new_status}")
                return False
            
            # Find the task in any status list and move it
            found = False
            for status in tasks:
                if task in tasks[status]:
                    self.logger.debug(f"Found task in '{status}', moving to '{new_status}'")
                    tasks[status].remove(task)
                    tasks[new_status].append(task)
                    found = True
                    break
                    
            if not found:
                self.logger.warning(f"Task not found for status update: {task}")
                return False
                
            success = self._write_tasks(tasks)
            if success:
                self.logger.info(f"Task updated successfully from '{status}' to '{new_status}': {task}")
            return success
        except Exception as e:
            self.logger.error(f"Error updating task status: {str(e)}", exc_info=True)
            return False
    
    def _write_tasks(self, tasks):
        """Write tasks back to the tasks file."""
        try:
            # Read the existing file to preserve sections that aren't tasks
            with open(self.tasks_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Update the last updated timestamp
            now = datetime.now().strftime("%B %d, %Y")
            content = re.sub(r'Last updated: .*', f'Last updated: {now}', content)
            
            # Update the task sections
            try:
                content = re.sub(
                    r'## ✅ Completed\n\n(?:- .*\n)*',
                    f'## ✅ Completed\n\n' + '\n'.join([f'- {task}' for task in tasks['completed']]) + '\n\n',
                    content
                )
                content = re.sub(
                    r'## 🛠️ In Progress\n\n(?:- .*\n)*',
                    f'## 🛠️ In Progress\n\n' + '\n'.join([f'- {task}' for task in tasks['in_progress']]) + '\n\n',
                    content
                )
                content = re.sub(
                    r'## ⏳ Pending\n\n(?:- .*\n)*',
                    f'## ⏳ Pending\n\n' + '\n'.join([f'- {task}' for task in tasks['pending']]) + '\n\n',
                    content
                )
            except Exception as e:
                self.logger.error(f"Error updating task sections: {str(e)}", exc_info=True)
                return False
            
            # Create a backup before writing
            backup_path = f"{self.tasks_file_path}.bak"
            try:
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.debug(f"Created backup at {backup_path}")
            except Exception as e:
                self.logger.warning(f"Could not create backup file: {str(e)}")
            
            # Write the updated content back to the file
            with open(self.tasks_file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            self.logger.debug("Tasks file updated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error writing tasks: {str(e)}", exc_info=True)
            return False 