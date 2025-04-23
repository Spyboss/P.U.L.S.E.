# General Pulse AI Crew

General Pulse uses a dynamic AI crew system where multiple specialized AI models work together to provide the best possible assistance. Each model has a specific role and personality, and they can collaborate to solve complex problems.

## Crew Structure

The AI crew is structured as follows:

- **Leader**: Gemini is the crew leader, orchestrating the other models and maintaining a personal relationship with the user.
- **Specialists**: Each specialist model has a specific role and expertise.
- **Paid Fallbacks**: These models are available as fallbacks when needed, but require paid API access.

## Crew Members

### Leader

- **Gemini** - Default Chat - Main orchestrator that knows the user personally and delegates to specialists.

### Specialists

- **DeepSeek** - Troubleshooting - Diagnoses errors, provides DevOps fixes, and solves technical problems.
- **DeepCoder** - Code Generation - Writes, debugs, and optimizes code with clean, efficient implementations.
- **Llama-Doc** - Documentation - Creates clear, concise documentation and explains complex concepts.
- **Mistral-Small** - Trends Analyst - Tracks market and AI trends, providing up-to-date information.
- **Llama-Content** - Content Creation - Generates engaging content for blogs, marketing, and more.
- **Llama-Technical** - Technical Translation - Translates technical jargon into understandable language.
- **Hermes** - Brainstorming - Generates creative ideas and innovative solutions.
- **Olmo** - Ethical AI - Provides ethical considerations and detects bias in AI systems.
- **MistralAI** - Task Automation - Automates workflows and streamlines processes.
- **Kimi** - Visual Reasoning - Analyzes images and provides visual content assistance.
- **Nemotron** - Advanced Reasoning - Handles complex reasoning tasks and in-depth analysis.

### Paid Fallbacks

- **Claude** - Fallback (Paid) - Paid fallback model for complex tasks requiring nuanced understanding.
- **Grok** - Fallback (Paid) - Paid fallback model with real-time knowledge and witty responses.

## Query Types and Routing

General Pulse automatically routes queries to the appropriate specialist based on the query type:

### Code-related Queries (DeepCoder)

- `code`: General coding help
- `debug`: Debugging code issues
- `algorithm`: Algorithm design and optimization

### Documentation-related Queries (Llama-Doc)

- `docs`: Documentation creation and management
- `explain`: Detailed explanations of concepts
- `summarize`: Summarizing complex information

### Problem-solving Queries (DeepSeek)

- `troubleshoot`: Diagnosing and fixing issues
- `solve`: Finding solutions to problems

### Information and Research Queries (Mistral-Small)

- `trends`: Information about current trends
- `research`: In-depth research on topics

### Content Creation Queries (Llama-Content)

- `content`: General content creation
- `creative`: Creative writing and ideas
- `write`: Writing assistance

### Technical Queries (Llama-Technical)

- `technical`: Technical information and explanations
- `math`: Mathematical problems and concepts

### Brainstorming Queries (Hermes)

- `brainstorm`: Generating multiple ideas
- `ideas`: Creative ideation

### Ethics Queries (Olmo)

- `ethics`: Ethical considerations and analysis

### Task Automation Queries (MistralAI)

- `automate`: Automating repetitive tasks
- `workflow`: Optimizing workflows
- `process`: Improving processes

## How to Use the AI Crew

You can interact with the AI crew in several ways:

1. **Direct Model Queries**: Ask a specific model directly.

   ```
   ask gemini what's the weather today?
   ask deepcoder to write a Python function to calculate factorial
   ask mistral-small about the latest AI trends
   ```

2. **Query Type Routing**: Use specialized query types to automatically route to the right model.

   ```
   ask code how to implement a binary search tree
   ask troubleshoot why my Docker container keeps crashing
   ask write a blog post about AI ethics
   ```

3. **Default Queries**: If you don't specify a model or query type, Gemini (the leader) will handle your query.
   ```
   what's the capital of France?
   how do I improve my coding skills?
   ```

## Crew Dynamics

The AI crew members are aware of each other and can suggest other specialists when appropriate. For example:

- If you ask DeepCoder about troubleshooting a server issue, it might suggest consulting DeepSeek.
- If you ask Mistral-Small about code optimization, it might suggest DeepCoder.
- If you ask Gemini about ethical considerations, it might delegate to Olmo.

This collaborative approach ensures you always get the best possible assistance for your specific needs.

## Model Availability

The availability of models depends on your API keys and the current status of the services:

- **Gemini**: Requires a valid Google AI API key.
- **OpenRouter Models**: All specialist models require a valid OpenRouter API key.
- **Paid Fallbacks**: Claude and Grok require paid API access.

You can check the current status of all models with the `status` command.
