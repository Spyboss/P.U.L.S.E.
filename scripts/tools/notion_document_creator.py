#!/usr/bin/env python3
"""
Notion Document Creator Demo

This script demonstrates creating different types of Notion documents
using the agent's capabilities.
"""

import os
import sys
import argparse
from skills.agent import Agent
from skills.optimized_model_interface import OptimizedModelInterface
from utils.logger import default_logger

def main():
    """Run the Notion document creator demo."""
    parser = argparse.ArgumentParser(description="Create documents in Notion")
    parser.add_argument('--title', type=str, help='Document title')
    parser.add_argument('--type', type=str, default='default',
                        choices=['default', 'todo', 'journal'],
                        help='Document type (default, todo, journal)')
    parser.add_argument('--content', type=str, help='Document content (optional)')
    parser.add_argument('--generate', action='store_true',
                        help='Generate content using AI')
    parser.add_argument('--prompt', type=str,
                        help='Prompt for AI content generation')

    args = parser.parse_args()

    # Initialize the logger
    log = default_logger

    # Check for Notion API key
    if 'NOTION_API_KEY' not in os.environ:
        print("Error: NOTION_API_KEY environment variable is not set.")
        print("Please set it with: $env:NOTION_API_KEY='your-api-key'")
        sys.exit(1)

    # Initialize the agent
    agent = Agent()
    log.info("Agent initialized for Notion document creation")

    # Get document title
    title = args.title
    if not title:
        title = input("Enter document title: ")

    # Get document type
    doc_type = args.type

    # Get or generate content
    content = args.content

    if not content and args.generate:
        # Use AI to generate content
        log.info("Generating content with AI...")
        model = OptimizedModelInterface()

        prompt = args.prompt
        if not prompt:
            default_prompts = {
                'default': f"Create a document titled '{title}'. Make it informative and well-structured.",
                'todo': f"Create a to-do list for '{title}'. Include 5-7 tasks with varying priorities.",
                'journal': f"Create a journal entry titled '{title}'. Include sections for goals, reflections, and next steps."
            }
            prompt = default_prompts.get(doc_type, default_prompts['default'])

        # Call the model
        response = model.call_model_api(prompt)
        if response and "content" in response:
            content = response["content"]
            log.info("Content generated successfully")
        else:
            log.warning("Failed to generate content with AI")
            content = f"# {title}\n\nThis is a placeholder document. Please add your content here."

    elif not content:
        # Use a template based on document type
        templates = {
            'default': f"# {title}\n\nThis is a new document created by General Pulse.\n\n## Overview\n\nAdd your content here.\n\n## Details\n\nMore information can be added in this section.",

            'todo': f"# {title}\n\n## Tasks\n\n- [ ] First task\n- [ ] Second task\n- [ ] Third task\n\n## Notes\n\nAdd any notes about these tasks here.",

            'journal': f"# {title}\n\n## Today's Goals\n\nWhat do you want to accomplish today?\n\n## Reflections\n\nThoughts and observations\n\n## Next Steps\n\nWhat's coming up next?"
        }
        content = templates.get(doc_type, templates['default'])

    # Create the document
    print(f"\nCreating {doc_type} document '{title}' in Notion...\n")
    result = agent.create_notion_document(title, content, doc_type)

    # Display result
    print(result)

    # If successful, suggest a follow-up action
    if "successfully" in result:
        print("\nWhat would you like to do next?")
        print("1. Create another document")
        print("2. Analyze a Notion page")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ")

        if choice == "1":
            # Could add recursive call or restart logic here
            print("To create another document, run this script again with different parameters.")
        elif choice == "2":
            url = input("Enter the URL of the Notion page to analyze: ")
            if url:
                from tools.notion_integration import NotionIntegration
                notion = NotionIntegration()
                analysis = notion.analyze_journal_page(url)

                if "error" not in analysis:
                    print("\n=== Page Analysis ===")
                    print(f"Title: {analysis.get('title', 'Unknown')}")
                    print(f"Sentiment: {analysis.get('sentiment', 'Unknown')}")
                    print(f"Topics: {', '.join(analysis.get('topics', ['None']))}")
                    print(f"Word count: {analysis.get('word_count', 0)}")
                else:
                    print(f"Error analyzing page: {analysis.get('error')}")

if __name__ == "__main__":
    main()