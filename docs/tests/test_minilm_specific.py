from utils.minilm_classifier import MiniLMClassifier

# Initialize the classifier
classifier = MiniLMClassifier()

# Test a specific query
query = "help"
result = classifier.classify_detailed(query)

print(f"Query: '{query}'")
print(f"Intent: {result['intent']}")
print(f"Confidence: {result['confidence']:.4f}")
print(f"Secondary intents: {[i['intent'] for i in result['secondary_intents']]}")

# Free memory
classifier.free_memory()
print("Memory freed successfully")
