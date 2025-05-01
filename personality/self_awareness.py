"""
Self-awareness engine for P.U.L.S.E.
Provides information about the system's purpose, capabilities, and state
"""

import os
import sys
import platform
import psutil
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import custom logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.log import get_logger

# Configure logger
logger = get_logger("self_awareness")

class SelfAwarenessEngine:
    """Engine for P.U.L.S.E. self-awareness and introspection"""

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

        # Technical stack
        self.tech_stack = {
            "core": "Python 3.9+, Mistral-Small (OpenRouter), MiniLM for intent classification",
            "data": "MongoDB Atlas (pulse DB) for persistent storage, SQLite for local caching",
            "portfolio": "React/Node.js (uminda-portfolio.pages.dev)",
            "skills": "Modular skill system with marketplace integration and specialized model routing",
            "integrations": "GitHub API, Notion API, OpenRouter API for AI model access"
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
                "main_brain": "Mistral-Small (mistralai/mistral-small-3.1-24b-instruct:free)",
                "code": "DeepCoder (agentica-org/deepcoder-14b-preview:free)",
                "troubleshooting": "DeepSeek (deepseek/deepseek-r1-zero:free)",
                "documentation": "Llama-Doc (meta-llama/llama-4-scout:free)",
                "technical": "Llama-Technical (meta-llama/llama-3.3-70b-instruct:free)",
                "brainstorming": "Hermes (nousresearch/deephermes-3-llama-3-8b-preview:free)",
                "ethics": "Molmo (allenai/molmo-7b-d:free)",
                "visual_reasoning": "Kimi (moonshotai/moonlight-16b-a3b-instruct:free)",
                "advanced_reasoning": "Nemotron (nvidia/llama-3.1-nemotron-ultra-253b-v1:free)",
                "math_chemistry": "Gemma (google/gemma-3-27b-it:free)",
                "script_optimization": "Dolphin (cognitivecomputations/dolphin3.0-mistral-24b:free)",
                "intent": "MiniLM (local) for fast command classification",
                "offline": "Phi (microsoft/phi-2:free via Ollama)"
            }
        }

        # Capabilities
        self.capabilities = [
            "Natural language understanding and generation via Mistral-Small",
            "Code generation and analysis with DeepCoder",
            "Troubleshooting and debugging with DeepSeek",
            "Documentation and explanation with Llama-Doc",
            "Technical content with Llama-Technical",
            "Brainstorming and idea generation with Hermes",
            "Ethical AI and bias detection with Molmo",
            "Visual reasoning and design with Kimi",
            "Advanced reasoning and problem-solving with Nemotron",
            "Mathematical and chemical problem-solving with Gemma",
            "Script optimization and automation with Dolphin",
            "Task management and automation through GitHub-Notion sync",
            "Memory management with MongoDB Atlas for persistent storage",
            "Bidirectional GitHub-Notion synchronization for commits and tasks",
            "Portfolio management and updates via GitHub integration",
            "Charismatic personality with anime references and J.A.R.V.I.S.-inspired responses",
            "Self-awareness and introspection for system status reporting",
            "Adaptive model routing based on query intent and system constraints",
            "Error handling and recovery for robust operation",
            "Resource optimization for low-memory environments",
            "Offline operation with Phi via Ollama"
        ]

        logger.info("Self-awareness engine initialized")

    def _get_system_info(self) -> Dict[str, Any]:
        """
        Get system information

        Returns:
            Dictionary with system information
        """
        try:
            # Get memory information
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "platform": platform.system(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "total_ram": f"{memory.total / (1024**3):.2f}GB",
                "available_ram": f"{memory.available / (1024**3):.2f}GB",
                "total_disk": f"{disk.total / (1024**3):.2f}GB",
                "free_disk": f"{disk.free / (1024**3):.2f}GB",
                "cpu_count": psutil.cpu_count(logical=True)
            }
        except Exception as e:
            logger.error(f"Error getting system information: {str(e)}")
            return {
                "platform": platform.system(),
                "python_version": platform.python_version()
            }

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

        elif "architecture" in query or "design" in query or "structure" in query:
            components = "\n".join([f"- {c}" for c in self.architecture['components']])
            return f"My architecture is {self.architecture['core']} with the following components:\n{components}"

        elif "model" in query or "brain" in query or "ai" in query:
            # Group models by category
            model_categories = {
                "Main Brain": ["main_brain"],
                "Code & Development": ["code", "troubleshooting", "script_optimization"],
                "Documentation & Explanation": ["documentation", "technical"],
                "Creativity & Reasoning": ["brainstorming", "advanced_reasoning", "visual_reasoning"],
                "Specialized Knowledge": ["math_chemistry", "ethics"],
                "Local & Offline": ["intent", "offline"]
            }

            models_text = ""
            for category, model_keys in model_categories.items():
                models_text += f"\n{category}:\n"
                for key in model_keys:
                    if key in self.architecture['models']:
                        models_text += f"- {key}: {self.architecture['models'][key]}\n"

            return f"I use multiple specialized AI models for different tasks:{models_text}\n\nMy main brain is {self.architecture['models']['main_brain']}.\n\nI can route queries to specialized models using the 'ask X' format, e.g., 'ask code how to implement a binary search tree'."

        elif "capability" in query or "can you" in query or "able to" in query:
            capabilities_text = "\n".join([f"- {c}" for c in self.capabilities])
            return f"Here are my capabilities:\n{capabilities_text}"

        elif "system" in query or "hardware" in query or "computer" in query:
            return f"""
I'm running on:
- Platform: {self.system_info['platform']}
- Processor: {self.system_info['processor']}
- Python: {self.system_info['python_version']}
- RAM: {self.system_info['total_ram']} (Available: {self.system_info['available_ram']})
- Disk: {self.system_info['total_disk']} (Free: {self.system_info['free_disk']})
- CPU Cores: {self.system_info['cpu_count']}
            """

        elif "version" in query or "update" in query:
            return f"I am {self.pulse_info['name']} version {self.pulse_info['version']}. You can find the latest updates at {self.pulse_info['github']}."

        else:
            return f"""
I am {self.pulse_info['name']} ({self.pulse_info['full_name']}), version {self.pulse_info['version']}.
I was created by {self.pulse_info['created_by']} to {self.pulse_info['purpose']}.
My personality is {self.pulse_info['personality']}.

You can ask me about my purpose, tech stack, architecture, models, capabilities, system, or version.
            """

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model information or None if not found
        """
        # Normalize model name
        model_name_lower = model_name.lower()

        # Map common variations to canonical names
        model_name_map = {
            "mistral": "main_brain",
            "mistralsmall": "main_brain",
            "mistral-small": "main_brain",
            "deepcoder": "code",
            "deepseek": "troubleshooting",
            "llamadoc": "documentation",
            "llama-doc": "documentation",
            "llamatechnical": "technical",
            "llama-technical": "technical",
            "hermes": "brainstorming",
            "molmo": "ethics",
            "kimi": "visual_reasoning",
            "nemotron": "advanced_reasoning",
            "gemma": "math_chemistry",
            "dolphin": "script_optimization",
            "minilm": "intent",
            "phi": "offline"
        }

        # Get canonical name if available
        canonical_name = model_name_map.get(model_name_lower, model_name_lower)

        # Check if model exists in architecture
        if canonical_name in self.architecture['models']:
            # Get model description
            model_desc = self.architecture['models'][canonical_name]

            # Extract model name and ID
            parts = model_desc.split('(')
            name = parts[0].strip()
            model_id = parts[1].strip(')') if len(parts) > 1 else ""

            # Define model information
            model_info = {
                "name": name,
                "id": model_id,
                "role": self._get_model_role(canonical_name),
                "strengths": self._get_model_strengths(canonical_name),
                "use_cases": self._get_model_use_cases(canonical_name)
            }

            return model_info

        return None

    def _get_model_role(self, model_key: str) -> str:
        """Get the role of a model"""
        roles = {
            "main_brain": "Main Brain",
            "code": "Code Generation",
            "troubleshooting": "Troubleshooting",
            "documentation": "Documentation",
            "technical": "Technical Translation",
            "brainstorming": "Brainstorming",
            "ethics": "Ethical AI",
            "visual_reasoning": "Visual Reasoning",
            "advanced_reasoning": "Advanced Reasoning",
            "math_chemistry": "Math & Chemistry",
            "script_optimization": "Script Optimization",
            "intent": "Intent Classification",
            "offline": "Offline Operation"
        }

        return roles.get(model_key, "Specialized Tasks")

    def _get_model_strengths(self, model_key: str) -> List[str]:
        """Get the strengths of a model"""
        strengths = {
            "main_brain": ["general knowledge", "balanced reasoning", "instruction following", "chat"],
            "code": ["code generation", "debugging", "algorithm design", "technical problem-solving"],
            "troubleshooting": ["error analysis", "debugging", "problem diagnosis", "solution finding"],
            "documentation": ["clear explanations", "documentation", "concept simplification", "tutorials"],
            "technical": ["technical writing", "complex concept translation", "technical accuracy"],
            "brainstorming": ["idea generation", "creative thinking", "exploration", "innovation"],
            "ethics": ["ethical analysis", "bias detection", "fairness evaluation", "value alignment"],
            "visual_reasoning": ["visual concepts", "design thinking", "spatial reasoning", "UI/UX"],
            "advanced_reasoning": ["complex problem-solving", "logical analysis", "multi-step reasoning"],
            "math_chemistry": ["mathematical computation", "chemical formulas", "scientific reasoning"],
            "script_optimization": ["code optimization", "script efficiency", "automation", "performance"],
            "intent": ["fast classification", "command recognition", "intent detection"],
            "offline": ["local operation", "privacy", "no internet required"]
        }

        return strengths.get(model_key, ["specialized knowledge", "focused capabilities"])

    def _get_model_use_cases(self, model_key: str) -> List[str]:
        """Get the use cases of a model"""
        use_cases = {
            "main_brain": ["general questions", "conversation", "everyday tasks", "information retrieval"],
            "code": ["programming help", "code generation", "debugging", "software development"],
            "troubleshooting": ["error fixing", "problem diagnosis", "technical support", "debugging"],
            "documentation": ["explaining concepts", "creating documentation", "tutorials", "guides"],
            "technical": ["technical writing", "complex explanations", "technical translation"],
            "brainstorming": ["idea generation", "creative projects", "exploration", "innovation"],
            "ethics": ["ethical analysis", "bias evaluation", "fairness assessment"],
            "visual_reasoning": ["design concepts", "visual ideas", "UI/UX discussions"],
            "advanced_reasoning": ["complex problems", "logical puzzles", "multi-step reasoning"],
            "math_chemistry": ["mathematical problems", "chemical questions", "scientific computation"],
            "script_optimization": ["code optimization", "performance improvement", "automation"],
            "intent": ["command classification", "quick responses", "intent detection"],
            "offline": ["local operation", "privacy-sensitive tasks", "offline work"]
        }

        return use_cases.get(model_key, ["specialized tasks", "focused applications"])

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current system status

        Returns:
            Dictionary with system status
        """
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Get CPU usage - use a try-except block to handle potential errors
            try:
                # First try with a very short interval
                cpu_percent = psutil.cpu_percent(interval=0.1)
            except Exception as cpu_err:
                logger.warning(f"Error getting CPU percent with interval: {str(cpu_err)}")
                try:
                    # Try without interval parameter
                    cpu_percent = psutil.cpu_percent()
                except Exception:
                    # Last resort - use a fixed value
                    logger.error("Failed to get CPU percent, using default value")
                    cpu_percent = 0

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024**2),
                "disk_percent": disk.percent,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# For testing
if __name__ == "__main__":
    engine = SelfAwarenessEngine()
    print(engine.get_self_description("What is your purpose?"))
    print("\n" + "-"*50 + "\n")
    print(engine.get_self_description("What is your tech stack?"))
    print("\n" + "-"*50 + "\n")
    print(engine.get_status())
