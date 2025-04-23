"""
DistilBERT Intent Classifier for General Pulse
Provides offline intent classification using DistilBERT
"""

import os
import asyncio
import structlog
import json
import gc
from typing import Dict, Any, List, Optional, Union

# Configure logger
logger = structlog.get_logger("distilbert_classifier")

class DistilBERTClassifier:
    """
    Intent classifier using DistilBERT for offline intent classification
    """

    def __init__(self):
        """
        Initialize the DistilBERT classifier
        """
        self.model = None
        self.tokenizer = None
        self.classifier = None
        self.is_initialized = False
        self.is_available = False
        self.labels = [
            "code", "debug", "algorithm", "docs", "explain", "summarize",
            "troubleshoot", "solve", "trends", "research", "content", "creative",
            "write", "technical", "math", "brainstorm", "ideas", "ethics",
            "visual", "reasoning", "general", "time", "reminder", "goal",
            "model", "memory", "personality", "cli_ui", "ollama"
        ]

        # Try to initialize the model
        self._try_initialize()

    def _try_initialize(self):
        """
        Try to initialize the model
        """
        try:
            # Check if transformers is available
            import importlib
            if importlib.util.find_spec("transformers") is None:
                logger.warning("Transformers package not found. DistilBERT classifier will not be available.")
                self.is_available = False
                return

            # Check if torch is available
            if importlib.util.find_spec("torch") is None:
                logger.warning("PyTorch package not found. DistilBERT classifier will not be available.")
                self.is_available = False
                return

            # Import required packages
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

            # Set is_available flag
            self.is_available = True

            # Check if we have enough memory
            import psutil
            available_gb = psutil.virtual_memory().available / (1024 ** 3)

            # Clean up memory if it's low
            if available_gb < 1.0:
                logger.warning(f"Low memory detected ({available_gb:.1f}GB available). Attempting to free memory...")
                gc.collect()
                torch.cuda.empty_cache() if torch.cuda.is_available() else None

                # Check memory again
                available_gb = psutil.virtual_memory().available / (1024 ** 3)
                logger.info(f"Available memory after cleanup: {available_gb:.2f} GB")

                if available_gb < 0.5:  # Critical threshold
                    logger.warning(f"Critically low memory ({available_gb:.1f}GB available). DistilBERT classifier will not be initialized.")
                    return

            # Initialize the model
            try:
                # Check if we have a trained model
                model_path = 'models/distilbert/intent_classifier'
                if os.path.exists(model_path):
                    logger.info(f"Loading trained DistilBERT model from {model_path}")

                    # Load label mapping
                    label_map_path = os.path.join(model_path, 'label_map.json')
                    if os.path.exists(label_map_path):
                        with open(label_map_path, 'r') as f:
                            mapping_data = json.load(f)
                            self.id2label = mapping_data.get('id2label', {})
                            # Convert string keys to integers
                            self.id2label = {int(k): v for k, v in self.id2label.items()}
                    else:
                        logger.warning(f"Label map not found at {label_map_path}, using default labels")
                        self.id2label = {i: label for i, label in enumerate(self.labels)}

                    # Load model and tokenizer
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path)

                    # Try to use 4-bit quantization if available
                    try:
                        from bitsandbytes.nn import Linear4bit
                        from transformers import BitsAndBytesConfig

                        logger.info("Using 4-bit quantization for memory efficiency")
                        bnb_config = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4",
                            bnb_4bit_compute_dtype=torch.float16
                        )

                        model = AutoModelForSequenceClassification.from_pretrained(
                            model_path,
                            quantization_config=bnb_config,
                            device_map="auto"
                        )
                    except ImportError:
                        logger.warning("bitsandbytes not available, using standard model")
                        model = AutoModelForSequenceClassification.from_pretrained(
                            model_path,
                            device_map="auto" if torch.cuda.is_available() else None
                        )

                    # Create pipeline
                    self.classifier = pipeline(
                        "text-classification",
                        model=model,
                        tokenizer=self.tokenizer,
                        device=-1  # Use CPU
                    )

                    self.is_initialized = True
                    logger.info("Trained DistilBERT classifier initialized successfully")
                else:
                    # Use default model
                    logger.warning(f"Trained model not found at {model_path}, using default model")
                    model_name = "distilbert-base-uncased"

                    # Initialize tokenizer
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)

                    # Use text classification pipeline
                    self.classifier = pipeline(
                        "text-classification",
                        model=model_name,
                        tokenizer=self.tokenizer,
                        device=-1  # Use CPU
                    )

                    self.is_initialized = True
                    logger.info("Default DistilBERT classifier initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize DistilBERT classifier: {str(e)}")
                self.is_initialized = False

        except ImportError as e:
            logger.warning(f"Failed to import required packages: {str(e)}")
            self.is_available = False

    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """
        Classify the intent of a text

        Args:
            text: Text to classify

        Returns:
            Classification result
        """
        if not self.is_available:
            return {
                "success": False,
                "message": "DistilBERT classifier is not available",
                "intent": "unknown",
                "confidence": 0.0
            }

        if not self.is_initialized:
            # Try to initialize again
            self._try_initialize()

            if not self.is_initialized:
                return {
                    "success": False,
                    "message": "DistilBERT classifier is not initialized",
                    "intent": "unknown",
                    "confidence": 0.0
                }

        try:
            # Try to use the model if it's initialized
            if self.is_initialized and self.classifier:
                try:
                    # Use the model for classification
                    result = await asyncio.to_thread(self.classifier, text)
                    label_id = result[0]["label"]
                    confidence = result[0]["score"]

                    # Convert label ID to intent name
                    if hasattr(self, 'id2label') and label_id in self.id2label:
                        intent = self.id2label[int(label_id) if isinstance(label_id, str) else label_id]
                    else:
                        intent = label_id

                    logger.info(f"Model classified '{text}' as '{intent}' with confidence {confidence}")
                except Exception as e:
                    logger.warning(f"Model classification failed: {str(e)}, falling back to keywords")
                    intent, confidence = await self._keyword_based_classification(text)
            else:
                # Fall back to keyword-based approach
                logger.info(f"Using keyword classification for '{text}'")
                intent, confidence = await self._keyword_based_classification(text)

            return {
                "success": True,
                "intent": intent,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Failed to classify intent: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to classify intent: {str(e)}",
                "intent": "unknown",
                "confidence": 0.0
            }

    async def _keyword_based_classification(self, text: str) -> tuple:
        """
        Simple keyword-based intent classification

        Args:
            text: Text to classify

        Returns:
            Tuple of (intent, confidence)
        """
        # Simple keyword-based classification for now
        lower_text = text.lower()

        # Command intents
        if any(word in lower_text for word in ["time", "what time", "current time", "clock"]):
            return "time", 0.9
        elif any(word in lower_text for word in ["remind", "reminder", "remember to", "don't forget"]):
            return "reminder", 0.9
        elif any(word in lower_text for word in ["goal", "objective", "target", "aim"]):
            return "goal", 0.9
        elif any(word in lower_text for word in ["use model", "with model", "ask model", "using model"]):
            return "model", 0.9
        elif any(word in lower_text for word in ["memory", "remember", "recall", "forget"]):
            return "memory", 0.9
        elif any(word in lower_text for word in ["personality", "trait", "character", "mood"]):
            return "personality", 0.9
        elif any(word in lower_text for word in ["cli", "interface", "ui", "launch"]):
            return "cli_ui", 0.9
        elif any(word in lower_text for word in ["ollama", "offline", "local", "toggle"]):
            return "ollama", 0.9

        # Coding and technical tasks
        if any(word in lower_text for word in ["code", "function", "class", "method", "implement", "programming"]):
            return "code", 0.8
        elif any(word in lower_text for word in ["bug", "error", "debug", "fix code", "issue", "not working"]):
            return "debug", 0.8
        elif any(word in lower_text for word in ["algorithm", "complexity", "optimize", "efficiency", "data structure"]):
            return "algorithm", 0.8

        # Documentation and explanation
        elif any(word in lower_text for word in ["document", "documentation", "comment", "api", "reference"]):
            return "docs", 0.8
        elif any(word in lower_text for word in ["explain", "clarify", "understand", "how does", "why is"]):
            return "explain", 0.8
        elif any(word in lower_text for word in ["summarize", "summary", "brief", "overview", "tldr"]):
            return "summarize", 0.8

        # Problem solving
        elif any(word in lower_text for word in ["troubleshoot", "diagnose", "problem", "not working", "error"]):
            return "troubleshoot", 0.8
        elif any(word in lower_text for word in ["solve", "solution", "resolve", "fix", "help"]):
            return "solve", 0.8

        # Information and research
        elif any(word in lower_text for word in ["trend", "news", "latest", "update", "current"]):
            return "trends", 0.8
        elif any(word in lower_text for word in ["research", "study", "investigate", "analyze", "deep dive"]):
            return "research", 0.8

        # Content creation
        elif any(word in lower_text for word in ["content", "generate", "create", "blog", "article"]):
            return "content", 0.8
        elif any(word in lower_text for word in ["creative", "story", "imagine", "fiction", "narrative"]):
            return "creative", 0.8
        elif any(word in lower_text for word in ["write", "draft", "compose", "author", "text"]):
            return "write", 0.8

        # Technical and specialized
        elif any(word in lower_text for word in ["technical", "complex", "detailed", "in-depth", "advanced"]):
            return "technical", 0.8
        elif any(word in lower_text for word in ["math", "calculation", "equation", "formula", "compute"]):
            return "math", 0.8

        # Brainstorming and ideas
        elif any(word in lower_text for word in ["brainstorm", "ideas", "suggestions", "options", "possibilities"]):
            return "brainstorm", 0.8
        elif any(word in lower_text for word in ["idea", "concept", "innovative", "novel", "new approach"]):
            return "ideas", 0.8

        # Ethics and responsibility
        elif any(word in lower_text for word in ["ethical", "ethics", "bias", "fair", "responsible", "moral"]):
            return "ethics", 0.8

        # Visual reasoning
        elif any(word in lower_text for word in ["image", "visual", "picture", "photo", "ui", "ux", "design", "interface"]):
            return "visual", 0.8

        # Advanced reasoning
        elif any(word in lower_text for word in ["reasoning", "complex", "analyze", "deep analysis", "thorough", "comprehensive"]):
            return "reasoning", 0.8

        # Default to general purpose
        return "general", 0.5

    async def train_model(self, training_data: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Train the intent classifier on custom data

        Args:
            training_data: List of training examples with text and intent

        Returns:
            Training result
        """
        if not self.is_available:
            return {
                "success": False,
                "message": "DistilBERT classifier is not available"
            }

        try:
            # Import the training script
            import importlib.util
            spec = importlib.util.spec_from_file_location("train_distilbert", "scripts/train_distilbert.py")
            train_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(train_module)

            # Run the training
            logger.info("Starting DistilBERT training process")
            success = await asyncio.to_thread(train_module.train_model)

            if success:
                # Reinitialize the model to load the newly trained model
                self.is_initialized = False
                self._try_initialize()

                return {
                    "success": True,
                    "message": "DistilBERT classifier trained successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "DistilBERT classifier training failed"
                }

        except Exception as e:
            logger.error(f"Failed to train DistilBERT classifier: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to train DistilBERT classifier: {str(e)}"
            }
