# General Pulse Usage Guide

This guide provides detailed instructions on how to use General Pulse and its AI crew effectively.

## Getting Started

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/uminda/general-pulse.git
   cd general-pulse
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up API keys in a `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

### Running General Pulse

Launch General Pulse with:

```bash
python pulse.py
```

Optional flags:

- `--simulate`: Simulate AI responses (for testing)
- `--user <username>`: Set the user identifier
- `--memory <path>`: Specify the path to the memory database
- `--debug`: Enable debug mode

## Basic Commands

### General Commands

- `help`: Show help message with available commands
- `status`: Show system status, including hardware, AI models, and session information
- `exit` or `quit`: Exit the application

### Time Commands

- `what time is it`: Get the current local time
- `what time is it in [location]`: Get the time in a specific location
  ```
  what time is it in Tokyo?
  what time is it in New York?
  ```

### Goal Commands

- `add goal [text]`: Add a new goal
  ```
  add goal Learn Python programming
  add goal priority 3 Finish the tourist guide app
  ```
- `list goals`: List all active goals
- `complete goal [text]`: Mark a goal as completed
  ```
  complete goal Learn Python
  ```
- `delete goal [text]`: Delete a goal
  ```
  delete goal Old project
  ```

### Memory Commands

- `search memory [query]`: Search memory for a query
  ```
  search memory python
  ```
- `search memory`: Show recent memories
- `save to memory [text]`: Save a memory
  ```
  save to memory I prefer dark mode in my code editor
  ```
- `save to memory [category]: [data]`: Save categorized data to memory
  ```
  save to memory projects: Tourist Guide App
  save to memory interests: Machine Learning
  ```
- `recall [category]`: Recall data from memory
  ```
  recall projects
  recall interests
  ```

## Using the AI Crew

### Direct Model Queries

Ask a specific AI crew member directly:

```
ask gemini what's the weather today?
ask deepcoder to write a Python function to calculate factorial
ask mistral-small about the latest AI trends
```

### Specialized Query Types

Use specialized query types to automatically route to the right model:

```
ask code how to implement a binary search tree
ask troubleshoot why my Docker container keeps crashing
ask write a blog post about AI ethics
ask visual analyze this UI design
ask reasoning solve this complex problem
```

### Available Models

#### Leader

- `ask gemini [query]`: Ask Gemini, the crew leader

#### Specialists

- `ask deepseek [query]`: Ask DeepSeek, the troubleshooting expert
- `ask deepcoder [query]`: Ask DeepCoder, the code generation specialist
- `ask llama-doc [query]`: Ask Llama-Doc, the documentation expert
- `ask mistral-small [query]`: Ask Mistral-Small, the trends analyst
- `ask llama-content [query]`: Ask Llama-Content, the content creation specialist
- `ask llama-technical [query]`: Ask Llama-Technical, the technical translation expert
- `ask hermes [query]`: Ask Hermes, the brainstorming specialist
- `ask olmo [query]`: Ask Olmo, the ethical AI specialist
- `ask kimi [query]`: Ask Kimi, the visual reasoning specialist
- `ask nemotron [query]`: Ask Nemotron, the advanced reasoning specialist
- `ask mistralai [query]`: Ask MistralAI, the task automation specialist

#### Paid Fallbacks

- `ask claude [query]`: Ask Claude, the paid fallback for complex tasks
- `ask grok [query]`: Ask Grok, the paid fallback with real-time knowledge

## Personality Customization

General Pulse has a customizable personality that adapts to your preferences:

- `show personality`: Show current personality traits
- `adjust [trait] to [value]`: Adjust a personality trait (0.0 to 1.0)
  ```
  adjust informative to 0.8
  adjust casual to 0.6
  adjust humor to 0.9
  ```

Available traits:

- `informative`: How detailed and informative responses are
- `courageous`: Willingness to tackle difficult topics
- `positive`: Level of positivity in responses
- `casual`: How casual vs. formal the tone is
- `strict`: How strict or lenient the responses are
- `personal`: How personal vs. impersonal the responses are
- `honest`: Level of directness and honesty
- `humor`: Amount of humor in responses
- `anime_references`: Frequency of anime references

## Advanced Features

### System Status

Check the system status with:

```
status
```

This shows:

- Hardware information (memory, disk, CPU)
- AI model usage statistics
- AI crew availability
- Specialized query types
- Session information

### CLI UI

Launch the CLI UI with:

```
launch cli ui
```

This provides a more interactive interface for using General Pulse.

## Troubleshooting

If you encounter issues:

1. Check the system status with `status` to verify model availability
2. Ensure your API keys are correctly set in the `.env` file
3. Check your internet connection
4. Try restarting General Pulse
5. Check the logs for error messages

## Getting Help

If you need help with General Pulse:

1. Use the `help` command to see available commands
2. Ask Gemini for assistance with General Pulse features
3. Ask DeepSeek to troubleshoot any issues you're experiencing
4. Refer to the documentation in the `docs` directory
