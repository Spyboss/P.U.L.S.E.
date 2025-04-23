"""
Test the keyword intent classifier with various inputs
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the intent handler
from utils.keyword_intent_handler import KeywordIntentHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/classifier_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('classifier_test')

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

def test_classifier():
    """Test the keyword intent classifier with various inputs"""
    logger.info("Starting classifier test")
    
    # Initialize the classifier
    classifier = KeywordIntentHandler()
    
    # Test cases for each intent
    test_cases = {
        "task": [
            "show my tasks",
            "list all tasks",
            "add task 'Client call tomorrow' priority 3",
            "create task 'Fix bug in login page'",
            "update task 'Review PR' priority 1",
            "complete task 'Send email'",
            "mark task 'Deploy to production' as done",
            "prioritize task 'Client meeting'",
            "what tasks do I have",
            "show pending tasks"
        ],
        "time": [
            "what time is it",
            "what time is it in Tokyo",
            "current time in London",
            "time in New York in 2 hours",
            "what's the date today",
            "what day is it",
            "what's the time",
            "current date",
            "time difference between Tokyo and London"
        ],
        "github": [
            "github Spyboss/pulse-cli info",
            "show github microsoft/vscode issues",
            "list issues for github.com/facebook/react",
            "github google/tensorflow commit utils/tensor_utils.py",
            "generate commit message for main.py in Spyboss/pulse",
            "create github repo pulse-cli",
            "check github status for Spyboss/pulse-cli"
        ],
        "notion": [
            "create notion document called 'Meeting Notes'",
            "add journal entry to notion",
            "create a notion page titled 'Project Ideas'",
            "make a journal entry",
            "add note to notion about 'Client Feedback'",
            "create new document in notion"
        ],
        "ai_query": [
            "ask claude what's CI/CD",
            "ask grok how to fix timezone conversion bugs",
            "ask deepseek how to implement fuzzy matching",
            "query claude about machine learning",
            "ask ai about python best practices",
            "what does claude think about microservices",
            "tell me about quantum computing",
            "explain how blockchain works",
            "write a blog post about AI ethics"
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
    
    # Add some edge cases and typos
    edge_cases = [
        "taks list",
        "shw my tasks",
        "add taks 'Fix bug' priorty 2",
        "tme in Toky",
        "what tim is it",
        "githb info Spyboss/pulse",
        "ask claud about python",
        "hlp me",
        "notion jrnal"
    ]
    
    # Run tests
    results = {
        "correct": 0,
        "incorrect": 0,
        "total": 0,
        "by_intent": {},
        "edge_cases": [],
        "failed_cases": []
    }
    
    # Initialize results by intent
    for intent in test_cases:
        results["by_intent"][intent] = {
            "correct": 0,
            "total": len(test_cases[intent]),
            "accuracy": 0
        }
    
    # Test regular cases
    for expected_intent, cases in test_cases.items():
        for case in cases:
            results["total"] += 1
            
            # Classify the case
            classified_intent = classifier.classify(case)
            
            # Check if correct
            is_correct = classified_intent == expected_intent
            
            if is_correct:
                results["correct"] += 1
                results["by_intent"][expected_intent]["correct"] += 1
                logger.info(f"✓ '{case}' correctly classified as '{classified_intent}'")
            else:
                results["incorrect"] += 1
                results["failed_cases"].append({
                    "text": case,
                    "expected": expected_intent,
                    "actual": classified_intent
                })
                logger.warning(f"✗ '{case}' incorrectly classified as '{classified_intent}' (expected '{expected_intent}')")
    
    # Test edge cases
    for case in edge_cases:
        # Try to determine the expected intent
        expected_intent = None
        for intent, keywords in [
            ("task", ["task", "taks", "list", "add", "show", "priorty"]),
            ("time", ["time", "tme", "tim", "toky"]),
            ("github", ["github", "githb"]),
            ("notion", ["notion", "jrnal"]),
            ("ai_query", ["ask", "claud"]),
            ("system", ["help", "hlp"])
        ]:
            if any(keyword in case.lower() for keyword in keywords):
                expected_intent = intent
                break
        
        if expected_intent:
            # Classify the case
            classified_intent = classifier.classify(case)
            
            # Check if correct
            is_correct = classified_intent == expected_intent
            
            results["edge_cases"].append({
                "text": case,
                "expected": expected_intent,
                "actual": classified_intent,
                "correct": is_correct
            })
            
            if is_correct:
                logger.info(f"✓ Edge case: '{case}' correctly classified as '{classified_intent}'")
            else:
                logger.warning(f"✗ Edge case: '{case}' incorrectly classified as '{classified_intent}' (expected '{expected_intent}')")
    
    # Calculate accuracy
    overall_accuracy = results["correct"] / results["total"] * 100 if results["total"] > 0 else 0
    
    # Calculate accuracy by intent
    for intent in results["by_intent"]:
        intent_data = results["by_intent"][intent]
        intent_data["accuracy"] = intent_data["correct"] / intent_data["total"] * 100 if intent_data["total"] > 0 else 0
    
    # Calculate edge case accuracy
    edge_correct = sum(1 for case in results["edge_cases"] if case["correct"])
    edge_accuracy = edge_correct / len(results["edge_cases"]) * 100 if results["edge_cases"] else 0
    
    # Add summary to results
    results["summary"] = {
        "overall_accuracy": overall_accuracy,
        "edge_case_accuracy": edge_accuracy,
        "timestamp": datetime.now().isoformat()
    }
    
    # Print summary
    print("\n" + "="*50)
    print(f"CLASSIFIER TEST RESULTS")
    print("="*50)
    print(f"Overall accuracy: {overall_accuracy:.1f}% ({results['correct']}/{results['total']})")
    print(f"Edge case accuracy: {edge_accuracy:.1f}% ({edge_correct}/{len(results['edge_cases'])})")
    print("\nAccuracy by intent:")
    for intent, data in results["by_intent"].items():
        print(f"  {intent}: {data['accuracy']:.1f}% ({data['correct']}/{data['total']})")
    
    # Print failed cases
    if results["failed_cases"]:
        print("\nFailed cases:")
        for case in results["failed_cases"]:
            print(f"  '{case['text']}' → got '{case['actual']}', expected '{case['expected']}'")
    
    # Save results to file
    try:
        with open('logs/classifier_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to logs/classifier_results.json")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    # Suggest keywords to add
    if results["failed_cases"]:
        print("\nSuggested keywords to add:")
        for case in results["failed_cases"]:
            # Extract potential keywords from the failed case
            words = set(case["text"].lower().split())
            # Remove common stopwords
            stopwords = {"a", "an", "the", "in", "on", "at", "to", "for", "with", "is", "are", "was", "were"}
            words = words - stopwords
            print(f"  For intent '{case['expected']}': {', '.join(words)}")
    
    logger.info(f"Classifier test completed with {overall_accuracy:.1f}% accuracy")
    return results

if __name__ == "__main__":
    test_classifier()
