import re
from skills.optimized_model_interface import OptimizedModelInterface

# Create model interface
mi = OptimizedModelInterface()

# Read the optimized_model_interface.py file directly
with open('skills/optimized_model_interface.py', 'r') as f:
    content = f.read()

# Extract the model mapping using regex with a more specific pattern
mapping_match = re.search(r'openrouter_model_mapping\s*=\s*\{([^{]*?)\}', content, re.DOTALL)
if mapping_match:
    mapping_str = mapping_match.group(1).strip()
    print("OpenRouter model mappings:")
    for line in mapping_str.splitlines():
        print(line.strip())

# Check available models
print("\nAvailable models:")
print(mi.get_available_models())

# Check model display names
print("\nModel display names:")
print(mi.model_mappings)