#!/usr/bin/env python3
"""
Daily Journal Entry Script

This script adds a daily journal entry to a specified Notion journal page.
It can either use a template, custom content, or AI-generated content.
"""

import os
import sys
import argparse
from datetime import datetime
from skills.agent import Agent
from utils.logger import default_logger

JOURNAL_URL = "https://www.notion.so/Journal-1d334ba186ed80b9800fc1dc708cdad4"

def main():
    """Add a daily journal entry to Notion."""
    parser = argparse.ArgumentParser(description="Create a daily journal entry in Notion")
    parser.add_argument('--url', type=str, default=JOURNAL_URL,
                       help='Notion journal page URL (default: personal journal page)')
    parser.add_argument('--content', type=str, help='Journal entry content')
    parser.add_argument('--template', action='store_true', 
                       help='Use default template instead of AI-generated content')
    parser.add_argument('--ai', action='store_true',
                       help='Force AI-generated content even if content is provided')
    parser.add_argument('--reflection', action='store_true',
                       help='Add a specific reflection-based journal template')
    
    args = parser.parse_args()
    
    # Initialize logger
    log = default_logger
    
    # Check for Notion API key
    if 'NOTION_API_KEY' not in os.environ:
        print("Error: NOTION_API_KEY environment variable is not set.")
        print("Please set it with: $env:NOTION_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Initialize agent
    agent = Agent()
    log.info("Agent initialized for journal entry creation")
    
    # Determine what content to use
    content = args.content
    
    # If reflection template requested
    if args.reflection:
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        weekday = today.strftime("%A")
        
        content = (
            f"### {weekday} Reflection\n\n"
            "#### What went well today?\n\n"
            "- \n\n"
            "#### What could have gone better?\n\n"
            "- \n\n"
            "#### What did I learn?\n\n"
            "- \n\n"
            "#### What am I grateful for?\n\n"
            "- \n\n"
            "#### What will I focus on tomorrow?\n\n"
            "- "
        )
        
    # Determine if we should use AI generation
    generate_with_ai = (content is None and not args.template) or args.ai
    
    # Get journal URL
    journal_url = args.url
    
    print(f"\nCreating daily journal entry for {datetime.now().strftime('%Y-%m-%d')}...")
    
    if generate_with_ai:
        print("Using AI to generate journal content...")
    elif content:
        print("Using provided custom content...")
    else:
        print("Using default journal template...")
    
    # Create the journal entry
    result = agent.create_daily_journal_entry(journal_url, content, generate_with_ai)
    
    # Display result
    print(f"\n{result}")

if __name__ == "__main__":
    main() 