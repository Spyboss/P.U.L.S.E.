"""
Analyze labeled data to extract top keywords for each intent
"""

import os
import csv
import re
import json
import logging
from collections import Counter, defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/keyword_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('keyword_analysis')

# Ensure directories exist
os.makedirs('models/keyword_classifier', exist_ok=True)
os.makedirs('logs', exist_ok=True)

def load_labeled_data(filename):
    """
    Load labeled data from CSV file
    
    Args:
        filename: CSV file to load
        
    Returns:
        Dictionary mapping intents to lists of texts
    """
    intent_texts = defaultdict(list)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row in reader:
                if len(row) >= 2:
                    text, intent = row
                    intent_texts[intent].append(text.lower())
        
        logger.info(f"Loaded {sum(len(texts) for texts in intent_texts.values())} labeled examples for {len(intent_texts)} intents")
        return intent_texts
    except Exception as e:
        logger.error(f"Error loading labeled data: {e}")
        return {}

def extract_keywords(texts, stopwords):
    """
    Extract keywords from a list of texts
    
    Args:
        texts: List of texts
        stopwords: Set of stopwords to ignore
        
    Returns:
        Counter of keywords and their frequencies
    """
    word_counts = Counter()
    
    for text in texts:
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stopwords
        words = [word for word in words if word not in stopwords]
        
        # Update counts
        word_counts.update(words)
    
    return word_counts

def get_top_keywords(intent_texts, top_n=10):
    """
    Get top keywords for each intent
    
    Args:
        intent_texts: Dictionary mapping intents to lists of texts
        top_n: Number of top keywords to extract
        
    Returns:
        Dictionary mapping intents to lists of top keywords
    """
    # Common stopwords
    stopwords = set([
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with",
        "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "i", "you", "he", "she", "it", "we", "they", "my", "your",
        "his", "her", "its", "our", "their", "me", "him", "us", "them", "what", "which",
        "who", "whom", "this", "that", "these", "those", "of", "from", "about", "as"
    ])
    
    intent_keywords = {}
    
    for intent, texts in intent_texts.items():
        # Extract keywords
        word_counts = extract_keywords(texts, stopwords)
        
        # Get top keywords
        top_keywords = [word for word, _ in word_counts.most_common(top_n)]
        
        intent_keywords[intent] = top_keywords
    
    return intent_keywords

def merge_with_existing_keywords(new_keywords, existing_keywords_path):
    """
    Merge new keywords with existing ones
    
    Args:
        new_keywords: Dictionary of new keywords
        existing_keywords_path: Path to existing keywords file
        
    Returns:
        Merged keywords dictionary
    """
    # Default keywords if file doesn't exist
    default_keywords = {
        "task": ["task", "todo", "to-do", "to do", "list", "add", "create", "show", "display", "update", "edit", "complete", "finish"],
        "time": ["time", "date", "day", "hour", "minute", "today", "tomorrow", "yesterday", "timezone", "clock"],
        "github": ["github", "repo", "repository", "commit", "issue", "pull request", "pr", "branch", "merge", "code"],
        "notion": ["notion", "document", "page", "journal", "entry", "note", "notes"],
        "ai_query": ["ask", "query", "claude", "grok", "deepseek", "gemini", "ai", "model", "question"],
        "system": ["help", "exit", "quit", "stop", "restart", "system"]
    }
    
    try:
        # Try to load existing keywords
        if os.path.exists(existing_keywords_path):
            with open(existing_keywords_path, 'r', encoding='utf-8') as f:
                existing_keywords = json.load(f)
        else:
            existing_keywords = default_keywords
        
        # Merge keywords
        merged_keywords = existing_keywords.copy()
        
        for intent, keywords in new_keywords.items():
            if intent in merged_keywords:
                # Add new keywords that don't already exist
                merged_keywords[intent] = list(set(merged_keywords[intent] + keywords))
            else:
                merged_keywords[intent] = keywords
        
        logger.info(f"Merged keywords for {len(merged_keywords)} intents")
        return merged_keywords
    except Exception as e:
        logger.error(f"Error merging keywords: {e}")
        return default_keywords

def save_keywords(keywords, filename):
    """
    Save keywords to a JSON file
    
    Args:
        keywords: Dictionary of keywords
        filename: File to save to
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(keywords, f, indent=2)
        
        logger.info(f"Saved keywords for {len(keywords)} intents to {filename}")
    except Exception as e:
        logger.error(f"Error saving keywords: {e}")

def main():
    """Main function"""
    logger.info("Starting keyword analysis")
    
    # Load labeled data
    intent_texts = load_labeled_data('data/labeled_data.csv')
    
    if not intent_texts:
        logger.error("No labeled data found")
        return
    
    # Extract top keywords
    top_keywords = get_top_keywords(intent_texts, top_n=10)
    
    # Merge with existing keywords
    existing_keywords_path = 'models/keyword_classifier/keywords.json'
    merged_keywords = merge_with_existing_keywords(top_keywords, existing_keywords_path)
    
    # Save merged keywords
    save_keywords(merged_keywords, existing_keywords_path)
    
    # Print summary
    print("\nTop keywords for each intent:")
    for intent, keywords in merged_keywords.items():
        print(f"{intent}: {', '.join(keywords[:10])}")
    
    logger.info("Keyword analysis complete")

if __name__ == "__main__":
    main()
