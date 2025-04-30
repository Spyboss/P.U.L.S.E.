"""
Test script to verify that PyTorch and Transformers can be imported
"""

def test_imports():
    """Test importing PyTorch and Transformers"""
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
    except ImportError as e:
        print(f"Failed to import PyTorch: {e}")
    
    try:
        import transformers
        print(f"Transformers version: {transformers.__version__}")
    except ImportError as e:
        print(f"Failed to import Transformers: {e}")
    
    try:
        import sentence_transformers
        print(f"Sentence-Transformers version: {sentence_transformers.__version__}")
    except ImportError as e:
        print(f"Failed to import Sentence-Transformers: {e}")

if __name__ == "__main__":
    test_imports()
