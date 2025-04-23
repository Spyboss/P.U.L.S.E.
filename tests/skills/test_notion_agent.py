"""
Test script for interacting with the Notion integration through the agent
"""

import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools.notion_integration import NotionIntegration
from utils import logger

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the Notion integration directly
    notion = NotionIntegration()
    
    if not notion.is_configured():
        print("Notion integration is not properly configured.")
        sys.exit(1)
    
    print("Notion Integration Test")
    print("======================")
    print("1. Get current user information")
    print("2. List accessible databases")
    print("3. Create a test database (if none exists)")
    print("4. Exit")
    
    choice = input("\nSelect an option (1-4): ")
    
    if choice == "1":
        print("\nGetting user information...")
        user_info = notion.get_user()
        print(json.dumps(user_info, indent=2))
    
    elif choice == "2":
        print("\nListing databases...")
        databases = notion.list_databases()
        
        if "error" in databases:
            print(f"Error: {databases.get('error')}")
            print(f"Message: {databases.get('message', 'No message')}")
            return
        
        results = databases.get("results", [])
        print(f"Found {len(results)} databases:")
        
        for i, db in enumerate(results, 1):
            db_id = db.get("id", "Unknown")
            
            # Try different ways to get the title
            title = "Untitled"
            if "title" in db:
                title_data = db.get("title", [])
                if isinstance(title_data, list) and title_data:
                    if "text" in title_data[0] and "content" in title_data[0]["text"]:
                        title = title_data[0]["text"]["content"]
            
            print(f"{i}. {title} (ID: {db_id})")
            
            # If there are databases, offer to view the first one
            if i == 1:
                view_details = input("\nView details of this database? (y/n): ")
                if view_details.lower() == "y":
                    print(f"\nGetting details for database {db_id}...")
                    db_details = notion.get_database(db_id)
                    print(json.dumps(db_details, indent=2))
                    
                    query_pages = input("\nQuery pages in this database? (y/n): ")
                    if query_pages.lower() == "y":
                        print(f"\nQuerying database {db_id}...")
                        pages = notion.query_database(db_id)
                        print(json.dumps(pages, indent=2))
    
    elif choice == "3":
        print("\nCreating a test database...")
        print("NOTE: This feature requires the user to create a database manually in Notion")
        print("and share it with the integration.")
        print("\nInstructions:")
        print("1. Go to Notion and create a new page")
        print("2. Type /database and select 'Table - Full page'")
        print("3. Add columns like 'Name', 'Status', 'Priority'")
        print("4. Title your database (e.g., 'General Pulse Tasks')")
        print("5. Click 'Share' in the top right")
        print("6. Search for and add your integration ('General Pulse')")
        print("7. Run option 2 in this script to check if the database is accessible")
    
    elif choice == "4":
        print("\nExiting...")
        return
    
    else:
        print("\nInvalid option. Please try again.")

if __name__ == "__main__":
    main() 