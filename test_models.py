"""
Test script to verify that local models can be loaded
"""
import os
import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer

def test_minilm():
    """Test loading the MiniLM model"""
    try:
        # Set environment variables to force CPU
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["USE_TORCH"] = "1"
        
        print("Loading MiniLM model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("MiniLM model loaded successfully!")
        
        # Test encoding a sentence
        sentences = ["This is a test sentence."]
        embeddings = model.encode(sentences)
        print(f"Encoded sentence shape: {embeddings.shape}")
        
        return True
    except Exception as e:
        print(f"Failed to load MiniLM model: {e}")
        return False

if __name__ == "__main__":
    # Check if PyTorch is available
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    # Test loading MiniLM
    success = test_minilm()
    
    if success:
        print("\n✅ All tests passed! Local models can be loaded.")
    else:
        print("\n❌ Tests failed. Local models cannot be loaded.")
