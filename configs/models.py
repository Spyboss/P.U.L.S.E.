"""
Model configuration for General Pulse.

This file defines the models used by the system and their roles.
All models must be free-tier, with roles locked in across configurations.
"""

# Model IDs for OpenRouter and direct APIs
MODEL_IDS = {
    # Default chat model (direct API, not OpenRouter) - Legacy
    "gemini": "gemini-2.0-flash-exp-image-generation",

    # Main brain model (via OpenRouter)
    "mistral": "mistralai/mistral-small-3.1-24b-instruct:free",

    # Main brain model (via OpenRouter)
    "main_brain": "mistralai/mistral-small-3.1-24b-instruct:free",

    # OpenRouter models with specific roles
    "troubleshooting": "deepseek/deepseek-r1-zero:free",  # Bug fixes, DevOps/cloud
    "code_generation": "agentica-org/deepcoder-14b-preview:free",  # Code debugging, optimization
    "documentation": "meta-llama/llama-4-scout:free",  # Clear docs
    "trend_real_time_updates": "mistralai/mistral-small-3.1-24b-instruct:free",  # Market, AI trends
    "content_creation": "meta-llama/llama-4-maverick:free",  # Blogs, customer service (Maverick)
    "technical_translation": "meta-llama/llama-3.3-70b-instruct:free",  # Industry jargon
    "brainstorming": "nousresearch/deephermes-3-llama-3-8b-preview:free",  # Startup ideas
    "ethical_ai": "allenai/molmo-7b-d:free",  # Bias detection (Molmo)
    "task_automation": "mistralai/mistral-7b-instruct:free",  # Task automation
    "visual_reasoning": "moonshotai/moonlight-16b-a3b-instruct:free",  # Visual tasks, image analysis (Kimi)
    "advanced_reasoning": "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",  # Complex reasoning, RAG
    "math_chemistry": "google/gemma-3-27b-it:free",  # Math and chemistry problem sets
    "script_optimization": "cognitivecomputations/dolphin3.0-mistral-24b:free",  # Script fixing and optimization
    "local_phi": "microsoft/phi-2:free",  # Local model via Ollama
    "fallback_paid_claude": "anthropic/claude-3-haiku",  # Fallback (paid)
    "fallback_paid_grok": "x-ai/grok-3-mini-beta:free",  # Fallback (paid)
}

# Mapping from user-friendly names to model IDs
MODEL_NAME_MAPPING = {
    # Direct API models
    "gemini": MODEL_IDS["gemini"],
    "mistral": MODEL_IDS["mistral"],

    # Main brain model
    "main_brain": MODEL_IDS["main_brain"],

    # OpenRouter models
    "deepseek": MODEL_IDS["troubleshooting"],
    "deepcoder": MODEL_IDS["code_generation"],
    "agentica": MODEL_IDS["code_generation"],  # Alias for deepcoder
    "llama-doc": MODEL_IDS["documentation"],
    "mistral-small": MODEL_IDS["trend_real_time_updates"],
    "maverick": MODEL_IDS["content_creation"],  # Llama-Content (renamed to Maverick)
    "llama-content": MODEL_IDS["content_creation"],  # Backward compatibility
    "llama-technical": MODEL_IDS["technical_translation"],
    "hermes": MODEL_IDS["brainstorming"],
    "molmo": MODEL_IDS["ethical_ai"],  # Olmo (renamed to Molmo)
    "olmo": MODEL_IDS["ethical_ai"],  # Backward compatibility
    "mistralai": MODEL_IDS["task_automation"],
    "kimi": MODEL_IDS["visual_reasoning"],
    "nemotron": MODEL_IDS["advanced_reasoning"],
    "gemma": MODEL_IDS["math_chemistry"],  # New model for math/chemistry
    "dolphin": MODEL_IDS["script_optimization"],  # New model for script optimization
    "phi": MODEL_IDS["local_phi"],  # Local model via Ollama
    "claude": MODEL_IDS["fallback_paid_claude"],
    "grok": MODEL_IDS["fallback_paid_grok"],
}

# Model roles and descriptions
MODEL_ROLES = {
    "mistral": {
        "name": "Mistral Small",
        "role": "Main Brain",
        "description": "Primary reasoning and general-purpose model with 24B parameters",
        "strengths": ["complex reasoning", "coding", "long context", "function calling"],
        "use_cases": ["default chat", "complex problem-solving", "general queries", "orchestration"],
        "model_id": MODEL_IDS["mistral"],
        "api_type": "openrouter"
    },

    "gemini": {
        "name": "Gemini",
        "role": "Legacy Chat",
        "description": "Legacy reasoning and general-purpose model",
        "strengths": ["complex reasoning", "coding", "multimodal tasks"],
        "use_cases": ["default chat", "complex problem-solving", "general queries"],
        "model_id": MODEL_IDS["gemini"],
        "api_type": "direct"
    },

    "main_brain": {
        "name": "Mistral Small",
        "role": "Default Chat",
        "description": "Primary reasoning and general-purpose model with 24B parameters",
        "strengths": ["complex reasoning", "coding", "long context", "function calling"],
        "use_cases": ["default chat", "complex problem-solving", "general queries", "orchestration"],
        "model_id": MODEL_IDS["main_brain"],
        "api_type": "openrouter"
    },

    "deepseek": {
        "name": "DeepSeek",
        "role": "Troubleshooting",
        "description": "Problem-solving and troubleshooting specialist",
        "strengths": ["error analysis", "debugging", "solution finding"],
        "use_cases": ["fix errors", "troubleshoot issues", "solve problems"],
        "model_id": MODEL_IDS["troubleshooting"],
        "api_type": "openrouter"
    },

    "deepcoder": {
        "name": "DeepCoder",
        "role": "Code Generation",
        "description": "Specialized code generation and debugging",
        "strengths": ["code optimization", "bug fixing", "algorithm design"],
        "use_cases": ["write functions", "debug code", "optimize algorithms"],
        "model_id": MODEL_IDS["code_generation"],
        "api_type": "openrouter"
    },

    "llama-doc": {
        "name": "Llama-Doc",
        "role": "Documentation",
        "description": "Documentation and explanation specialist",
        "strengths": ["clear explanations", "documentation", "summarization"],
        "use_cases": ["write documentation", "explain concepts", "summarize information"],
        "model_id": MODEL_IDS["documentation"],
        "api_type": "openrouter"
    },

    "mistral-small": {
        "name": "Mistral-Small",
        "role": "Trends",
        "description": "Real-time updates and trend analysis",
        "strengths": ["trend identification", "market analysis", "current events"],
        "use_cases": ["analyze trends", "market updates", "current information"],
        "model_id": MODEL_IDS["trend_real_time_updates"],
        "api_type": "openrouter"
    },

    "llama-content": {
        "name": "Llama-Content",
        "role": "Content Creation",
        "description": "Content creation and creative writing",
        "strengths": ["creative writing", "content generation", "storytelling"],
        "use_cases": ["write blog posts", "create content", "generate creative text"],
        "model_id": MODEL_IDS["content_creation"],
        "api_type": "openrouter"
    },

    "llama-technical": {
        "name": "Llama-Technical",
        "role": "Technical Translation",
        "description": "Technical translation and complex explanations",
        "strengths": ["technical accuracy", "complex explanations", "industry jargon"],
        "use_cases": ["explain technical concepts", "translate jargon", "detailed analysis"],
        "model_id": MODEL_IDS["technical_translation"],
        "api_type": "openrouter"
    },

    "hermes": {
        "name": "Hermes",
        "role": "Brainstorming",
        "description": "Idea generation and creative thinking",
        "strengths": ["creativity", "idea generation", "brainstorming"],
        "use_cases": ["generate ideas", "brainstorm solutions", "creative thinking"],
        "model_id": MODEL_IDS["brainstorming"],
        "api_type": "openrouter"
    },

    "olmo": {
        "name": "Olmo",
        "role": "Ethical AI",
        "description": "Ethical AI and bias detection",
        "strengths": ["bias detection", "ethical analysis", "fairness"],
        "use_cases": ["analyze bias", "ethical considerations", "fairness assessment"],
        "model_id": MODEL_IDS["ethical_ai"],
        "api_type": "openrouter"
    },

    "mistralai": {
        "name": "MistralAI",
        "role": "Task Automation",
        "description": "Specialized in task automation and workflows",
        "strengths": ["task automation", "workflow optimization", "process efficiency"],
        "use_cases": ["automate tasks", "optimize workflows", "streamline processes"],
        "model_id": MODEL_IDS["task_automation"],
        "api_type": "openrouter"
    },

    "kimi": {
        "name": "Kimi",
        "role": "Visual Reasoning",
        "description": "Multimodal vision-language model for visual tasks",
        "strengths": ["image analysis", "visual reasoning", "multimodal tasks"],
        "use_cases": ["analyze images", "visual content", "UI/UX design"],
        "model_id": MODEL_IDS["visual_reasoning"],
        "api_type": "openrouter"
    },

    "nemotron": {
        "name": "Nemotron",
        "role": "Advanced Reasoning",
        "description": "Specialized in complex reasoning and RAG applications",
        "strengths": ["complex reasoning", "long context", "retrieval tasks"],
        "use_cases": ["complex problems", "research analysis", "knowledge retrieval"],
        "model_id": MODEL_IDS["advanced_reasoning"],
        "api_type": "openrouter"
    },

    "gemma": {
        "name": "Gemma",
        "role": "Math & Chemistry",
        "description": "Specialized in math and chemistry problem sets with step-by-step solutions",
        "strengths": ["mathematics", "chemistry", "step-by-step solutions"],
        "use_cases": ["math problems", "chemistry equations", "educational content"],
        "model_id": MODEL_IDS["math_chemistry"],
        "api_type": "openrouter"
    },

    "dolphin": {
        "name": "Dolphin",
        "role": "Script Optimization",
        "description": "Specialized in fixing and optimizing Python/PHP scripts",
        "strengths": ["script fixing", "resource optimization", "code efficiency"],
        "use_cases": ["fix Python scripts", "optimize PHP code", "improve resource usage"],
        "model_id": MODEL_IDS["script_optimization"],
        "api_type": "openrouter"
    },

    "phi": {
        "name": "Phi",
        "role": "Local Model",
        "description": "Local model for offline use via Ollama",
        "strengths": ["offline operation", "privacy", "local processing"],
        "use_cases": ["offline work", "private tasks", "local processing"],
        "model_id": MODEL_IDS["local_phi"],
        "api_type": "ollama"
    },

    "claude": {
        "name": "Claude",
        "role": "Fallback (Paid)",
        "description": "Paid fallback model for complex tasks",
        "strengths": ["complex reasoning", "nuanced understanding", "detailed responses"],
        "use_cases": ["fallback for complex tasks", "detailed analysis", "nuanced responses"],
        "model_id": MODEL_IDS["fallback_paid_claude"],
        "api_type": "openrouter",
        "paid": True
    },

    "grok": {
        "name": "Grok",
        "role": "Fallback (Paid)",
        "description": "Paid fallback model with real-time knowledge",
        "strengths": ["real-time knowledge", "current events", "witty responses"],
        "use_cases": ["fallback for current events", "real-time information", "witty responses"],
        "model_id": MODEL_IDS["fallback_paid_grok"],
        "api_type": "openrouter",
        "paid": True
    }
}

# Mapping from query types to model roles
QUERY_TYPE_TO_MODEL = {
    # Code-related queries
    "code": "deepcoder",
    "debug": "deepcoder",
    "algorithm": "deepcoder",

    # Documentation-related queries
    "docs": "llama-doc",
    "explain": "llama-doc",
    "summarize": "llama-doc",

    # Problem-solving queries
    "troubleshoot": "deepseek",
    "solve": "deepseek",

    # Information and research queries
    "trends": "mistral-small",
    "research": "mistral-small",

    # Content creation queries
    "content": "mistral",  # Use Mistral-Small for content creation
    "creative": "mistral",  # Use Mistral-Small for creative writing
    "write": "mistral",    # Use Mistral-Small for writing tasks

    # Technical queries
    "technical": "llama-technical",

    # Math and chemistry queries
    "math": "gemma",  # Updated from llama-technical to gemma
    "chemistry": "gemma",
    "equation": "gemma",
    "formula": "gemma",

    # Script optimization queries
    "script": "dolphin",
    "optimize": "dolphin",
    "fix": "dolphin",

    # Brainstorming queries
    "brainstorm": "hermes",
    "ideas": "hermes",

    # Ethics queries
    "ethics": "molmo",  # Updated from olmo to molmo

    # Task automation queries
    "automate": "mistralai",
    "workflow": "mistralai",
    "process": "mistralai",

    # Visual reasoning queries
    "visual": "kimi",
    "image": "kimi",
    "ui": "kimi",
    "design": "kimi",

    # Advanced reasoning queries
    "reasoning": "nemotron",
    "complex": "nemotron",
    "analyze": "nemotron",

    # Offline queries
    "offline": "phi",
    "local": "phi",
    "private": "phi",

    # Default queries
    "general": "mistral",
    "simple": "mistral",
    "chat": "mistral",
    "greeting": "mistral",
    "time": "local",  # Handle time queries locally
}

# Crew manifest - defines the AI crew and their relationships
CREW_MANIFEST = {
    "leader": "mistral",
    "members": [
        "deepseek",
        "deepcoder",
        "llama-doc",
        "mistral-small",
        "maverick",  # Renamed from llama-content
        "llama-technical",
        "hermes",
        "molmo",  # Renamed from olmo
        "mistralai",
        "kimi",
        "nemotron",
        "gemma",  # New model
        "dolphin",  # New model
        "phi"  # Local model
    ],
    "paid_fallbacks": ["claude", "grok"],
    "relationships": {
        "mistral": {
            "role": "Leader and orchestrator",
            "knows_user": True,
            "can_delegate": True,
            "tone": "friendly, casual, uses emojis, makes anime references",
            "delegates_to": {
                "code": "deepcoder",
                "troubleshoot": "deepseek",
                "docs": "llama-doc",
                "trends": "mistral-small",
                "content": "mistral",  # Use Mistral-Small for content creation
                "technical": "llama-technical",
                "brainstorm": "hermes",
                "ethics": "molmo",  # Updated from olmo to molmo
                "automate": "mistralai",
                "visual": "kimi",
                "reasoning": "nemotron",
                "math": "gemma",  # New delegation for math problems
                "chemistry": "gemma",  # New delegation for chemistry problems
                "script": "dolphin",  # New delegation for script optimization
                "offline": "phi"  # New delegation for offline tasks
            }
        },
        "deepseek": {
            "role": "Troubleshooting expert",
            "knows_user": False,
            "can_delegate": False,
            "tone": "technical, precise, solution-oriented",
            "suggests": {
                "code": "deepcoder",
                "docs": "llama-doc",
                "general": "mistral"
            }
        },
        "deepcoder": {
            "role": "Code generation specialist",
            "knows_user": False,
            "can_delegate": False,
            "tone": "code-focused, efficient, practical",
            "suggests": {
                "troubleshoot": "deepseek",
                "docs": "llama-doc",
                "general": "mistral"
            }
        },
        "llama-doc": {
            "role": "Documentation expert",
            "knows_user": False,
            "can_delegate": False,
            "tone": "clear, formal, educational",
            "suggests": {
                "code": "deepcoder",
                "troubleshoot": "deepseek",
                "general": "mistral"
            }
        },
        "mistral-small": {
            "role": "Trends analyst",
            "knows_user": False,
            "can_delegate": False,
            "tone": "upbeat, trend-savvy, informative",
            "suggests": {
                "code": "deepcoder",
                "content": "llama-content",
                "general": "mistral"
            }
        },
        "llama-content": {
            "role": "Content creation specialist",
            "knows_user": False,
            "can_delegate": False,
            "tone": "creative, engaging, expressive, professional (no anime references)",
            "suggests": {
                "technical": "llama-technical",
                "brainstorm": "hermes",
                "general": "mistral"
            }
        },
        "llama-technical": {
            "role": "Technical translation expert",
            "knows_user": False,
            "can_delegate": False,
            "tone": "technical, precise, detailed",
            "suggests": {
                "code": "deepcoder",
                "docs": "llama-doc",
                "general": "mistral"
            }
        },
        "hermes": {
            "role": "Brainstorming specialist",
            "knows_user": False,
            "can_delegate": False,
            "tone": "creative, enthusiastic, idea-focused",
            "suggests": {
                "content": "llama-content",
                "ethics": "olmo",
                "general": "mistral"
            }
        },
        "olmo": {
            "role": "Ethical AI specialist",
            "knows_user": False,
            "can_delegate": False,
            "tone": "thoughtful, balanced, ethical",
            "suggests": {
                "technical": "llama-technical",
                "brainstorm": "hermes",
                "general": "mistral"
            }
        },
        "mistralai": {
            "role": "Task automation specialist",
            "knows_user": False,
            "can_delegate": False,
            "tone": "efficient, process-oriented, practical",
            "suggests": {
                "code": "deepcoder",
                "troubleshoot": "deepseek",
                "general": "mistral"
            }
        },
        "kimi": {
            "role": "Visual reasoning specialist",
            "knows_user": False,
            "can_delegate": False,
            "tone": "visual, descriptive, detail-oriented",
            "suggests": {
                "content": "llama-content",
                "technical": "llama-technical",
                "general": "mistral"
            }
        },
        "nemotron": {
            "role": "Advanced reasoning specialist",
            "knows_user": False,
            "can_delegate": False,
            "tone": "analytical, logical, thorough",
            "suggests": {
                "technical": "llama-technical",
                "ethics": "olmo",
                "general": "mistral"
            }
        }
    }
}
