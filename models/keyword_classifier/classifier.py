
import re
import json
import os

class KeywordIntentClassifier:
    def __init__(self, keywords_path="models/keyword_classifier/keywords.json"):
        # Load keywords
        with open(keywords_path, "r", encoding="utf-8") as f:
            self.keywords = json.load(f)
        
        # Add common stopwords to ignore
        self.stopwords = set([
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with",
            "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "i", "you", "he", "she", "it", "we", "they", "my", "your",
            "his", "her", "its", "our", "their", "me", "him", "us", "them"
        ])
    
    def classify(self, text):
        # Tokenize text
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        # Remove stopwords
        words = words - self.stopwords
        
        # Calculate score for each intent
        scores = {}
        for intent, intent_keywords in self.keywords.items():
            # Count matching keywords
            matches = words.intersection(intent_keywords)
            scores[intent] = len(matches)
        
        # Get the intent with the highest score
        if any(scores.values()):
            max_intent = max(scores.items(), key=lambda x: x[1])[0]
            return max_intent
        else:
            return "other"
