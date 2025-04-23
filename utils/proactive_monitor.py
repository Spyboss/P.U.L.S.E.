"""
Proactive Monitor for General Pulse

This module provides proactive monitoring capabilities that allow the system
to anticipate user needs and provide alerts without being prompted.
"""

import os
import asyncio
import time
import psutil
import structlog
from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
import json

# Configure logger
logger = structlog.get_logger("proactive_monitor")

class ProactiveMonitor:
    """
    Monitors system status, calendar events, and project files to proactively
    alert the user about important events or issues.
    """
    
    def __init__(self, callback: Optional[Callable[[str, str, Dict[str, Any]], Awaitable[None]]] = None):
        """
        Initialize the proactive monitor
        
        Args:
            callback: Async callback function to call when an alert is triggered
                     Function signature: async def callback(alert_type, message, data)
        """
        self.callback = callback
        self.running = False
        self.task = None
        
        # Configure monitoring thresholds
        self.thresholds = {
            "cpu_percent": 85.0,  # CPU usage percentage
            "memory_percent": 80.0,  # Memory usage percentage
            "disk_percent": 90.0,  # Disk usage percentage
            "temperature": 80.0,  # CPU temperature (if available)
            "battery_percent": 15.0,  # Battery percentage (if available)
        }
        
        # Track alert states to avoid repeated alerts
        self.alert_states = {
            "cpu_high": False,
            "memory_high": False,
            "disk_high": False,
            "temperature_high": False,
            "battery_low": False,
            "calendar_alerted": set(),  # Set of event IDs that have been alerted
            "project_alerted": set(),  # Set of file paths that have been alerted
        }
        
        # Configure monitoring intervals (in seconds)
        self.intervals = {
            "system": 60,  # Check system status every 60 seconds
            "calendar": 300,  # Check calendar events every 5 minutes
            "projects": 600,  # Check project files every 10 minutes
        }
        
        # Track last check times
        self.last_checks = {
            "system": 0,
            "calendar": 0,
            "projects": 0,
        }
        
        logger.info("Proactive monitor initialized")
    
    async def start(self):
        """
        Start the proactive monitoring
        """
        if self.running:
            logger.warning("Proactive monitor already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitoring_loop())
        logger.info("Proactive monitoring started")
    
    async def stop(self):
        """
        Stop the proactive monitoring
        """
        if not self.running:
            logger.warning("Proactive monitor not running")
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        
        logger.info("Proactive monitoring stopped")
    
    async def _monitoring_loop(self):
        """
        Main monitoring loop
        """
        try:
            while self.running:
                current_time = time.time()
                
                # Check system status
                if current_time - self.last_checks["system"] >= self.intervals["system"]:
                    await self._check_system_status()
                    self.last_checks["system"] = current_time
                
                # Check calendar events
                if current_time - self.last_checks["calendar"] >= self.intervals["calendar"]:
                    await self._check_calendar_events()
                    self.last_checks["calendar"] = current_time
                
                # Check project files
                if current_time - self.last_checks["projects"] >= self.intervals["projects"]:
                    await self._check_project_files()
                    self.last_checks["projects"] = current_time
                
                # Sleep for a short time to avoid high CPU usage
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            if self.callback:
                await self.callback(
                    "error",
                    f"Proactive monitoring encountered an error: {str(e)}",
                    {"error": str(e)}
                )
    
    async def _check_system_status(self):
        """
        Check system status and trigger alerts if needed
        """
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Check for high CPU usage
            if cpu_percent >= self.thresholds["cpu_percent"] and not self.alert_states["cpu_high"]:
                self.alert_states["cpu_high"] = True
                if self.callback:
                    await self.callback(
                        "system",
                        f"High CPU usage detected: {cpu_percent:.1f}%",
                        {
                            "type": "cpu",
                            "value": cpu_percent,
                            "threshold": self.thresholds["cpu_percent"]
                        }
                    )
            elif cpu_percent < self.thresholds["cpu_percent"] - 10 and self.alert_states["cpu_high"]:
                # Reset alert state when CPU usage drops significantly
                self.alert_states["cpu_high"] = False
            
            # Check for high memory usage
            if memory_percent >= self.thresholds["memory_percent"] and not self.alert_states["memory_high"]:
                self.alert_states["memory_high"] = True
                if self.callback:
                    await self.callback(
                        "system",
                        f"High memory usage detected: {memory_percent:.1f}%",
                        {
                            "type": "memory",
                            "value": memory_percent,
                            "threshold": self.thresholds["memory_percent"],
                            "available_mb": memory.available / (1024 * 1024)
                        }
                    )
            elif memory_percent < self.thresholds["memory_percent"] - 10 and self.alert_states["memory_high"]:
                # Reset alert state when memory usage drops significantly
                self.alert_states["memory_high"] = False
            
            # Check for high disk usage
            if disk_percent >= self.thresholds["disk_percent"] and not self.alert_states["disk_high"]:
                self.alert_states["disk_high"] = True
                if self.callback:
                    await self.callback(
                        "system",
                        f"High disk usage detected: {disk_percent:.1f}%",
                        {
                            "type": "disk",
                            "value": disk_percent,
                            "threshold": self.thresholds["disk_percent"],
                            "free_gb": disk.free / (1024 * 1024 * 1024)
                        }
                    )
            elif disk_percent < self.thresholds["disk_percent"] - 5 and self.alert_states["disk_high"]:
                # Reset alert state when disk usage drops
                self.alert_states["disk_high"] = False
            
            # Try to get battery info if available
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_percent = battery.percent
                    battery_plugged = battery.power_plugged
                    
                    # Check for low battery
                    if (battery_percent <= self.thresholds["battery_percent"] and 
                        not battery_plugged and 
                        not self.alert_states["battery_low"]):
                        self.alert_states["battery_low"] = True
                        if self.callback:
                            await self.callback(
                                "system",
                                f"Low battery warning: {battery_percent:.1f}%",
                                {
                                    "type": "battery",
                                    "value": battery_percent,
                                    "threshold": self.thresholds["battery_percent"],
                                    "plugged": battery_plugged
                                }
                            )
                    elif (battery_percent > self.thresholds["battery_percent"] + 5 or battery_plugged) and self.alert_states["battery_low"]:
                        # Reset alert state when battery is charged or plugged in
                        self.alert_states["battery_low"] = False
            except Exception as e:
                # Battery info might not be available on all systems
                pass
            
            # Try to get temperature info if available
            try:
                temperatures = psutil.sensors_temperatures()
                if temperatures:
                    # Get the highest temperature from any sensor
                    max_temp = 0
                    for name, entries in temperatures.items():
                        for entry in entries:
                            if entry.current > max_temp:
                                max_temp = entry.current
                    
                    # Check for high temperature
                    if max_temp >= self.thresholds["temperature"] and not self.alert_states["temperature_high"]:
                        self.alert_states["temperature_high"] = True
                        if self.callback:
                            await self.callback(
                                "system",
                                f"High CPU temperature detected: {max_temp:.1f}°C",
                                {
                                    "type": "temperature",
                                    "value": max_temp,
                                    "threshold": self.thresholds["temperature"]
                                }
                            )
                    elif max_temp < self.thresholds["temperature"] - 5 and self.alert_states["temperature_high"]:
                        # Reset alert state when temperature drops
                        self.alert_states["temperature_high"] = False
            except Exception as e:
                # Temperature info might not be available on all systems
                pass
            
        except Exception as e:
            logger.error(f"Error checking system status: {str(e)}")
    
    async def _check_calendar_events(self):
        """
        Check for upcoming calendar events
        """
        try:
            # This is a placeholder for calendar integration
            # In a real implementation, this would connect to the user's calendar
            # For now, we'll check a local calendar file if it exists
            
            calendar_file = "data/calendar.json"
            if not os.path.exists(calendar_file):
                return
            
            try:
                with open(calendar_file, "r") as f:
                    events = json.load(f)
            except Exception as e:
                logger.error(f"Error loading calendar file: {str(e)}")
                return
            
            # Get current time
            now = datetime.now()
            
            # Check for events in the next hour
            for event in events:
                try:
                    event_id = event.get("id", "")
                    event_title = event.get("title", "Untitled Event")
                    event_time_str = event.get("time", "")
                    
                    if not event_id or not event_time_str:
                        continue
                    
                    # Parse event time
                    event_time = datetime.fromisoformat(event_time_str)
                    
                    # Calculate time until event
                    time_until = event_time - now
                    
                    # Alert for events starting in the next 15 minutes
                    if (0 < time_until.total_seconds() <= 900 and  # 15 minutes in seconds
                        event_id not in self.alert_states["calendar_alerted"]):
                        
                        # Add to alerted events
                        self.alert_states["calendar_alerted"].add(event_id)
                        
                        # Calculate minutes until event
                        minutes_until = int(time_until.total_seconds() / 60)
                        
                        if self.callback:
                            await self.callback(
                                "calendar",
                                f"Upcoming event in {minutes_until} minutes: {event_title}",
                                {
                                    "type": "event",
                                    "id": event_id,
                                    "title": event_title,
                                    "time": event_time_str,
                                    "minutes_until": minutes_until
                                }
                            )
                except Exception as e:
                    logger.error(f"Error processing calendar event: {str(e)}")
            
            # Clean up old events from the alerted set
            for event_id in list(self.alert_states["calendar_alerted"]):
                try:
                    # Find the event
                    event = next((e for e in events if e.get("id") == event_id), None)
                    
                    if not event:
                        # Event no longer exists, remove from alerted set
                        self.alert_states["calendar_alerted"].remove(event_id)
                        continue
                    
                    event_time_str = event.get("time", "")
                    if not event_time_str:
                        continue
                    
                    # Parse event time
                    event_time = datetime.fromisoformat(event_time_str)
                    
                    # If event is in the past, remove from alerted set
                    if event_time < now:
                        self.alert_states["calendar_alerted"].remove(event_id)
                except Exception as e:
                    logger.error(f"Error cleaning up calendar event: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error checking calendar events: {str(e)}")
    
    async def _check_project_files(self):
        """
        Check for changes in project files
        """
        try:
            # This is a placeholder for project file monitoring
            # In a real implementation, this would monitor the user's project directories
            # For now, we'll check a projects directory if it exists
            
            projects_dir = "projects"
            if not os.path.exists(projects_dir):
                return
            
            # Get list of project directories
            project_dirs = [d for d in os.listdir(projects_dir) 
                           if os.path.isdir(os.path.join(projects_dir, d))]
            
            for project_dir in project_dirs:
                project_path = os.path.join(projects_dir, project_dir)
                
                # Check for git repository
                git_dir = os.path.join(project_path, ".git")
                if os.path.exists(git_dir):
                    # Check for uncommitted changes
                    try:
                        import subprocess
                        
                        # Run git status
                        result = subprocess.run(
                            ["git", "status", "--porcelain"],
                            cwd=project_path,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            # Uncommitted changes detected
                            changes = result.stdout.strip().split("\n")
                            
                            # Create a unique identifier for this set of changes
                            changes_hash = hash(result.stdout.strip())
                            change_id = f"{project_dir}:{changes_hash}"
                            
                            if change_id not in self.alert_states["project_alerted"]:
                                # Add to alerted projects
                                self.alert_states["project_alerted"].add(change_id)
                                
                                if self.callback:
                                    await self.callback(
                                        "project",
                                        f"Uncommitted changes detected in project: {project_dir}",
                                        {
                                            "type": "git",
                                            "project": project_dir,
                                            "changes": changes,
                                            "change_count": len(changes)
                                        }
                                    )
                    except Exception as e:
                        logger.error(f"Error checking git status for project {project_dir}: {str(e)}")
                
                # Check for TODO comments in code files
                try:
                    todo_files = []
                    
                    # Extensions to check
                    code_extensions = [".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".cs", ".go"]
                    
                    # Walk through project directory
                    for root, dirs, files in os.walk(project_path):
                        # Skip .git directory
                        if ".git" in dirs:
                            dirs.remove(".git")
                        
                        # Skip node_modules directory
                        if "node_modules" in dirs:
                            dirs.remove("node_modules")
                        
                        # Check code files
                        for file in files:
                            if any(file.endswith(ext) for ext in code_extensions):
                                file_path = os.path.join(root, file)
                                
                                # Check if file was modified in the last 24 hours
                                file_mtime = os.path.getmtime(file_path)
                                if time.time() - file_mtime <= 86400:  # 24 hours in seconds
                                    # Check for TODO comments
                                    try:
                                        with open(file_path, "r", encoding="utf-8") as f:
                                            content = f.read()
                                            
                                            if "TODO" in content or "FIXME" in content:
                                                rel_path = os.path.relpath(file_path, project_path)
                                                todo_files.append(rel_path)
                                    except Exception as e:
                                        # Skip files that can't be read
                                        pass
                    
                    if todo_files:
                        # Create a unique identifier for this set of TODO files
                        todo_hash = hash(":".join(sorted(todo_files)))
                        todo_id = f"{project_dir}:todo:{todo_hash}"
                        
                        if todo_id not in self.alert_states["project_alerted"]:
                            # Add to alerted projects
                            self.alert_states["project_alerted"].add(todo_id)
                            
                            if self.callback:
                                await self.callback(
                                    "project",
                                    f"TODO comments found in recently modified files in project: {project_dir}",
                                    {
                                        "type": "todo",
                                        "project": project_dir,
                                        "files": todo_files,
                                        "file_count": len(todo_files)
                                    }
                                )
                except Exception as e:
                    logger.error(f"Error checking TODO comments for project {project_dir}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error checking project files: {str(e)}")
    
    def set_threshold(self, name: str, value: float):
        """
        Set a monitoring threshold
        
        Args:
            name: Threshold name
            value: Threshold value
        """
        if name in self.thresholds:
            self.thresholds[name] = value
            logger.info(f"Set {name} threshold to {value}")
        else:
            logger.warning(f"Unknown threshold: {name}")
    
    def set_interval(self, name: str, seconds: int):
        """
        Set a monitoring interval
        
        Args:
            name: Interval name
            seconds: Interval in seconds
        """
        if name in self.intervals:
            self.intervals[name] = seconds
            logger.info(f"Set {name} interval to {seconds} seconds")
        else:
            logger.warning(f"Unknown interval: {name}")
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the proactive monitor
        
        Returns:
            Dictionary with status information
        """
        status = {
            "running": self.running,
            "thresholds": self.thresholds.copy(),
            "intervals": self.intervals.copy(),
            "last_checks": {k: datetime.fromtimestamp(v).isoformat() if v > 0 else None 
                           for k, v in self.last_checks.items()},
            "current_system": await self._get_current_system_status()
        }
        
        return status
    
    async def _get_current_system_status(self) -> Dict[str, Any]:
        """
        Get the current system status
        
        Returns:
            Dictionary with system status information
        """
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            # Get network info
            net_io = psutil.net_io_counters()
            
            # Get battery info if available
            battery_info = None
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = {
                        "percent": battery.percent,
                        "plugged": battery.power_plugged,
                        "time_left": str(timedelta(seconds=battery.secsleft)) if battery.secsleft > 0 else "unknown"
                    }
            except:
                pass
            
            # Get temperature info if available
            temp_info = None
            try:
                temperatures = psutil.sensors_temperatures()
                if temperatures:
                    temp_info = {}
                    for name, entries in temperatures.items():
                        temp_info[name] = [{"label": entry.label, "current": entry.current, 
                                          "high": entry.high, "critical": entry.critical} 
                                         for entry in entries]
            except:
                pass
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count(logical=True),
                    "physical_cores": psutil.cpu_count(logical=False)
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "battery": battery_info,
                "temperature": temp_info,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {"error": str(e)}
