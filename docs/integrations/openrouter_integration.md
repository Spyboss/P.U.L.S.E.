# OpenRouter Integration for General Pulse

## Overview

This document describes the integration of [OpenRouter](https://openrouter.ai/) into the General Pulse application to solve API billing and reliability issues with multiple language model providers.

## Implementation Status

✅ **IMPLEMENTED** - June 2025
🔄 **UPDATED** - April 15, 2025 - Enhanced model selection with specialized models for different tasks

## What is OpenRouter?

OpenRouter is a unified API gateway that provides access to multiple AI models through a single endpoint. It simplifies the process of working with various AI models by:

- Providing a single API endpoint and authentication method
- Handling proper formatting for different providers
- Managing fallbacks automatically
- Consolidating billing across multiple providers

## Why We Integrated OpenRouter

The integration addresses several challenges:

1. **Billing issues with direct APIs**:

   - Claude API: "Credit balance too low" errors
   - DeepSeek API: "Insufficient Balance" errors
   - Grok API: Authentication failures with provided keys

2. **Simplified management**:

   - Single API key for multiple models
   - Consistent response format
   - Reduced maintenance overhead

3. **Cost optimization**:
   - Pay-as-you-go pricing model
   - No need for separate accounts with each provider

## Implementation Details

### Integration Architecture

The integration uses a hybrid approach:

- OpenRouter for models with billing/authentication issues (Claude, Grok, DeepSeek)
- Direct API for Gemini (which works reliably)
- Fallback to simulation mode when needed

### Key Components

1. **Environment Configuration**

   - Added `OPENROUTER_API_KEY` to `.env` file
   - Kept original API keys as fallback

2. **Model Interface**

   - Added `_call_openrouter_api()` method to `ModelInterface` class
   - Modified `call_model_api()` to use OpenRouter for specific models
   - Created model mappings for OpenRouter models

3. **Configuration**
   - Added OpenRouter section to `model_api_config.yaml`
   - Defined model mappings for Claude, Grok (using Mistral as replacement), and DeepSeek

### Recent Enhancements (April 15, 2025)

Several significant improvements were made to enhance the OpenRouter integration:

1. **Expanded Model Selection**:

   - Added 20+ specialized models for different tasks
   - Implemented intelligent query classification to select the best model
   - Created a sophisticated fallback strategy for model reliability

2. **Improved Query Classification**:

   - Enhanced keyword detection for better model selection
   - Added support for multi-word phrases in classification
   - Implemented category-based classification for related tasks

3. **Robust Fallback Strategy**:

   - Created a category-based fallback system
   - Implemented prioritized fallback chains for each query type
   - Added dedicated fallback models for reliability

4. **Better Error Handling**:
   - Enhanced error detection and reporting
   - Added detailed logging for model selection and fallbacks
   - Improved response processing for different model formats

### API Model Mappings

General Pulse now uses a sophisticated model selection system with specialized models for different tasks:

#### Coding and Technical Tasks

- **Code Generation**: `deepseek/deepseek-coder-v2:free` - Best for generating code
- **Debugging**: `agentica-org/deepcoder-14b-preview:free` - Good for debugging issues
- **Algorithm Design**: `meta-llama/llama-4-code:free` - Good for algorithm design

#### Documentation and Explanation

- **Documentation**: `meta-llama/llama-4-scout:free` - Great for documentation
- **Explanation**: `anthropic/claude-3-5-sonnet:free` - Best for explanations
- **Summarization**: `anthropic/claude-3-haiku:free` - Fast summarization

#### Problem Solving

- **Troubleshooting**: `deepseek/deepseek-r1-zero:free` - Technical troubleshooting
- **General Problem Solving**: `google/gemini-1.5-flash:free` - General problem solving

#### Information and Research

- **Trends**: `mistralai/mistral-small-24b-instruct-2501:free` - Good for trends
- **Research**: `meta-llama/llama-3.3-70b-instruct:free` - Detailed research

#### Content Creation

- **Content**: `meta-llama/llama-3.2-11b-vision-instruct:free` - Content with images
- **Creative**: `anthropic/claude-3-opus:free` - Most creative content
- **Writing**: `anthropic/claude-3-sonnet:free` - High-quality writing

#### Technical and Specialized

- **Technical**: `meta-llama/llama-3.3-70b-instruct:free` - Technical content
- **Mathematics**: `deepseek/deepseek-math:free` - Mathematical problems

#### Brainstorming and Ideas

- **Brainstorming**: `nousresearch/nous-hermes-2-mixtral-8x7b-sft:free` - Creative ideas
- **Innovative Ideas**: `google/gemini-1.5-pro:free` - Innovative thinking

#### Ethics and Responsibility

- **Ethics**: `anthropic/claude-3-5-sonnet:free` - Ethical considerations

#### Fallback Options

- **Primary Fallback**: `microsoft/phi-3-mini:free` - Primary fallback
- **Secondary Fallback**: `deepseek/deepseek-v3-base:free` - Secondary fallback

## Current Usage in Application

### AI-Driven Commit Message Generation

The OpenRouter integration is a key component of our AI-driven commit message generator:

- DeepSeek (via OpenRouter) is used as the default model for code-related tasks
- The integration provides reliable API access for generating commit messages
- Our testing shows DeepSeek produces higher quality commit messages than other models

Example in `github_skills.py`:

```python
def create_commit_message(self, repo_url, file_path, diff=None):
    # ...
    model_name = "deepseek-coder"  # Default to DeepSeek for code-related tasks
    self.logger.info(f"Generating commit message using {model_name}")
    response = model.call_model_api(prompt, model_name=model_name)
    # ...
```

### Basic Usage

The OpenRouter integration is transparent to existing code. The `ModelInterface` automatically routes requests to OpenRouter for specific models:

```python
from skills.model_interface import ModelInterface

# Initialize the interface
model_interface = ModelInterface()

# Call models as usual - OpenRouter is used automatically
response = model_interface.call_model_api("claude", "Your prompt here")
response = model_interface.call_model_api("grok", "Your prompt here")
response = model_interface.call_model_api("deepseek", "Your prompt here")

# Gemini continues to use direct API
response = model_interface.call_model_api("gemini", "Your prompt here")
```

### Credit Limit Considerations

When using the free tier OpenRouter API, be aware of the following credit limitations:

1. **Token Constraints**:

   - Models like Claude-3-Opus have tight token limits on the free tier
   - For Claude-3-Opus, we default to max_tokens=400 to stay within free credit limits
   - The system will automatically detect and report credit limit errors

2. **Error Handling**:
   - OpenRouter may return 200 status codes with embedded error objects
   - Our system now properly detects and handles these errors
   - The `execute_with_fallbacks` method includes retry logic for transient errors

Example handling credit limits:

```python
async def test_model_execution_flow():
    """Test model flow with proper credit limit handling"""
    flow = ExecutionFlow()
    result = await flow.execute_query(
        'Your prompt here',
        model_preference='claude-3-opus',
        system_prompt='',
        temperature=0.7,
        max_tokens=400  # Reduced to fit within free credits
    )
    return result
```

### Advanced Configuration

The model selection system is configured directly in the `skills/model_orchestrator.py` file. The system includes:

1. **Model Definitions**: A comprehensive dictionary of specialized models for different tasks
2. **Query Classification**: A sophisticated system to determine the best model for each query
3. **Fallback Strategy**: A robust fallback system to ensure reliability

```python
# Example from model_orchestrator.py
self.free_models = {
    # Coding and technical tasks
    "code": "deepseek/deepseek-coder-v2:free",  # Best for code generation
    "debug": "agentica-org/deepcoder-14b-preview:free",  # Good for debugging
    "algorithm": "meta-llama/llama-4-code:free",  # Good for algorithm design

    # Documentation and explanation
    "docs": "meta-llama/llama-4-scout:free",  # Great for documentation
    "explain": "anthropic/claude-3-5-sonnet:free",  # Best for explanations
    "summarize": "anthropic/claude-3-haiku:free",  # Fast summarization

    # ... and many more specialized models
}
```

## Testing

A dedicated test script (`test_openrouter.py`) verifies the OpenRouter integration:

```bash
# Test with direct API call
python test_openrouter.py

# Test with execution flow
python test_openrouter.py flow
```

The test script:

- Validates connections to OpenRouter for each model
- Tests real API responses and credit limit handling
- Reports success/failure for each model

## Performance Findings

After extensive testing, we've observed:

1. **Model Performance**:

   - DeepSeek performs best for code-related tasks
   - Claude excels at creative content and explanations
   - Mistral (our replacement for Grok) works well for general queries

2. **Response Quality**:
   - DeepSeek generates concise, accurate commit messages
   - Claude occasionally returns empty responses (issue tracked)
   - All models show better performance through OpenRouter than direct APIs

## Troubleshooting

### Common Issues

1. **Empty responses from Claude**

   - Issue: Claude sometimes returns empty responses through OpenRouter
   - Solution: Add retry logic or fall back to simulation

2. **Invalid model ID errors**

   - Issue: OpenRouter model IDs may change over time
   - Solution: Update model mappings in `configs/model_api_config.yaml`

3. **Network connectivity issues**

   - Issue: Connection timeouts or SSL errors
   - Solution: Check network settings, proxy configuration, or VPN status

4. **Credit limit errors**
   - Issue: "This request requires more credits, or fewer max_tokens" errors
   - Solution: Reduce max_tokens parameter or upgrade to a paid OpenRouter account

### Simulation Fallback

The system automatically falls back to simulation mode when:

- OpenRouter API is unavailable
- A specific model on OpenRouter has issues
- The API returns an error response

This ensures the application remains functional even when external services fail.

## Maintenance

### API Key Management

The OpenRouter API key should be rotated periodically for security purposes:

1. Create a new API key at [OpenRouter Console](https://openrouter.ai/keys)
2. Update the `.env` file with the new key
3. Test with `test_openrouter.py` before deploying

### Monitoring Usage

Monitor your OpenRouter usage at [OpenRouter Dashboard](https://openrouter.ai/dashboard) to:

- Track costs
- Monitor request volumes
- Identify potential issues

## Future Improvements

Potential enhancements to the integration:

1. **Performance-Based Model Selection**: Dynamically adjust model selection based on historical performance metrics
2. **Adaptive Learning**: Learn from successful and failed model calls to improve selection over time
3. **Parallel Model Querying**: Query multiple models simultaneously for critical tasks and select the best response
4. **Response Caching**: Cache responses for frequently used prompts to reduce API calls
5. **Custom Model Fine-Tuning**: Explore fine-tuning options for specialized tasks
6. **Cost Optimization**: Implement token counting and budget management for optimal model selection
7. **Streaming Responses**: Add support for streaming responses for real-time interactions
8. **Structured Output Formatting**: Implement consistent output formatting across different models

## References

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Quickstart Guide](https://openrouter.ai/docs/quickstart)
- [Available Models](https://openrouter.ai/models)
