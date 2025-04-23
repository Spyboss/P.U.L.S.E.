"""
Check if DistilBERT training is viable and prepare for training
"""

import os
import sys
import csv
import json
import logging
import psutil
import sqlite3
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/distilbert_prep.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('distilbert_prep')

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('docs/development', exist_ok=True)

def check_system_resources():
    """
    Check if the system has enough resources for DistilBERT
    
    Returns:
        dict: System resource information
    """
    # Get memory information
    memory = psutil.virtual_memory()
    
    # Convert to GB for readability
    total_memory_gb = memory.total / (1024 ** 3)
    available_memory_gb = memory.available / (1024 ** 3)
    
    # Check if we have enough memory (need at least 2.5GB free)
    has_enough_memory = available_memory_gb >= 2.5
    
    # Get CPU information
    cpu_count = psutil.cpu_count(logical=False)  # Physical cores
    cpu_logical_count = psutil.cpu_count(logical=True)  # Logical cores
    
    # Check if we have enough CPU power (at least 2 cores recommended)
    has_enough_cpu = cpu_count >= 2
    
    # Get disk information
    disk = psutil.disk_usage('/')
    free_disk_gb = disk.free / (1024 ** 3)
    
    # Check if we have enough disk space (at least 1GB free)
    has_enough_disk = free_disk_gb >= 1
    
    # Overall viability
    is_viable = has_enough_memory and has_enough_cpu and has_enough_disk
    
    return {
        "memory": {
            "total_gb": round(total_memory_gb, 2),
            "available_gb": round(available_memory_gb, 2),
            "sufficient": has_enough_memory
        },
        "cpu": {
            "physical_cores": cpu_count,
            "logical_cores": cpu_logical_count,
            "sufficient": has_enough_cpu
        },
        "disk": {
            "free_gb": round(free_disk_gb, 2),
            "sufficient": has_enough_disk
        },
        "is_viable": is_viable
    }

def count_training_examples():
    """
    Count the number of training examples available
    
    Returns:
        dict: Training data information
    """
    # Check database
    db_count = 0
    try:
        if os.path.exists('memory/tasks.db'):
            conn = sqlite3.connect('memory/tasks.db')
            cursor = conn.cursor()
            
            # Count tasks
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_type='conversation'")
            db_count = cursor.fetchone()[0]
            
            conn.close()
    except Exception as e:
        logger.error(f"Error counting database examples: {e}")
    
    # Check CSV file
    csv_count = 0
    try:
        if os.path.exists('data/labeled_data.csv'):
            with open('data/labeled_data.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                csv_count = sum(1 for _ in reader)
    except Exception as e:
        logger.error(f"Error counting CSV examples: {e}")
    
    # Total examples
    total_count = db_count + csv_count
    
    # Check if we have enough examples (at least 200 recommended)
    has_enough_data = total_count >= 200
    
    return {
        "database_examples": db_count,
        "csv_examples": csv_count,
        "total_examples": total_count,
        "sufficient": has_enough_data
    }

def generate_training_script():
    """
    Generate a training script for DistilBERT
    
    Returns:
        str: Path to the generated script
    """
    script_content = """
# DistilBERT Intent Classifier Training Script
# This script trains a 4-bit quantized DistilBERT model for intent classification

import os
import pandas as pd
import numpy as np
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
from transformers import EarlyStoppingCallback
from datasets import Dataset
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/distilbert_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('distilbert_training')

# Ensure directories exist
os.makedirs('models/distilbert', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Load data
df = pd.read_csv('data/labeled_data.csv')

# Map labels to integers
label_map = {label: i for i, label in enumerate(df['label'].unique())}
id2label = {i: label for label, i in label_map.items()}
df['label_id'] = df['label'].map(label_map)

# Split data
train_df, eval_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])

# Convert to datasets
train_dataset = Dataset.from_pandas(train_df)
eval_dataset = Dataset.from_pandas(eval_df)

# Load tokenizer
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

# Tokenize function
def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True, max_length=128)

# Tokenize datasets
train_dataset = train_dataset.map(tokenize_function, batched=True)
eval_dataset = eval_dataset.map(tokenize_function, batched=True)

# Load model with 4-bit quantization
from bitsandbytes.nn import Linear4bit
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

model = DistilBertForSequenceClassification.from_pretrained(
    'distilbert-base-uncased',
    num_labels=len(label_map),
    id2label=id2label,
    label2id=label_map,
    quantization_config=bnb_config
)

# Training arguments
training_args = TrainingArguments(
    output_dir='models/distilbert/checkpoints',
    evaluation_strategy='epoch',
    save_strategy='epoch',
    learning_rate=5e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model='accuracy',
    push_to_hub=False,
    fp16=True,  # Use mixed precision training
)

# Define compute metrics function
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    
    # Calculate accuracy
    accuracy = (predictions == labels).mean()
    
    return {'accuracy': accuracy}

# Initialize Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)

# Train model
trainer.train()

# Evaluate model
eval_results = trainer.evaluate()
logger.info(f"Evaluation results: {eval_results}")

# Save model
model.save_pretrained('models/distilbert/intent_classifier')
tokenizer.save_pretrained('models/distilbert/intent_classifier')

# Save label mapping
import json
with open('models/distilbert/intent_classifier/label_map.json', 'w') as f:
    json.dump(label_map, f)

# Generate classification report
eval_pred = trainer.predict(eval_dataset)
y_pred = np.argmax(eval_pred.predictions, axis=1)
y_true = eval_pred.label_ids

report = classification_report(y_true, y_pred, target_names=list(label_map.keys()), output_dict=True)
logger.info(f"Classification report:\\n{classification_report(y_true, y_pred, target_names=list(label_map.keys()))}")

# Save report
with open('models/distilbert/intent_classifier/classification_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print("Training complete! Model saved to models/distilbert/intent_classifier")
"""
    
    # Save the script
    script_path = 'scripts/train_distilbert.py'
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    logger.info(f"Training script generated at {script_path}")
    return script_path

def generate_documentation():
    """
    Generate documentation for DistilBERT implementation
    
    Returns:
        str: Path to the generated documentation
    """
    doc_content = """
# DistilBERT Intent Classification Plan

## Overview

This document outlines the plan for implementing a DistilBERT-based intent classification system for General Pulse. The current keyword-based system works well for basic intent classification, but a machine learning approach can provide better accuracy and handle more complex queries.

## Requirements

### System Requirements

- **Memory**: At least 2.5GB of free RAM
- **CPU**: At least 2 cores recommended
- **Disk**: At least 1GB of free disk space
- **Python**: 3.9+ with PyTorch, Transformers, and BitsAndBytes libraries

### Data Requirements

- At least 200 labeled examples for training
- Balanced distribution across intent classes
- High-quality, diverse examples

## Implementation Plan

### Phase 1: Data Collection and Preparation

1. **Collect Data**:
   - Extract user queries from tasks.db
   - Generate synthetic examples
   - Label data with intents

2. **Prepare Dataset**:
   - Split into training and evaluation sets
   - Balance classes if necessary
   - Preprocess text (tokenization, etc.)

### Phase 2: Model Training

1. **Train DistilBERT Model**:
   - Use 4-bit quantization for memory efficiency
   - Fine-tune on intent classification task
   - Implement early stopping to prevent overfitting
   - Save best model based on validation accuracy

2. **Evaluate Model**:
   - Calculate accuracy, precision, recall, and F1 score
   - Generate confusion matrix
   - Identify problematic intent classes

### Phase 3: Integration

1. **Create Model Interface**:
   - Implement `DistilBERTIntentHandler` class
   - Add fallback to keyword-based classification
   - Optimize for inference speed

2. **Memory Management**:
   - Implement lazy loading of the model
   - Add memory usage monitoring
   - Implement model unloading when not in use

### Phase 4: Deployment

1. **Package Model**:
   - Export model in ONNX format for faster inference
   - Create model metadata file
   - Document model capabilities and limitations

2. **Update Documentation**:
   - Add usage instructions
   - Document performance metrics
   - Provide examples of supported queries

## Hybrid Approach

Until the DistilBERT model is fully trained and validated, we'll use a hybrid approach:

1. **Primary Classification**: Use the keyword-based classifier for all queries
2. **Data Collection**: Store all queries and classifications for future training
3. **Gradual Transition**: Once the DistilBERT model reaches sufficient accuracy (>90%), gradually transition to using it as the primary classifier

## Monitoring and Improvement

1. **Track Performance**:
   - Log classification accuracy
   - Monitor memory usage
   - Track inference time

2. **Continuous Improvement**:
   - Periodically retrain with new data
   - Adjust model parameters based on performance
   - Add support for new intents as needed

## Fallback Strategy

If the DistilBERT model fails (due to memory constraints or other issues):

1. Automatically fall back to the keyword-based classifier
2. Log the failure for analysis
3. Notify the user if appropriate

## Timeline

1. **Data Collection**: 1-2 weeks
2. **Model Training**: 1 week
3. **Integration**: 1 week
4. **Testing and Refinement**: 1-2 weeks

Total estimated time: 4-6 weeks

## Conclusion

The DistilBERT-based intent classification system will provide improved accuracy and flexibility compared to the current keyword-based approach. By using quantization and efficient memory management, we can make this work even on systems with limited resources.
"""
    
    # Save the documentation
    doc_path = 'docs/development/distilbert_plan.md'
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    logger.info(f"Documentation generated at {doc_path}")
    return doc_path

def main():
    """Main function"""
    logger.info("Starting DistilBERT preparation check")
    
    # Check system resources
    logger.info("Checking system resources...")
    resources = check_system_resources()
    
    # Count training examples
    logger.info("Counting training examples...")
    training_data = count_training_examples()
    
    # Determine if DistilBERT is viable
    is_viable = resources["is_viable"] and training_data["sufficient"]
    
    # Print summary
    print("\n" + "="*50)
    print("DISTILBERT VIABILITY CHECK")
    print("="*50)
    
    print("\nSystem Resources:")
    print(f"  Memory: {resources['memory']['available_gb']:.2f}GB available of {resources['memory']['total_gb']:.2f}GB total")
    print(f"  CPU: {resources['cpu']['physical_cores']} physical cores, {resources['cpu']['logical_cores']} logical cores")
    print(f"  Disk: {resources['disk']['free_gb']:.2f}GB free space")
    
    print("\nTraining Data:")
    print(f"  Database examples: {training_data['database_examples']}")
    print(f"  CSV examples: {training_data['csv_examples']}")
    print(f"  Total examples: {training_data['total_examples']}")
    
    print("\nViability:")
    print(f"  System resources: {'✓' if resources['is_viable'] else '✗'}")
    print(f"  Training data: {'✓' if training_data['sufficient'] else '✗'}")
    print(f"  Overall: {'✓ VIABLE' if is_viable else '✗ NOT VIABLE'}")
    
    # Generate training script if viable
    if is_viable:
        print("\nGenerating training script and documentation...")
        script_path = generate_training_script()
        doc_path = generate_documentation()
        
        print(f"\nTraining script generated at: {script_path}")
        print(f"Documentation generated at: {doc_path}")
        
        print("\nNext steps:")
        print("1. Install required packages: pip install torch transformers datasets bitsandbytes")
        print("2. Run the training script: python scripts/train_distilbert.py")
        print("3. Review the documentation for integration details")
    else:
        print("\nDistilBERT training is not viable at this time.")
        print("Recommendations:")
        
        if not resources["memory"]["sufficient"]:
            print("- Free up at least 2.5GB of memory or upgrade your system")
        
        if not training_data["sufficient"]:
            print(f"- Collect more training data (need {200 - training_data['total_examples']} more examples)")
            print("- Run scripts/extract_training_data.py to generate more examples")
        
        print("\nContinue using the keyword-based classifier for now.")
        
        # Generate documentation anyway
        doc_path = generate_documentation()
        print(f"\nDocumentation generated at: {doc_path}")
    
    # Save results
    results = {
        "timestamp": import datetime; datetime.datetime.now().isoformat(),
        "resources": resources,
        "training_data": training_data,
        "is_viable": is_viable
    }
    
    try:
        with open('logs/distilbert_viability.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved to logs/distilbert_viability.json")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    logger.info("DistilBERT preparation check complete")

if __name__ == "__main__":
    main()
