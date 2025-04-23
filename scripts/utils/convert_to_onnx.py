#!/usr/bin/env python3
"""
ONNX Conversion Script for DistilBERT
Converts the HuggingFace DistilBERT model to ONNX format for optimized inference
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from pathlib import Path
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = "typeform/distilbert-base-uncased-mnli"
ONNX_DIR = Path("models/onnx")
BATCH_SIZE = 1  # Optimized for 4GB RAM

def convert_model():
    """Convert DistilBERT model to ONNX format with memory optimizations"""
    logger.info(f"Starting conversion of {MODEL_NAME} to ONNX format")
    
    # Create output directory
    ONNX_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory at {ONNX_DIR}")
    
    # Load original model
    logger.info("Loading tokenizer and model from HuggingFace")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    
    # Set model to evaluation mode
    model.eval()
    
    # Dummy input for tracing
    logger.info("Creating dummy input for tracing")
    dummy_input = tokenizer(
        "This is a sample input for ONNX conversion", 
        return_tensors="pt",
        padding="max_length",
        max_length=128,
        truncation=True
    )
    
    # Get input names dynamically
    input_names = list(dummy_input.keys())
    logger.info(f"Input names for ONNX model: {input_names}")
    
    # Export to ONNX
    logger.info("Exporting model to ONNX format")
    onnx_path = ONNX_DIR/"distilbert.onnx"
    
    torch.onnx.export(
        model,
        tuple(dummy_input[name] for name in input_names),
        onnx_path,
        opset_version=13,
        input_names=input_names,
        output_names=["logits"],
        dynamic_axes={
            name: {0: "batch_size", 1: "sequence"} for name in input_names
        } | {"logits": {0: "batch_size"}}
    )
    
    # Save tokenizer
    tokenizer_path = ONNX_DIR
    logger.info(f"Saving tokenizer to {tokenizer_path}")
    tokenizer.save_pretrained(tokenizer_path)
    
    # Verify the exported model size
    model_size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    logger.info(f"ONNX model saved to {onnx_path} (Size: {model_size_mb:.2f} MB)")
    
    # Create a simple verification file
    with open(ONNX_DIR / "info.txt", "w") as f:
        f.write(f"Model: {MODEL_NAME}\n")
        f.write(f"Conversion date: {os.path.getctime(onnx_path)}\n")
        f.write(f"Model size: {model_size_mb:.2f} MB\n")
        f.write(f"Input names: {', '.join(input_names)}\n")
        f.write(f"Output names: logits\n")
        f.write(f"Max sequence length: 128\n")
    
    logger.info("Conversion complete!")

if __name__ == "__main__":
    try:
        convert_model()
    except Exception as e:
        logger.error(f"Error during model conversion: {str(e)}", exc_info=True) 