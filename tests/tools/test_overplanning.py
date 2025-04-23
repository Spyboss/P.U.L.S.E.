"""
Test script for the Notion Overplanning Detector
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

from tools.notion_integration import NotionIntegration
from tools.notion_overplanning_detector import NotionOverplanningDetector

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the Notion Overplanning Detector')
    parser.add_argument('--database_id', help='ID of the Notion database to analyze')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the Notion integration
    notion = NotionIntegration()
    
    if not notion.is_configured():
        print("Notion integration is not properly configured.")
        print("Make sure the .env file contains NOTION_API_KEY and NOTION_VERSION.")
        sys.exit(1)
    
    # Initialize the Overplanning Detector
    detector = NotionOverplanningDetector()
    
    if not detector.is_configured():
        print("Notion Overplanning Detector is not properly configured.")
        print("Make sure the Notion integration and AI models are properly configured.")
        sys.exit(1)
    
    print("Notion Overplanning Detector Test")
    print("================================")
    
    # If no database ID is provided, list databases and let user select one
    database_id = args.database_id
    if not database_id:
        print("\nListing available Notion databases...")
        databases = notion.list_databases()
        
        if "error" in databases:
            print(f"Error: {databases.get('error')}")
            if "message" in databases:
                print(f"Message: {databases.get('message', 'No message')}")
            sys.exit(1)
        
        results = databases.get("results", [])
        print(f"Found {len(results)} databases:")
        
        if not results:
            print("No databases found. Make sure you've shared databases with your integration.")
            print("See test_notion.py for instructions on how to create and share a database.")
            sys.exit(1)
        
        # Display databases for selection
        for i, db in enumerate(results, 1):
            db_id = db.get("id", "Unknown ID")
            
            # Extract title
            title = "Untitled Database"
            if "title" in db:
                title_data = db.get("title", [])
                if isinstance(title_data, list) and title_data:
                    if "text" in title_data[0] and "content" in title_data[0]["text"]:
                        title = title_data[0]["text"]["content"]
            
            print(f"{i}. {title} (ID: {db_id})")
        
        # Let user select a database
        try:
            selection = int(input("\nSelect a database to analyze (enter number): "))
            if selection < 1 or selection > len(results):
                print("Invalid selection.")
                sys.exit(1)
            
            database_id = results[selection-1].get("id")
            print(f"Selected database ID: {database_id}")
        except ValueError:
            print("Please enter a valid number.")
            sys.exit(1)
    
    # Analyze the selected database
    print(f"\nAnalyzing database for overplanning: {database_id}")
    analysis = detector.analyze_task_board(database_id)
    
    if "error" in analysis:
        print(f"Error: {analysis.get('error')}")
        sys.exit(1)
    
    # Display results
    print("\nAnalysis Results:")
    print(f"Total Tasks: {analysis.get('total_tasks', 0)}")
    print(f"Tasks with Due Dates: {analysis.get('tasks_with_dates', 0)}")
    
    if analysis.get("overplanning_detected", False):
        print("\n⚠️ OVERPLANNING DETECTED! ⚠️")
        
        # Display insights
        print("\nInsights:")
        for i, insight in enumerate(analysis.get("insights", []), 1):
            insight_type = insight.get("type", "unknown")
            severity = insight.get("severity", "medium").upper()
            
            if insight_type == "daily_overload":
                print(f"{i}. [DAILY OVERLOAD - {severity}] {insight.get('task_count')} tasks due on {insight.get('date_formatted')}")
                print(f"   (Threshold: {insight.get('threshold')} tasks per day)")
            elif insight_type == "weekly_overload":
                print(f"{i}. [WEEKLY OVERLOAD - {severity}] {insight.get('task_count')} tasks due during {insight.get('week_formatted')}")
                print(f"   (Threshold: {insight.get('threshold')} tasks per week)")
            elif insight_type == "priority_conflict":
                print(f"{i}. [PRIORITY CONFLICT - {severity}] {insight.get('high_priority_count')} high-priority tasks due on {insight.get('date_formatted')}")
                print(f"   (Threshold: {insight.get('threshold')} high-priority tasks per day)")
            elif insight_type == "undated_tasks":
                print(f"{i}. [UNDATED TASKS - {severity}] {insight.get('count')} tasks have no due date")
        
        # Display the roast
        if "roast" in analysis and analysis["roast"]:
            print("\n🔥 Humorous Roast:")
            print(f"\"{analysis['roast']}\"")
        
        # Display task recommendations
        if "task_recommendations" in analysis and analysis["task_recommendations"]:
            print("\n💡 Task Recommendations:")
            for i, rec in enumerate(analysis["task_recommendations"], 1):
                print(f"\n{i}. Task: {rec.get('title', 'Unknown')}")
                if rec.get("rationale"):
                    print(f"   Rationale: {rec.get('rationale')}")
                if rec.get("recommendation"):
                    print(f"   Recommendation: {rec.get('recommendation')}")
    else:
        print("\n✅ Your planning looks good! No signs of overplanning detected.")
    
    # Option to save results to a file
    save_option = input("\nSave analysis results to file? (y/n): ")
    if save_option.lower() == 'y':
        filename = f"overplanning_analysis_{database_id[-6:]}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    main() 