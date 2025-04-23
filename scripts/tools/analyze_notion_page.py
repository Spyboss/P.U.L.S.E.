#!/usr/bin/env python3
"""
Notion Page Analyzer
Script to analyze a Notion page and display its content and analytics
"""

import os
import sys
from tools.notion_integration import NotionIntegration

def main():
    # Notion URL to analyze
    notion_url = "https://www.notion.so/Weekly-To-do-List-1d334ba186ed8034bdabd5d163b1caa0?pvs=4"
    
    # Initialize the Notion integration
    notion = NotionIntegration()
    
    # Check if Notion integration is configured
    if not notion.is_configured():
        print("Notion integration is not configured.")
        print("Please set the NOTION_API_KEY environment variable.")
        sys.exit(1)
    
    # Extract page ID from the URL
    page_id = notion.extract_id_from_url(notion_url)
    if not page_id:
        print(f"Could not extract page ID from URL: {notion_url}")
        sys.exit(1)
    
    print(f"Extracted page ID: {page_id}")
    
    # First, try to get basic page info
    page_info = notion.get_page(page_id)
    if "error" in page_info:
        print(f"Error retrieving page: {page_info.get('error')}")
        sys.exit(1)
        
    print("\n=== Page Information ===")
    print(f"Page exists: {'Yes' if page_info else 'No'}")
    
    # Get page blocks/content
    blocks = notion.get_block_children(page_id)
    if "error" in blocks:
        print(f"Error retrieving page content: {blocks.get('error')}")
    else:
        print(f"Number of blocks: {len(blocks.get('results', []))}")
    
    # Now analyze the page
    print("\n=== Analyzing Page ===")
    analysis = notion.analyze_journal_page(notion_url)
    
    if "error" in analysis:
        print(f"Analysis error: {analysis.get('error')}")
        sys.exit(1)
    
    # Print analysis results
    print("\n=== Analysis Results ===")
    print(f"Title: {analysis.get('title', 'No title')}")
    print(f"Word count: {analysis.get('word_count', 0)}")
    print(f"Character count: {analysis.get('character_count', 0)}")
    print(f"Sentiment: {analysis.get('sentiment', 'Unknown')}")
    print(f"Topics: {', '.join(analysis.get('topics', ['None found']))}")
    
    # Print content summary
    print("\n=== Content Preview ===")
    content = analysis.get('content', 'No content available')
    print(content[:1000] + ("..." if len(content) > 1000 else ""))

if __name__ == "__main__":
    main() 