"""
Train DistilBERT for intent classification
This script trains a 4-bit quantized DistilBERT model for intent classification
"""

import os
import pandas as pd
import numpy as np
import torch
import gc
import logging
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
from transformers import EarlyStoppingCallback
from datasets import Dataset
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/distilbert_training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('distilbert_training')

# Ensure directories exist
os.makedirs('models/distilbert', exist_ok=True)
os.makedirs('logs', exist_ok=True)

def check_memory():
    """Check available memory and clean up if needed"""
    available_memory = psutil.virtual_memory().available / (1024 * 1024 * 1024)  # GB
    logger.info(f"Available memory: {available_memory:.2f} GB")
    
    if available_memory < 1.0:
        logger.warning(f"Low memory detected ({available_memory:.2f} GB). Cleaning up...")
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        # Check memory again
        available_memory = psutil.virtual_memory().available / (1024 * 1024 * 1024)
        logger.info(f"Available memory after cleanup: {available_memory:.2f} GB")
        
        if available_memory < 0.5:
            logger.error("Critically low memory. Cannot proceed with training.")
            return False
    
    return True

def train_model():
    """Train the DistilBERT model for intent classification"""
    
    # Check memory before starting
    if not check_memory():
        return False
    
    try:
        # Load data
        logger.info("Loading training data...")
        df = pd.read_csv('data/intent_training_data.csv')
        
        # Log data statistics
        logger.info(f"Loaded {len(df)} examples with {df['label'].nunique()} unique labels")
        logger.info(f"Label distribution: {df['label'].value_counts().to_dict()}")
        
        # Map labels to integers
        label_map = {label: i for i, label in enumerate(df['label'].unique())}
        id2label = {i: label for label, i in label_map.items()}
        df['label_id'] = df['label'].map(label_map)
        
        # Save label mapping
        with open('models/distilbert/label_map.json', 'w') as f:
            json.dump({"label_map": label_map, "id2label": id2label}, f)
        
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
        logger.info("Tokenizing datasets...")
        train_dataset = train_dataset.map(tokenize_function, batched=True)
        eval_dataset = eval_dataset.map(tokenize_function, batched=True)
        
        # Check memory before loading model
        if not check_memory():
            return False
        
        # Load model with 4-bit quantization if bitsandbytes is available
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
            
            model = DistilBertForSequenceClassification.from_pretrained(
                'distilbert-base-uncased',
                num_labels=len(label_map),
                id2label=id2label,
                label2id=label_map,
                quantization_config=bnb_config
            )
        except ImportError:
            logger.warning("bitsandbytes not available, using standard model")
            model = DistilBertForSequenceClassification.from_pretrained(
                'distilbert-base-uncased',
                num_labels=len(label_map),
                id2label=id2label,
                label2id=label_map
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
            fp16=True if torch.cuda.is_available() else False,  # Use mixed precision training if GPU available
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
        logger.info("Starting model training...")
        trainer.train()
        
        # Evaluate model
        logger.info("Evaluating model...")
        eval_results = trainer.evaluate()
        logger.info(f"Evaluation results: {eval_results}")
        
        # Save model
        logger.info("Saving model...")
        model.save_pretrained('models/distilbert/intent_classifier')
        tokenizer.save_pretrained('models/distilbert/intent_classifier')
        
        # Generate detailed evaluation report
        eval_dataset_df = eval_df.copy()
        eval_dataset_df['predictions'] = trainer.predict(eval_dataset).predictions.argmax(axis=1)
        eval_dataset_df['predicted_label'] = eval_dataset_df['predictions'].map(id2label)
        
        report = classification_report(
            eval_dataset_df['label'], 
            eval_dataset_df['predicted_label'],
            output_dict=True
        )
        
        with open('models/distilbert/evaluation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Model training completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during model training: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    train_model()
