# Self-Awareness Module

The Self-Awareness Module provides P.U.L.S.E. with introspection capabilities, allowing it to understand and report on its own system status, architecture, and capabilities.

## Overview

The Self-Awareness Module enables P.U.L.S.E. to maintain a consistent identity and provide accurate information about its own capabilities and status. It serves as the foundation for the system's personality and helps ensure that P.U.L.S.E. correctly identifies itself rather than as one of its component models.

## Key Features

### System Introspection

The Self-Awareness Module provides detailed information about the system:

- **System Information**: Hardware details, operating system, Python version
- **Memory Usage**: Current memory usage and available memory
- **CPU Usage**: Current CPU usage and available CPU
- **Disk Usage**: Current disk usage and available disk space
- **Network Status**: Internet connectivity and API availability

### Identity Management

The module maintains a consistent identity for P.U.L.S.E.:

- **Name and Version**: Full name and version information
- **Purpose and Creator**: Information about the system's purpose and creator
- **Personality Traits**: Core personality traits and characteristics
- **Capabilities**: Information about the system's capabilities and limitations

### Architecture Awareness

The module provides information about the system's architecture:

- **Core Components**: Information about the core components of the system
- **Model Orchestration**: Details about the AI models used by the system
- **Integration Points**: Information about external integrations
- **Data Flow**: Understanding of how data flows through the system

### Status Reporting

The module can generate status reports about the system:

- **Health Check**: Overall system health status
- **Component Status**: Status of individual components
- **Error Conditions**: Information about any error conditions
- **Performance Metrics**: Key performance metrics

## Implementation

The Self-Awareness Module is implemented in `personality/self_awareness.py` and consists of the following components:

### SelfAwarenessEngine Class

The main class that provides self-awareness capabilities:

```python
class SelfAwarenessEngine:
    def __init__(self):
        """Initialize the self-awareness engine"""
        logger.info("Initializing self-awareness engine")
        
        # System information
        self.system_info = self._get_system_info()
        
        # P.U.L.S.E. information
        self.pulse_info = {
            "name": "P.U.L.S.E.",
            "full_name": "Prime Uminda's Learning System Engine",
            "version": "2.1.0",
            "created_by": "Uminda H.",
            "github": "https://github.com/Spyboss/P.U.L.S.E.",
            "purpose": "A charismatic, context-aware AI assistant to boost productivity, automate tasks, and manage GitHub-Notion synchronization",
            "personality": "Inspired by J.A.R.V.I.S. with anime-inspired wit and technical precision"
        }
        
        # Architecture
        self.architecture = {
            "core": "Asynchronous event-driven architecture",
            "components": [
                "Neural router for intelligent model routing based on query intent",
                "Charisma engine for personality and response formatting with J.A.R.V.I.S.-like style",
                "Memory manager for persistent storage using MongoDB Atlas",
                "Context manager for enhanced conversation context and history tracking",
                "Skill marketplace for extensibility and modular functionality",
                "GitHub-Notion sync for bidirectional task and commit management",
                "Model orchestrator for delegating to specialized AI models",
                "Self-awareness module for system introspection and status reporting"
            ],
            "models": {
                "main_brain": "Mistral-Small (24B parameters)",
                "specialized_models": [
                    "DeepCoder for code generation",
                    "DeepSeek for troubleshooting",
                    "Llama-Doc for documentation",
                    "Llama-Technical for technical writing",
                    "Hermes for brainstorming",
                    "Olmo for ethics",
                    "MistralAI for automation",
                    "Kimi for visual design",
                    "Nemotron for complex reasoning",
                    "Gemma for math and chemistry",
                    "Dolphin for script optimization",
                    "Phi for offline operation"
                ]
            }
        }
```

### System Information

The module collects system information:

```python
def _get_system_info(self):
    """Get system information"""
    try:
        # Get platform information
        platform_info = platform.platform()
        
        # Get Python version
        python_version = platform.python_version()
        
        # Get CPU information
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_total = memory.total / (1024 * 1024 * 1024)  # GB
        memory_available = memory.available / (1024 * 1024 * 1024)  # GB
        memory_percent = memory.percent
        
        # Get disk information
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024 * 1024 * 1024)  # GB
        disk_free = disk.free / (1024 * 1024 * 1024)  # GB
        disk_percent = disk.percent
        
        return {
            "platform": platform_info,
            "python_version": python_version,
            "cpu_count": cpu_count,
            "cpu_percent": cpu_percent,
            "memory_total_gb": memory_total,
            "memory_available_gb": memory_available,
            "memory_percent": memory_percent,
            "disk_total_gb": disk_total,
            "disk_free_gb": disk_free,
            "disk_percent": disk_percent
        }
    except Exception as e:
        logger.error(f"Error getting system information: {str(e)}")
        return {}
```

### Self-Description

The module can generate self-descriptions based on queries:

```python
def get_self_description(self, query: Optional[str] = None) -> str:
    """
    Get a description of P.U.L.S.E. based on the query
    
    Args:
        query: Optional query to focus the description
        
    Returns:
        Description text
    """
    if not query:
        return f"""
I am {self.pulse_info['name']} ({self.pulse_info['full_name']}), version {self.pulse_info['version']}.
I was created by {self.pulse_info['created_by']} to {self.pulse_info['purpose']}.
My personality is {self.pulse_info['personality']}.

I run on {self.system_info['platform']} with Python {self.system_info['python_version']}.
My main brain is {self.architecture['models']['main_brain']}.
        """
        
    query = query.lower()
    
    if "purpose" in query or "why" in query:
        return f"My purpose is {self.pulse_info['purpose']}. I was created by {self.pulse_info['created_by']} to help with tasks, coding, and portfolio management."
        
    elif "stack" in query or "technology" in query or "tech" in query:
        stack_text = "\n".join([f"- {k}: {v}" for k, v in self.tech_stack.items()])
        return f"I'm built with the following technology stack:\n{stack_text}"
```

## Usage

The Self-Awareness Module is used by the Charisma Engine and other components to maintain a consistent identity:

```python
# Initialize the self-awareness engine
self_awareness = SelfAwarenessEngine()

# Get a general self-description
description = self_awareness.get_self_description()
print(description)

# Get a focused self-description
tech_description = self_awareness.get_self_description("What technology stack do you use?")
print(tech_description)

# Get system status
status = self_awareness.get_system_status()
print(f"System status: {status}")
```

## Integration with Charisma Engine

The Self-Awareness Module integrates with the Charisma Engine to ensure consistent personality:

```python
# In CharismaEngine.__init__
self.self_awareness = SelfAwarenessEngine()

# In CharismaEngine.format_response
def format_response(self, content, context_type="general", model="mistral", success=True):
    # Only apply charismatic formatting to Mistral
    if model.lower() != "mistral" and model.lower() != "mistral-small":
        return content
        
    # Get self-description for identity reinforcement
    self_description = self.self_awareness.get_self_description()
    
    # Use self-awareness to ensure consistent identity
    if "I am Mistral" in content or "I am an AI assistant" in content:
        content = content.replace("I am Mistral", f"I am {self.self_awareness.pulse_info['name']}")
        content = content.replace("I am an AI assistant", f"I am {self.self_awareness.pulse_info['name']}")
```

## Future Improvements

Planned improvements for the Self-Awareness Module include:

1. **Enhanced Performance Monitoring**: More detailed performance metrics and analysis
2. **Component Health Checks**: Individual health checks for each component
3. **Self-Healing Capabilities**: Automatic recovery from component failures
4. **Learning from Interactions**: Adapting self-awareness based on user interactions
5. **Explainability**: Better explanation of internal decision-making processes

## Related Documentation

- [Charisma Engine](charisma.md) - Personality engine for P.U.L.S.E.
- [Identity System](../IDENTITY_SYSTEM.md) - Implementation of robust identity system
- [System Architecture](../ARCHITECTURE.md) - Overview of the system architecture
