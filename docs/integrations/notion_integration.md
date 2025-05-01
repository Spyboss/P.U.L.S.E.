# Notion Integration

P.U.L.S.E. (Prime Uminda's Learning System Engine) offers powerful integration with Notion, allowing you to programmatically create and analyze documents. This document outlines the available features and how to use them.

## Features

1. **Document Creation**

   - Create standard documents
   - Create to-do lists
   - Create journal entries
   - AI-powered content generation

2. **Page Analysis**

   - Extract page content and metadata
   - Analyze sentiment of journal entries
   - Identify topics and themes
   - Count words and characters

3. **Journal Management**
   - Add daily journal entries to existing pages
   - Use templated or AI-generated content
   - Daily reflection templates
   - Automatic date and formatting

## Setup

To use the Notion integration, you need to:

1. Create a Notion integration in your [Notion workspace settings](https://www.notion.so/my-integrations)
2. Set the `NOTION_API_KEY` environment variable with your integration token
3. Share specific pages with your integration

## Usage

### Command Line Interface

Use the `notion_document_creator.py` script to create documents:

```bash
# Create a simple document
python notion_document_creator.py --title "Meeting Notes" --type "default"

# Create a to-do list
python notion_document_creator.py --title "Weekly Tasks" --type "todo"

# Create a journal entry
python notion_document_creator.py --title "Daily Reflection" --type "journal"

# Generate content using AI
python notion_document_creator.py --title "Project Ideas" --generate
```

For daily journal entries, use the `daily_journal.py` script:

```bash
# Add entry with default template
python daily_journal.py

# Add reflection-style entry
python daily_journal.py --reflection

# Add AI-generated journal entry
python daily_journal.py --ai

# Add custom content
python daily_journal.py --content "Today I learned about Notion API integration"

# Specify a different journal page
python daily_journal.py --url "https://www.notion.so/Your-Journal-ID"
```

### Agent Integration

When using the P.U.L.S.E. agent, you can create documents with natural language:

```
create a to-do list called "Project Milestones"
```

```
create a journal entry about today's achievements
```

```
add a daily journal entry to my journal page
```

### Page Analysis

Analyze existing Notion pages:

```python
from tools.notion_integration import NotionIntegration

notion = NotionIntegration()
analysis = notion.analyze_journal_page("https://www.notion.so/Your-Page-1d334ba186ed8034bdabd5d163b1caa0")

print(f"Title: {analysis.get('title')}")
print(f"Sentiment: {analysis.get('sentiment')}")
print(f"Topics: {', '.join(analysis.get('topics', []))}")
print(f"Word count: {analysis.get('word_count')}")
```

## API Reference

### NotionIntegration Class

- `extract_id_from_url(url)`: Extract a Notion page ID from a URL
- `create_page(title, content, parent_id, template)`: Create a new Notion page
- `append_journal_entry(page_id_or_url, entry_content, date)`: Append entry to an existing page
- `create_daily_journal_entry(journal_page_url, content)`: Add daily journal entry
- `analyze_journal_page(url_or_id)`: Analyze a Notion page for content and insights
- `get_page(page_id)`: Get information about a specific page
- `get_block_children(block_id)`: Get the content blocks of a page

### Agent Methods

- `create_notion_document(title, content, document_type)`: Create a document through the agent
- `create_daily_journal_entry(journal_page_url, content, generate_content)`: Add journal entry

## Examples

### Creating a To-Do List

```python
from tools.notion_integration import NotionIntegration

notion = NotionIntegration()
todo_content = """
# Weekly Tasks

- [ ] Complete project proposal
- [ ] Schedule team meeting
- [x] Research competitors
- [ ] Create wireframes
"""

result = notion.create_page(
    "Weekly Planning",
    todo_content,
    template="todo"
)

print(f"To-do list created: {result.get('url')}")
```

### Adding a Daily Journal Entry

```python
from tools.notion_integration import NotionIntegration
from datetime import datetime

notion = NotionIntegration()
today = datetime.now().strftime("%Y-%m-%d")
weekday = datetime.now().strftime("%A")

content = f"""
### {weekday} Reflection

#### Accomplishments
- Implemented Notion API integration
- Fixed bugs in the journal system
- Added documentation

#### Challenges
- API rate limiting
- Understanding Notion block structure

#### Tomorrow's Focus
- Implement recurring journal reminders
- Add sentiment tracking over time
"""

result = notion.create_daily_journal_entry(
    "https://www.notion.so/Journal-1d334ba186ed80b9800fc1dc708cdad4",
    content
)

print(f"Journal entry added: {result.get('url')}")
```

### Analyzing a Journal Page

```python
from tools.notion_integration import NotionIntegration

notion = NotionIntegration()
analysis = notion.analyze_journal_page("https://www.notion.so/Your-Journal-1d334ba186ed8034bdabd5d163b1caa0")

if "error" not in analysis:
    print(f"Sentiment: {analysis.get('sentiment')}")
    print(f"Topics: {', '.join(analysis.get('topics', []))}")
    print(f"Word count: {analysis.get('word_count')}")
else:
    print(f"Error: {analysis.get('error')}")
```
