#!/usr/bin/env python3
"""
Test script for the intent classifier
Validates the functionality of the intent classifier with various input cases
"""

import os
import sys
import logging
import importlib.util

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("test_intent_classifier")

# Ensure we can import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test cases for intent classification validation
TEST_CASES = [
    ("What time is it?", "datetime_intent"),
    ("Create a new GitHub repo", "github_intent"),
    ("help me", "help_intent"),
    ("Write a blog post about AI", "content_creation_intent"),
    ("Ask Claude what is the weather like today", "model_query_intent"),
    ("Create a journal entry in Notion", "notion_intent"),
    ("Remind me to call mom tomorrow", "task_tracker_intent"),
    ("Hello, how are you today?", "greeting_intent"),
    ("What's the system status?", "system_status_intent")
]

def check_dependencies():
    """Check if we have the necessary dependencies installed"""
    try:
        import structlog
        logger.info("✅ structlog is installed")
    except ImportError:
        logger.error("❌ structlog is not installed. Install with: pip install structlog")
        return False
    
    try:
        from transformers import pipeline
        logger.info("✅ transformers is installed")
    except ImportError:
        logger.warning("⚠️ transformers is not installed. Classifier will use regex fallback.")
        logger.warning("  Install with: pip install transformers")
    
    try:
        import torch
        logger.info(f"✅ torch is installed (version {torch.__version__})")
        logger.info(f"   CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        logger.warning("⚠️ torch is not installed. Models will use CPU only.")
        logger.warning("  Install with: pip install torch")
    
    return True

def load_intent_classifier():
    """Load the intent classifier"""
    try:
        # First try loading from utils.intent_handler
        try:
            from utils.intent_handler import IntentClassifier
            logger.info("✅ Loaded IntentClassifier from utils.intent_handler")
            return IntentClassifier()
        except (ImportError, AttributeError):
            # Try next location
            pass
        
        # Try loading from skills.intent_classifier
        try:
            from skills.intent_classifier import IntentClassifier
            logger.info("✅ Loaded IntentClassifier from skills.intent_classifier")
            return IntentClassifier()
        except (ImportError, AttributeError):
            # Try final location
            pass
        
        # Try utils.intent_classifier as last resort
        from utils.intent_classifier import IntentClassifier
        logger.info("✅ Loaded IntentClassifier from utils.intent_classifier")
        return IntentClassifier()
        
    except (ImportError, AttributeError) as e:
        logger.error(f"❌ Failed to load IntentClassifier: {str(e)}")
        logger.error("  Make sure the module path is correct")
        return None

def validate_classifier(classifier):
    """Validate the classifier with test cases"""
    if classifier is None:
        logger.error("❌ Cannot validate without a classifier")
        return False
    
    results = {}
    passed = 0
    total = len(TEST_CASES)
    
    logger.info("\n🧪 Starting intent classification tests...")
    
    for i, (text, expected) in enumerate(TEST_CASES, 1):
        try:
            result = classifier.classify(text)
            success = result == expected
            
            if success:
                passed += 1
                logger.info(f"✅ Test {i}/{total}: \"{text}\" → {result}")
            else:
                logger.warning(f"❌ Test {i}/{total}: \"{text}\" → {result} (expected: {expected})")
                
            results[text] = success
        except Exception as e:
            logger.error(f"💥 Error on test {i}/{total}: \"{text}\" - {str(e)}")
            results[text] = False
    
    success_rate = (passed / total) * 100
    logger.info(f"\n📊 Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        logger.info("✅ PASS: Intent classifier is working well")
    elif success_rate >= 60:
        logger.info("⚠️ PARTIAL PASS: Intent classifier needs some improvement")
    else:
        logger.info("❌ FAIL: Intent classifier needs significant fixes")
    
    return success_rate >= 60  # Return True if at least 60% pass

def main():
    """Main test function"""
    logger.info("🔍 Testing Intent Classifier")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Missing critical dependencies. Please install them first.")
        return 1
    
    # Load classifier
    classifier = load_intent_classifier()
    if classifier is None:
        return 1
    
    # Run validation
    if not validate_classifier(classifier):
        logger.error("❌ Validation failed")
        return 1
    
    logger.info("✨ Test completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 