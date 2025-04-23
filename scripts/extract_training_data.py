"""
Extract training data from tasks.db and generate new simulated interactions
"""

import os
import sqlite3
import csv
import re
import random
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('data_extraction')

# Ensure directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Define regex patterns for intent classification
INTENT_PATTERNS = {
    "task": [
        r'task',
        r'todo',
        r'to-do',
        r'to do',
        r'list',
        r'add',
        r'create',
        r'show',
        r'display',
        r'update',
        r'edit',
        r'complete',
        r'finish',
        r'prioritize'
    ],
    "time": [
        r'time',
        r'date',
        r'day',
        r'hour',
        r'minute',
        r'today',
        r'tomorrow',
        r'yesterday',
        r'timezone',
        r'clock'
    ],
    "github": [
        r'github',
        r'repo',
        r'repository',
        r'commit',
        r'issue',
        r'pull request',
        r'pr',
        r'branch',
        r'merge',
        r'code'
    ],
    "notion": [
        r'notion',
        r'document',
        r'page',
        r'journal',
        r'entry',
        r'note',
        r'notes'
    ],
    "ai_query": [
        r'ask',
        r'query',
        r'claude',
        r'grok',
        r'deepseek',
        r'gemini',
        r'ai',
        r'model',
        r'question'
    ],
    "system": [
        r'help',
        r'exit',
        r'quit',
        r'stop',
        r'restart',
        r'system'
    ]
}

def classify_intent(text):
    """
    Classify text into an intent using regex patterns
    
    Args:
        text: The text to classify
        
    Returns:
        The classified intent
    """
    text = text.lower()
    
    # Count matches for each intent
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(r'\b' + pattern + r'\b', text):
                score += 1
        scores[intent] = score
    
    # Get the intent with the highest score
    if any(scores.values()):
        max_intent = max(scores.items(), key=lambda x: x[1])[0]
        return max_intent
    else:
        return "other"

def extract_from_db():
    """
    Extract interactions from tasks.db
    
    Returns:
        List of interactions
    """
    interactions = []
    
    try:
        # Connect to the database
        conn = sqlite3.connect('memory/tasks.db')
        cursor = conn.cursor()
        
        # Get tasks
        cursor.execute("SELECT name, description FROM tasks WHERE task_type='conversation'")
        tasks = cursor.fetchall()
        
        for name, description in tasks:
            if name and len(name) > 3:
                interactions.append(name)
            if description and len(description) > 3 and description != name:
                interactions.append(description)
        
        # Get agent responses
        cursor.execute("SELECT response FROM agent_responses")
        responses = cursor.fetchall()
        
        # Extract user queries from responses where possible
        for response, in responses:
            if response and isinstance(response, str) and len(response) > 10:
                # Try to extract user queries from the response
                query_match = re.search(r'query: "(.*?)"', response)
                if query_match:
                    interactions.append(query_match.group(1))
        
        conn.close()
        
        logger.info(f"Extracted {len(interactions)} interactions from database")
        return interactions
        
    except Exception as e:
        logger.error(f"Error extracting from database: {e}")
        return []

def generate_simulated_queries(base_queries, count=100):
    """
    Generate simulated queries based on existing patterns
    
    Args:
        base_queries: List of base queries to use as templates
        count: Number of queries to generate
        
    Returns:
        List of simulated queries
    """
    simulated = []
    
    # Templates for different intent types
    templates = {
        "task": [
            "show my tasks",
            "list all tasks",
            "add task '{}'",
            "create task '{}'",
            "update task '{}'",
            "complete task '{}'",
            "mark task '{}' as done",
            "prioritize task '{}'",
            "what tasks do I have",
            "show pending tasks"
        ],
        "time": [
            "what time is it",
            "what time is it in {}",
            "current time in {}",
            "time in {}",
            "what's the date today",
            "what day is it",
            "what's the time",
            "current date",
            "time difference between {} and {}"
        ],
        "github": [
            "github {}/{} info",
            "show github {}/{} issues",
            "list issues for {}/{}",
            "github {}/{} commit {}",
            "generate commit message for {} in {}/{}",
            "create github repo {}",
            "check github status for {}/{}"
        ],
        "notion": [
            "create notion document called '{}'",
            "add journal entry to notion",
            "create a notion page titled '{}'",
            "make a journal entry",
            "add note to notion about '{}'",
            "create new document in notion"
        ],
        "ai_query": [
            "ask claude {}",
            "ask grok {}",
            "ask deepseek {}",
            "query claude about {}",
            "ask ai about {}",
            "what does claude think about {}"
        ],
        "system": [
            "help",
            "exit",
            "quit",
            "system status",
            "restart",
            "what can you do",
            "show commands"
        ]
    }
    
    # Sample content for placeholders
    task_names = [
        "Fix bug in login page",
        "Call client about project",
        "Review pull request",
        "Prepare presentation",
        "Update documentation",
        "Research new framework",
        "Setup development environment",
        "Deploy to production",
        "Backup database",
        "Create user guide"
    ]
    
    locations = [
        "New York",
        "London",
        "Tokyo",
        "Paris",
        "Sydney",
        "Berlin",
        "Singapore",
        "Moscow",
        "Dubai",
        "Los Angeles"
    ]
    
    github_users = ["Spyboss", "microsoft", "google", "facebook", "apple", "netflix", "amazon", "twitter", "uber", "airbnb"]
    github_repos = ["repo", "project", "app", "framework", "library", "tool", "sdk", "api", "cli", "ui"]
    github_files = ["main.py", "utils.py", "app.js", "index.html", "styles.css", "README.md", "config.json", "Dockerfile", "requirements.txt", "setup.py"]
    
    notion_titles = [
        "Meeting Notes",
        "Project Ideas",
        "Research Findings",
        "Weekly Plan",
        "Book Summary",
        "Learning Resources",
        "Client Feedback",
        "Product Roadmap",
        "Team Goals",
        "Personal Reflections"
    ]
    
    ai_topics = [
        "machine learning",
        "artificial intelligence",
        "neural networks",
        "deep learning",
        "natural language processing",
        "computer vision",
        "reinforcement learning",
        "data science",
        "robotics",
        "ethics in AI"
    ]
    
    # Generate simulated queries
    for _ in range(count):
        # Choose a random intent
        intent = random.choice(list(templates.keys()))
        
        # Choose a random template for that intent
        template = random.choice(templates[intent])
        
        # Fill in the template based on intent type
        if intent == "task":
            task_name = random.choice(task_names)
            query = template.format(task_name)
        elif intent == "time":
            if "{}" in template:
                if template.count("{}") == 2:
                    loc1, loc2 = random.sample(locations, 2)
                    query = template.format(loc1, loc2)
                else:
                    query = template.format(random.choice(locations))
            else:
                query = template
        elif intent == "github":
            user = random.choice(github_users)
            repo = random.choice(github_repos)
            file = random.choice(github_files)
            if template.count("{}") == 3:
                query = template.format(user, repo, file)
            elif template.count("{}") == 2:
                query = template.format(user, repo)
            elif "commit" in template:
                query = template.format(file, user, repo)
            else:
                query = template.format(user)
        elif intent == "notion":
            if "{}" in template:
                query = template.format(random.choice(notion_titles))
            else:
                query = template
        elif intent == "ai_query":
            query = template.format(random.choice(ai_topics))
        else:  # system
            query = template
        
        simulated.append(query)
    
    logger.info(f"Generated {len(simulated)} simulated queries")
    return simulated

def save_to_file(interactions, filename):
    """
    Save interactions to a file
    
    Args:
        interactions: List of interactions
        filename: File to save to
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            f.write('\n'.join(interactions))
        
        logger.info(f"Saved {len(interactions)} interactions to {filename}")
    except Exception as e:
        logger.error(f"Error saving to file: {e}")

def save_labeled_data(interactions, filename):
    """
    Save labeled interactions to a CSV file
    
    Args:
        interactions: List of interactions
        filename: File to save to
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['text', 'label'])
            
            for text in interactions:
                label = classify_intent(text)
                writer.writerow([text, label])
        
        logger.info(f"Saved {len(interactions)} labeled interactions to {filename}")
    except Exception as e:
        logger.error(f"Error saving labeled data: {e}")

def main():
    """Main function"""
    logger.info("Starting data extraction")
    
    # Extract interactions from database
    db_interactions = extract_from_db()
    
    # Generate simulated queries
    simulated_queries = generate_simulated_queries(db_interactions)
    
    # Combine real and simulated interactions
    all_interactions = db_interactions + simulated_queries
    
    # Save to files
    save_to_file(simulated_queries, 'data/new_interactions.txt')
    save_labeled_data(all_interactions, 'data/labeled_data.csv')
    
    logger.info("Data extraction complete")

if __name__ == "__main__":
    main()
