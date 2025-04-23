from utils.minilm_classifier import MiniLMClassifier

# Initialize the classifier
classifier = MiniLMClassifier()

# Test classification
test_queries = [
    "help",
    "status",
    "what is the capital of France?",
    "write a Python function to calculate factorial",
    "enable offline mode",
    "test gemini",
    "github search repositories"
]

print("Testing MiniLM classifier...")
for query in test_queries:
    result = classifier.classify_detailed(query)
    print(f"Query: '{query}'")
    print(f"  Intent: {result['intent']}")
    print(f"  Confidence: {result['confidence']:.4f}")
    print(f"  Secondary intents: {[i['intent'] for i in result['secondary_intents']]}")
    print()

# Free memory
classifier.free_memory()
print("Memory freed successfully")
