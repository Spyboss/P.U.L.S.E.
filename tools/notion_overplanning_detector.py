"""
Notion Overplanning Detector for General Pulse
Analyzes Notion task boards for signs of unrealistic planning and overcommitment
"""

import os
import sys
import json
import datetime
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import logger, load_yaml_config, save_json_data, ensure_directory_exists
from tools.notion_integration import NotionIntegration
from skills.optimized_model_interface import OptimizedModelInterface

class NotionOverplanningDetector:
    """Tool for detecting overplanning in Notion task boards and providing humorous feedback."""

    def __init__(self, config_path="configs/agent_config.yaml"):
        """Initialize the Overplanning Detector with configuration."""
        self.config_path = config_path
        self.logger = logger
        self.logger.debug(f"NotionOverplanningDetector initializing with config path: {config_path}")

        try:
            self.config = load_yaml_config(config_path)
            self.overplanning_config = self.config.get('tools', {}).get('overplanning_detector', {})
            self.enabled = self.overplanning_config.get('enabled', True)

            # Initialize Notion integration
            self.notion_integration = NotionIntegration(config_path)

            # Initialize model interface for AI analysis
            self.model_interface = OptimizedModelInterface()

            # Load configuration
            self.roast_model = self.overplanning_config.get('roast_model', 'claude')
            self.reasoning_model = self.overplanning_config.get('reasoning_model', 'deepseek')

            # Overplanning thresholds
            self.daily_task_threshold = self.overplanning_config.get('daily_task_threshold', 5)
            self.weekly_task_threshold = self.overplanning_config.get('weekly_task_threshold', 15)
            self.priority_conflict_threshold = self.overplanning_config.get('priority_conflict_threshold', 3)

            if self.enabled:
                self.logger.info("Notion Overplanning Detector enabled")
            else:
                self.logger.info("Notion Overplanning Detector disabled")
        except Exception as e:
            self.logger.error(f"Error initializing Notion Overplanning Detector: {str(e)}", exc_info=True)
            self.config = {}
            self.overplanning_config = {}
            self.enabled = False
            self.notion_integration = None
            self.model_interface = None
            self.roast_model = 'claude'
            self.reasoning_model = 'deepseek'
            self.daily_task_threshold = 5
            self.weekly_task_threshold = 15
            self.priority_conflict_threshold = 3

    def is_configured(self):
        """Check if Overplanning Detector is properly configured."""
        configured = (self.enabled and
                     self.notion_integration and
                     self.notion_integration.is_configured() and
                     self.model_interface and
                     self.model_interface.get_available_models())
        self.logger.debug(f"Overplanning Detector configured: {configured}")
        return configured

    def analyze_task_board(self, database_id):
        """Analyze a Notion database for signs of overplanning."""
        try:
            if not self.is_configured():
                self.logger.warning("Overplanning Detector not configured")
                return {"error": "Overplanning Detector not configured"}

            self.logger.info(f"Analyzing Notion database for overplanning: {database_id}")

            # Query the database
            database_query = self.notion_integration.query_database(database_id)

            if "error" in database_query:
                self.logger.error(f"Error querying database: {database_query['error']}")
                return database_query

            # Get database structure to understand the properties
            database_info = self.notion_integration.get_database(database_id)
            if "error" in database_info:
                self.logger.error(f"Error getting database info: {database_info['error']}")
                return database_info

            # Find relevant properties (date, status, priority)
            properties = database_info.get("properties", {})
            date_property = None
            status_property = None
            priority_property = None

            for prop_name, prop_details in properties.items():
                prop_type = prop_details.get("type", "")
                if prop_type == "date":
                    date_property = prop_name
                elif prop_type == "select" or prop_type == "status":
                    # Look for status-like properties
                    if "status" in prop_name.lower() or prop_details.get("name", "").lower() == "status":
                        status_property = prop_name
                elif prop_type == "select":
                    # Look for priority-like properties
                    if "priority" in prop_name.lower() or prop_details.get("name", "").lower() == "priority":
                        priority_property = prop_name

            self.logger.debug(f"Identified properties: Date={date_property}, Status={status_property}, Priority={priority_property}")

            # Extract tasks and analyze
            results = self._extract_and_analyze_tasks(database_query.get("results", []),
                                                     date_property,
                                                     status_property,
                                                     priority_property)

            # Generate insights and recommendations
            insights = self._generate_insights(results)

            # If overplanning detected, generate roasts and recommendations
            if insights.get("overplanning_detected", False):
                self.logger.info("Overplanning detected, generating roast and recommendations")
                insights["roast"] = self._generate_roast(insights)
                insights["task_recommendations"] = self._generate_task_recommendations(
                    insights,
                    results.get("upcoming_tasks", [])
                )

            # Cache the results
            self._cache_analysis_results(database_id, insights)

            return insights

        except Exception as e:
            self.logger.error(f"Error analyzing task board: {str(e)}", exc_info=True)
            return {"error": f"Error: {str(e)}"}

    def _extract_and_analyze_tasks(self, pages, date_property, status_property, priority_property):
        """Extract task information from pages and analyze for overplanning."""
        results = {
            "total_tasks": len(pages),
            "tasks_with_dates": 0,
            "upcoming_tasks": [],
            "tasks_by_date": defaultdict(list),
            "tasks_by_week": defaultdict(list),
            "high_priority_tasks": [],
            "tasks_without_dates": [],
            "potential_conflicts": []
        }

        today = datetime.datetime.now().date()

        for page in pages:
            # Extract basic task info
            task = {
                "id": page.get("id", ""),
                "title": self._extract_title(page),
                "url": page.get("url", ""),
                "properties": page.get("properties", {})
            }

            # Extract date information if available
            task_date = None
            if date_property and date_property in task["properties"]:
                date_value = task["properties"][date_property].get("date", {})
                if date_value:
                    task_date_str = date_value.get("start")
                    if task_date_str:
                        task_date = datetime.datetime.fromisoformat(task_date_str.replace('Z', '+00:00')).date()
                        task["due_date"] = task_date_str
                        task["due_date_obj"] = task_date
                        results["tasks_with_dates"] += 1

                        # Only add to upcoming tasks if due date is today or in the future
                        if task_date >= today:
                            results["upcoming_tasks"].append(task)

                            # Add task to daily count
                            date_key = task_date.isoformat()
                            results["tasks_by_date"][date_key].append(task)

                            # Add task to weekly count
                            week_start = task_date - datetime.timedelta(days=task_date.weekday())
                            week_key = week_start.isoformat()
                            results["tasks_by_week"][week_key].append(task)

            # If no date, add to tasks without dates
            if "due_date" not in task:
                results["tasks_without_dates"].append(task)

            # Extract status information if available
            if status_property and status_property in task["properties"]:
                status_value = task["properties"][status_property].get("select", {})
                if status_value:
                    task["status"] = status_value.get("name", "Unknown")

            # Extract priority information if available
            if priority_property and priority_property in task["properties"]:
                priority_value = task["properties"][priority_property].get("select", {})
                if priority_value:
                    task["priority"] = priority_value.get("name", "Unknown")

                    # Add high priority tasks to list
                    priority_name = task.get("priority", "").lower()
                    if "high" in priority_name or "urgent" in priority_name or "p1" in priority_name or "p0" in priority_name:
                        task["is_high_priority"] = True
                        results["high_priority_tasks"].append(task)

        # Analyze for overplanning
        results["daily_overplanning"] = []
        results["weekly_overplanning"] = []

        # Check for daily overplanning
        for date_key, tasks in results["tasks_by_date"].items():
            if len(tasks) > self.daily_task_threshold:
                results["daily_overplanning"].append({
                    "date": date_key,
                    "task_count": len(tasks),
                    "tasks": tasks
                })

        # Check for weekly overplanning
        for week_key, tasks in results["tasks_by_week"].items():
            if len(tasks) > self.weekly_task_threshold:
                results["weekly_overplanning"].append({
                    "week_start": week_key,
                    "task_count": len(tasks),
                    "tasks": tasks
                })

        # Check for priority conflicts
        date_high_priority = defaultdict(list)
        for task in results["high_priority_tasks"]:
            if "due_date_obj" in task:
                date_key = task["due_date_obj"].isoformat()
                date_high_priority[date_key].append(task)

        for date_key, tasks in date_high_priority.items():
            if len(tasks) > self.priority_conflict_threshold:
                results["potential_conflicts"].append({
                    "date": date_key,
                    "high_priority_count": len(tasks),
                    "tasks": tasks
                })

        return results

    def _generate_insights(self, analysis_results):
        """Generate insights from the task analysis."""
        insights = {
            "total_tasks": analysis_results.get("total_tasks", 0),
            "tasks_with_dates": analysis_results.get("tasks_with_dates", 0),
            "overplanning_detected": False,
            "insights": []
        }

        # Check for overplanning flags
        daily_overplanning = analysis_results.get("daily_overplanning", [])
        weekly_overplanning = analysis_results.get("weekly_overplanning", [])
        priority_conflicts = analysis_results.get("potential_conflicts", [])

        # Add insights based on what we found
        if daily_overplanning:
            insights["overplanning_detected"] = True

            for overload in daily_overplanning:
                date = datetime.date.fromisoformat(overload.get("date"))
                insights["insights"].append({
                    "type": "daily_overload",
                    "date": overload.get("date"),
                    "date_formatted": date.strftime("%A, %B %d, %Y"),
                    "task_count": overload.get("task_count"),
                    "threshold": self.daily_task_threshold,
                    "severity": self._calculate_severity(overload.get("task_count"), self.daily_task_threshold)
                })

        if weekly_overplanning:
            insights["overplanning_detected"] = True

            for overload in weekly_overplanning:
                week_start = datetime.date.fromisoformat(overload.get("week_start"))
                week_end = week_start + datetime.timedelta(days=6)
                insights["insights"].append({
                    "type": "weekly_overload",
                    "week_start": overload.get("week_start"),
                    "week_formatted": f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}",
                    "task_count": overload.get("task_count"),
                    "threshold": self.weekly_task_threshold,
                    "severity": self._calculate_severity(overload.get("task_count"), self.weekly_task_threshold)
                })

        if priority_conflicts:
            insights["overplanning_detected"] = True

            for conflict in priority_conflicts:
                date = datetime.date.fromisoformat(conflict.get("date"))
                insights["insights"].append({
                    "type": "priority_conflict",
                    "date": conflict.get("date"),
                    "date_formatted": date.strftime("%A, %B %d, %Y"),
                    "high_priority_count": conflict.get("high_priority_count"),
                    "threshold": self.priority_conflict_threshold,
                    "severity": self._calculate_severity(conflict.get("high_priority_count"), self.priority_conflict_threshold)
                })

        if len(analysis_results.get("tasks_without_dates", [])) > 0:
            insights["insights"].append({
                "type": "undated_tasks",
                "count": len(analysis_results.get("tasks_without_dates", [])),
                "severity": "low"
            })

        return insights

    def _generate_roast(self, insights):
        """Generate a humorous roast based on the insights found."""
        try:
            if not insights or not insights.get("overplanning_detected", False):
                return None

            self.logger.info(f"Generating humorous roast based on {len(insights.get('insights', []))} insights")

            # Format the insights for the prompt
            insight_text = ""
            for i, insight in enumerate(insights.get("insights", []), 1):
                insight_type = insight.get("type", "unknown")

                if insight_type == "daily_overload":
                    insight_text += f"{i}. Daily Overload: {insight.get('task_count')} tasks due on {insight.get('date_formatted')} " \
                                   f"(threshold: {insight.get('threshold')}). Severity: {insight.get('severity', 'medium')}.\n"
                elif insight_type == "weekly_overload":
                    insight_text += f"{i}. Weekly Overload: {insight.get('task_count')} tasks due during the week of " \
                                   f"{insight.get('week_formatted')} (threshold: {insight.get('threshold')}). " \
                                   f"Severity: {insight.get('severity', 'medium')}.\n"
                elif insight_type == "priority_conflict":
                    insight_text += f"{i}. Priority Conflict: {insight.get('high_priority_count')} high-priority tasks due on " \
                                   f"{insight.get('date_formatted')} (threshold: {insight.get('threshold')}). " \
                                   f"Severity: {insight.get('severity', 'medium')}.\n"
                elif insight_type == "undated_tasks":
                    insight_text += f"{i}. Undated Tasks: {insight.get('count')} tasks have no due date. " \
                                   f"Severity: {insight.get('severity', 'low')}.\n"

            # Create the prompt
            prompt = f"""You are a hilarious but helpful personal productivity coach. You've analyzed a user's Notion
task board and found the following signs of overplanning and task overload:

{insight_text}

Write a short, snarky, and entertaining roast (1-2 paragraphs) about their unrealistic planning.
Be blunt but still constructive - like a friend who's not afraid to call them out.
Use humor, pop culture references, and a dash of tough love.

Some example tones:
- "Bro, you're not Superman, delete three of these tasks or I'm locking you out."
- "Scheduling 10 high-priority tasks on Tuesday? What are you, a productivity AI with no concept of human limitations?"
- "I see you've planned your week as if you've discovered the mythical 48-hour day. Spoiler alert: it doesn't exist."

Keep it under 150 words and make it memorable.
"""

            # Call the model to generate the roast
            roast_response = self.model_interface.call_model_api(
                self.roast_model,
                prompt
            )

            if "error" in roast_response:
                self.logger.error(f"Error generating roast: {roast_response['error']}")
                return "I'd roast your planning skills, but your schedule is already on fire. Try removing a few tasks before you burn out completely!"

            return roast_response.get("response", "").strip()

        except Exception as e:
            self.logger.error(f"Error generating roast: {str(e)}", exc_info=True)
            return "Your schedule looks more overloaded than a clown car at a circus convention. Maybe scale back a bit?"

    def _generate_task_recommendations(self, insights, upcoming_tasks):
        """Generate AI-powered recommendations for which tasks to deprioritize."""
        try:
            if not insights or not insights.get("overplanning_detected", False) or not upcoming_tasks:
                return []

            self.logger.info(f"Generating task recommendations based on {len(upcoming_tasks)} upcoming tasks")

            # Format the insights for the prompt
            insight_text = ""
            for i, insight in enumerate(insights.get("insights", []), 1):
                insight_type = insight.get("type", "unknown")

                if insight_type == "daily_overload":
                    insight_text += f"{i}. Daily Overload: {insight.get('task_count')} tasks due on {insight.get('date_formatted')} " \
                                   f"(threshold: {insight.get('threshold')}). Severity: {insight.get('severity', 'medium')}.\n"
                elif insight_type == "weekly_overload":
                    insight_text += f"{i}. Weekly Overload: {insight.get('task_count')} tasks due during the week of " \
                                   f"{insight.get('week_formatted')} (threshold: {insight.get('threshold')}). " \
                                   f"Severity: {insight.get('severity', 'medium')}.\n"
                elif insight_type == "priority_conflict":
                    insight_text += f"{i}. Priority Conflict: {insight.get('high_priority_count')} high-priority tasks due on " \
                                   f"{insight.get('date_formatted')} (threshold: {insight.get('threshold')}). " \
                                   f"Severity: {insight.get('severity', 'medium')}.\n"

            # Format task list
            tasks_text = ""
            for i, task in enumerate(upcoming_tasks, 1):
                title = task.get("title", "Untitled Task")
                due_date = task.get("due_date", "No date")
                priority = task.get("priority", "No priority")
                status = task.get("status", "No status")

                tasks_text += f"{i}. Title: {title}\n"
                tasks_text += f"   Due Date: {due_date}\n"
                if priority != "No priority":
                    tasks_text += f"   Priority: {priority}\n"
                if status != "No status":
                    tasks_text += f"   Status: {status}\n"
                tasks_text += "\n"

            # Create the prompt
            prompt = f"""You are an expert productivity advisor. Your job is to analyze a user's task list and
recommend which tasks to deprioritize or reschedule based on signs of overplanning.

Here are the signs of overplanning that have been detected:
{insight_text}

Here are the upcoming tasks:
{tasks_text}

Based on this information, select up to 5 tasks that should be deprioritized, rescheduled, or delegated to make the
user's schedule more realistic. For each task, provide:
1. The task number and title
2. Your rationale for why this task could be delayed or deprioritized
3. A specific recommendation (reschedule to when, delegate to whom, or delete)

Format your response for each task as:
TASK X: [Task Title]
RATIONALE: [Your reasoning for why this task can wait]
RECOMMENDATION: [Specific action to take]

Focus on non-urgent tasks, tasks that can be delegated, or tasks that don't align with important goals.
"""

            # Call the model to generate the recommendations
            recommendation_response = self.model_interface.call_model_api(
                self.reasoning_model,
                prompt
            )

            if "error" in recommendation_response:
                self.logger.error(f"Error generating recommendations: {recommendation_response['error']}")
                return []

            # Parse the recommendations into structured format
            response_text = recommendation_response.get("response", "").strip()
            task_sections = response_text.split("TASK")

            recommendations = []
            for section in task_sections:
                if not section.strip():
                    continue

                # Extract task number and details
                lines = section.split("\n")
                task_header = lines[0].strip()

                task_num = None
                task_title = ""

                # Parse task header (e.g., "1: Task Title" or "Task Title")
                if ":" in task_header:
                    parts = task_header.split(":", 1)
                    try:
                        task_num = int(parts[0].strip())
                        task_title = parts[1].strip()
                    except ValueError:
                        task_title = task_header
                else:
                    task_title = task_header

                # Find rationale and recommendation
                rationale = ""
                recommendation = ""

                for line in lines[1:]:
                    if line.startswith("RATIONALE:"):
                        rationale = line.replace("RATIONALE:", "").strip()
                    elif line.startswith("RECOMMENDATION:"):
                        recommendation = line.replace("RECOMMENDATION:", "").strip()

                if task_title and (rationale or recommendation):
                    recommendations.append({
                        "task_num": task_num,
                        "title": task_title,
                        "rationale": rationale,
                        "recommendation": recommendation
                    })

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating task recommendations: {str(e)}", exc_info=True)
            return []

    def _extract_title(self, page):
        """Extract the title from a Notion page."""
        # Try to get title from properties
        properties = page.get("properties", {})
        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "title":
                title_items = prop_value.get("title", [])
                if title_items:
                    title_parts = []
                    for item in title_items:
                        if item.get("type") == "text":
                            title_parts.append(item.get("text", {}).get("content", ""))
                    return "".join(title_parts)

        # Fallback to page title if available
        if "title" in page:
            title_items = page.get("title", [])
            if isinstance(title_items, list) and title_items:
                title_parts = []
                for item in title_items:
                    if item.get("type") == "text":
                        title_parts.append(item.get("text", {}).get("content", ""))
                return "".join(title_parts)

        return "Untitled"

    def _calculate_severity(self, value, threshold):
        """Calculate severity based on how far value exceeds threshold."""
        ratio = value / threshold

        if ratio >= 3:
            return "critical"
        elif ratio >= 2:
            return "high"
        elif ratio >= 1.5:
            return "medium"
        else:
            return "low"

    def _cache_analysis_results(self, database_id, results):
        """Cache analysis results for a database."""
        try:
            storage_dir = "memory/notion/overplanning"
            ensure_directory_exists(storage_dir)

            # Use timestamp for the cache file
            import time
            timestamp = int(time.time())
            cache_file = os.path.join(storage_dir, f"{database_id}_analysis_{timestamp}.json")

            with open(cache_file, 'w', encoding='utf-8') as f:
                # Add timestamp to results
                results_with_time = results.copy()
                results_with_time["timestamp"] = timestamp
                results_with_time["analysis_time"] = datetime.datetime.now().isoformat()

                json.dump(results_with_time, f, indent=2)

            self.logger.debug(f"Cached overplanning analysis results for database {database_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error caching analysis results: {str(e)}", exc_info=True)
            return False