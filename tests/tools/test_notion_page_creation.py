#!/usr/bin/env python3
"""
Test script for Notion page creation
"""

import sys
from tools.notion_integration import NotionIntegration

def create_document_example():
    """Create different types of Notion documents as examples"""
    
    notion = NotionIntegration()
    
    # Check if Notion integration is configured
    if not notion.is_configured():
        print("Notion integration is not configured.")
        print("Please set the NOTION_API_KEY environment variable.")
        sys.exit(1)
    
    print("Creating sample Notion pages...\n")
    
    # 1. Create a simple document with default template
    simple_content = (
        "This is a sample document created by General Pulse.\n\n"
        "It demonstrates the ability to programmatically create Notion pages.\n\n"
        "You can modify this content as needed."
    )
    
    simple_doc = notion.create_page(
        "Sample Document - Created by General Pulse",
        content=simple_content
    )
    
    if simple_doc.get("success"):
        print(f"✅ Simple document created!")
        print(f"   Title: {simple_doc.get('title')}")
        print(f"   URL: {simple_doc.get('url')}")
    else:
        print(f"❌ Failed to create simple document: {simple_doc.get('error')}")
    
    print("\n---\n")
    
    # 2. Create a to-do list
    todo_content = (
        "# Weekly Tasks\n\n"
        "- [ ] Review project roadmap\n"
        "- [ ] Update documentation\n"
        "- [x] Create Notion integration\n"
        "- [ ] Schedule team meeting\n"
        "- [ ] Research new APIs\n"
    )
    
    todo_doc = notion.create_page(
        "To-Do List - Created by General Pulse",
        content=todo_content,
        template="todo"
    )
    
    if todo_doc.get("success"):
        print(f"✅ To-do list created!")
        print(f"   Title: {todo_doc.get('title')}")
        print(f"   URL: {todo_doc.get('url')}")
    else:
        print(f"❌ Failed to create to-do list: {todo_doc.get('error')}")
    
    print("\n---\n")
    
    # 3. Create a journal entry
    journal_content = (
        "# Project Journal\n\n"
        "## Progress Update\n\n"
        "Today we implemented Notion integration in our project. This allows us to create and manage documents programmatically.\n\n"
        "## Next Steps\n\n"
        "- Enhance content formatting\n"
        "- Add support for databases\n"
        "- Implement better error handling\n\n"
        "## Challenges\n\n"
        "The main challenge was understanding the Notion API structure and how to properly format blocks."
    )
    
    journal_doc = notion.create_page(
        "Journal Entry - Created by General Pulse",
        content=journal_content,
        template="journal"
    )
    
    if journal_doc.get("success"):
        print(f"✅ Journal entry created!")
        print(f"   Title: {journal_doc.get('title')}")
        print(f"   URL: {journal_doc.get('url')}")
    else:
        print(f"❌ Failed to create journal: {journal_doc.get('error')}")
    
    print("\nCompleted testing Notion page creation.")

if __name__ == "__main__":
    create_document_example() 