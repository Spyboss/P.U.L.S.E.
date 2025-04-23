"""
Test script for the Notion integration
"""

import os
import sys
import json
import traceback
from dotenv import load_dotenv

from tools.notion_integration import NotionIntegration

def main():
    try:
        # Load environment variables
        load_dotenv()
        
        # Print environment variables (sanitized)
        print("Environment variables:")
        notion_key = os.environ.get("NOTION_API_KEY", "")
        print(f"NOTION_API_KEY: {'***' + notion_key[-4:] if notion_key else 'Not set'}")
        print(f"NOTION_VERSION: {os.environ.get('NOTION_VERSION', 'Not set')}")
        
        # Initialize the Notion integration
        notion = NotionIntegration()
        
        # Check if configured
        if not notion.is_configured():
            print("Notion integration is not configured properly.")
            print("Make sure the .env file contains NOTION_API_KEY and NOTION_VERSION.")
            sys.exit(1)
        
        print("Notion integration configured successfully!")
        
        # Test getting current user info
        print("\nGetting current user information...")
        user_data = notion.get_user()
        if "error" in user_data:
            print(f"Error: {user_data['error']}")
            if "message" in user_data:
                print(f"Message: {user_data['message']}")
        else:
            print(f"Connected as: {user_data.get('name', 'Unknown')} ({user_data.get('type', 'Unknown')})")
            print(f"Bot: {user_data.get('bot', False)}")
            print(f"User object: {json.dumps(user_data, indent=2)}")
        
        # Test listing databases
        print("\nListing available databases...")
        databases = notion.list_databases()
        if "error" in databases:
            print(f"Error: {databases['error']}")
            if "message" in databases:
                print(f"Message: {databases['message']}")
        else:
            results = databases.get("results", [])
            print(f"Found {len(results)} databases:")
            
            if not results:
                print("No databases found. This could be because:")
                print("1. Your integration doesn't have access to any databases")
                print("2. You need to share databases with your integration")
                print("3. The API key doesn't have the correct permissions")
            
            for db in results:
                db_id = db.get("id", "Unknown ID")
                title = "Untitled Database"
                
                # Handle different title structures
                if "title" in db:
                    title_data = db.get("title", [])
                    if isinstance(title_data, list) and title_data:
                        title_obj = title_data[0]
                        if "text" in title_obj and "content" in title_obj["text"]:
                            title = title_obj["text"]["content"]
                    elif isinstance(title_data, dict):
                        # Try to extract title from properties
                        properties = db.get("properties", {})
                        if "title" in properties:
                            title = properties["title"].get("title", "Untitled Database")
                
                print(f"- {title} (ID: {db_id})")
                
                # If a database was found, try querying it
                if db_id != "Unknown ID":
                    print(f"\nGetting details for database: {title}")
                    db_details = notion.get_database(db_id)
                    if "error" in db_details:
                        print(f"Error: {db_details['error']}")
                        if "message" in db_details:
                            print(f"Message: {db_details['message']}")
                    else:
                        print(f"Database {title} has the following properties:")
                        properties = db_details.get("properties", {})
                        for prop_name, prop_details in properties.items():
                            print(f"  - {prop_name} ({prop_details.get('type', 'Unknown type')})")
                    
                    # Try querying the database
                    print(f"\nQuerying database: {title}")
                    query_results = notion.query_database(db_id)
                    if "error" in query_results:
                        print(f"Error: {query_results['error']}")
                        if "message" in query_results:
                            print(f"Message: {query_results['message']}")
                    else:
                        pages = query_results.get("results", [])
                        print(f"Found {len(pages)} pages in the database")
                        for i, page in enumerate(pages[:3], 1):  # Show first 3 pages
                            page_id = page.get("id", "Unknown")
                            print(f"  {i}. Page ID: {page_id}")
                    
                    # Only process one database as an example
                    break
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 