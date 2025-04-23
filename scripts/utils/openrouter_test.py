import requests
import json
import time

# OpenRouter API Key
API_KEY = "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"

def test_openrouter_call(model_name, prompt):
    """Test a single OpenRouter API call"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://general-pulse.app",
        "X-Title": "General Pulse Assistant"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    print(f"Making API call to OpenRouter with model {model_name}...")
    start_time = time.time()
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        elapsed = time.time() - start_time
        print(f"Response received in {elapsed:.2f} seconds")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("API RESPONSE:")
            print(json.dumps(result, indent=2))
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print("\nGENERATED CONTENT:")
                print(content)
            else:
                print("\nNo content found in response")
        else:
            print("ERROR RESPONSE:")
            print(response.text)
            
    except Exception as e:
        print(f"Error making API call: {str(e)}")

def get_available_models():
    """Get the list of available models from OpenRouter"""
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        response = requests.get(
            url="https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            models = response.json()
            print("AVAILABLE MODELS:")
            for model in models:
                if "id" in model and "pricing" in model and "context_length" in model:
                    print(f"{model['id']} - {model.get('description', 'No description')}")
                    print(f"  Context: {model['context_length']} tokens")
                    if model['pricing'].get('prompt'):
                        print(f"  Pricing: ${model['pricing']['prompt']} per 1M prompt tokens, ${model['pricing']['completion']} per 1M completion tokens")
                    
                    # Check if model is available on free tier
                    if model.get('free_tier', False):
                        print("  🟢 Available on free tier")
                    else:
                        print("  🔴 Not available on free tier")
                    print()
        else:
            print(f"Error fetching models: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error fetching models: {str(e)}")

if __name__ == "__main__":
    # Get the list of available models first
    get_available_models()
    
    print("\n" + "="*50 + "\n")
    
    # Test different models
    models = [
        "anthropic/claude-3-haiku",        # Claude
        "google/gemini-pro",               # Gemini
        "deepseek/deepseek-r1-zero:free"   # DeepSeek R1 Zero (free tier)
    ]
    
    prompt = "Explain the benefits of meditation in 3 sentences."
    
    for model in models:
        test_openrouter_call(model, prompt)
        print("\n" + "="*50 + "\n")
        time.sleep(2)  # Pause between requests 