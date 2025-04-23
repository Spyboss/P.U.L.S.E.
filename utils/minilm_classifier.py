"""
MiniLM-L6 Intent Classifier for General Pulse

This module provides a lightweight, efficient intent classification system
using the all-MiniLM-L6-v2 model, which is optimized for low-spec hardware.
"""

import os
import gc
import numpy as np
import structlog
from typing import Dict, List, Tuple, Any, Optional, Union
from sklearn.metrics.pairwise import cosine_similarity

# Configure logger
logger = structlog.get_logger("minilm_classifier")

class MiniLMClassifier:
    """
    Intent classifier using the all-MiniLM-L6-v2 model from sentence-transformers.
    
    This classifier is optimized for low-spec hardware, with a much smaller memory
    footprint and faster inference times compared to DistilBERT, while maintaining
    similar accuracy for short text classification.
    """
    
    def __init__(self, intents_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the MiniLM classifier.
        
        Args:
            intents_config: Optional dictionary mapping intent names to descriptions
                           If None, default intents will be used
        """
        try:
            # Import here to avoid loading the model until needed
            from sentence_transformers import SentenceTransformer
            
            # Log initialization
            logger.info("Initializing MiniLM classifier")
            
            # Define default intents if not provided
            self.intents = intents_config or {
                # System commands
                "status": "Check system status",
                "help": "Get help with commands",
                "version": "Check version information",
                "exit": "Exit the application",
                
                # Model commands
                "ask_model": "Ask a specific model a question",
                "test_model": "Test a specific model",
                
                # Ollama commands
                "ollama_status": "Check Ollama status",
                "ollama_start": "Start Ollama service",
                "ollama_stop": "Stop Ollama service",
                "ollama_pull": "Pull a model from Ollama",
                
                # Mode commands
                "enable_offline": "Enable offline mode",
                "disable_offline": "Disable offline mode",
                "toggle_debug": "Toggle debug mode",
                
                # Query types
                "code": "Programming-related queries",
                "debug": "Troubleshooting requests",
                "brainstorm": "Creative ideation",
                "document": "Technical explanations",
                "automate": "Task automation",
                "content": "Content creation",
                "trends": "Trend analysis",
                "ethics": "Ethical considerations",
                
                # Tool commands
                "github": "GitHub-related commands",
                "notion": "Notion-related commands",
                "search": "Web search commands",
                
                # General conversation
                "greeting": "Greetings and casual conversation",
                "general": "General queries not matching other intents"
            }
            
            # Load the model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Pre-compute embeddings for all intents
            self.intent_names = list(self.intents.keys())
            self.embeddings = self.model.encode(self.intent_names)
            
            logger.info(f"MiniLM classifier initialized with {len(self.intents)} intents")
            
        except ImportError as e:
            logger.error(f"Failed to initialize MiniLM classifier: {str(e)}")
            logger.error("Please install sentence-transformers: pip install sentence-transformers")
            raise ImportError("sentence-transformers is required for MiniLM classifier") from e
        except Exception as e:
            logger.error(f"Error initializing MiniLM classifier: {str(e)}")
            raise
    
    def classify(self, query: str, threshold: float = 0.65) -> str:
        """
        Classify a query into an intent.
        
        Args:
            query: The query to classify
            threshold: Confidence threshold (0.0 to 1.0)
            
        Returns:
            The predicted intent name
        """
        try:
            # Encode the query
            query_embed = self.model.encode(query)
            
            # Calculate similarities
            similarities = cosine_similarity([query_embed], self.embeddings)[0]
            
            # Get the most similar intent
            max_idx = np.argmax(similarities)
            max_similarity = similarities[max_idx]
            
            # Check if similarity is above threshold
            if max_similarity > threshold:
                intent = self.intent_names[max_idx]
                logger.debug(f"Classified '{query}' as '{intent}' with confidence {max_similarity:.4f}")
                return intent
            else:
                logger.debug(f"No intent matched '{query}' above threshold {threshold} (best: {self.intent_names[max_idx]} at {max_similarity:.4f})")
                return "general"
                
        except Exception as e:
            logger.error(f"Error classifying query: {str(e)}")
            return "general"
    
    def classify_detailed(self, query: str, threshold: float = 0.65, top_k: int = 3) -> Dict[str, Any]:
        """
        Classify a query with detailed information.
        
        Args:
            query: The query to classify
            threshold: Confidence threshold (0.0 to 1.0)
            top_k: Number of top intents to return
            
        Returns:
            Dictionary with classification details
        """
        try:
            # Encode the query
            query_embed = self.model.encode(query)
            
            # Calculate similarities
            similarities = cosine_similarity([query_embed], self.embeddings)[0]
            
            # Get indices of top-k intents
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Get top intents and their scores
            top_intents = [(self.intent_names[i], similarities[i]) for i in top_indices]
            
            # Primary intent
            primary_intent = top_intents[0][0] if top_intents[0][1] > threshold else "general"
            primary_confidence = float(top_intents[0][1])
            
            # Secondary intents (excluding primary)
            secondary_intents = [
                {"intent": intent, "confidence": float(score)}
                for intent, score in top_intents[1:]
                if score > threshold * 0.8  # Lower threshold for secondary intents
            ]
            
            return {
                "intent": primary_intent,
                "confidence": primary_confidence,
                "secondary_intents": secondary_intents,
                "all_scores": {self.intent_names[i]: float(similarities[i]) for i in top_indices}
            }
                
        except Exception as e:
            logger.error(f"Error in detailed classification: {str(e)}")
            return {
                "intent": "general",
                "confidence": 0.0,
                "secondary_intents": [],
                "all_scores": {}
            }
    
    def free_memory(self):
        """
        Free memory used by the model.
        Useful for systems with limited RAM.
        """
        try:
            # Delete the model to free memory
            if hasattr(self, 'model'):
                del self.model
                
            # Force garbage collection
            gc.collect()
            
            logger.info("MiniLM classifier memory freed")
            
        except Exception as e:
            logger.error(f"Error freeing memory: {str(e)}")
    
    def reload_model(self):
        """
        Reload the model if it was previously freed.
        """
        try:
            if not hasattr(self, 'model') or self.model is None:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("MiniLM classifier model reloaded")
        except Exception as e:
            logger.error(f"Error reloading model: {str(e)}")
            raise

# Singleton instance for reuse
_classifier_instance = None

def get_classifier() -> MiniLMClassifier:
    """
    Get a singleton instance of the MiniLM classifier.
    
    Returns:
        MiniLMClassifier instance
    """
    global _classifier_instance
    
    if _classifier_instance is None:
        _classifier_instance = MiniLMClassifier()
        
    return _classifier_instance

def classify_intent(query: str, threshold: float = 0.65) -> str:
    """
    Classify a query into an intent using the singleton classifier.
    
    Args:
        query: The query to classify
        threshold: Confidence threshold (0.0 to 1.0)
        
    Returns:
        The predicted intent name
    """
    classifier = get_classifier()
    return classifier.classify(query, threshold)

def classify_intent_detailed(query: str, threshold: float = 0.65) -> Dict[str, Any]:
    """
    Classify a query with detailed information using the singleton classifier.
    
    Args:
        query: The query to classify
        threshold: Confidence threshold (0.0 to 1.0)
        
    Returns:
        Dictionary with classification details
    """
    classifier = get_classifier()
    return classifier.classify_detailed(query, threshold)

def free_classifier_memory():
    """
    Free memory used by the singleton classifier.
    """
    global _classifier_instance
    
    if _classifier_instance is not None:
        _classifier_instance.free_memory()
        _classifier_instance = None
        
    # Force garbage collection
    gc.collect()
