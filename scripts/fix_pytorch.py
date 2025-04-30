"""
Fix PyTorch and Transformers compatibility issues for General Pulse
"""

import os
import sys
import subprocess
import platform
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    print(f"Python version: {platform.python_version()}")
    major, minor, _ = platform.python_version_tuple()
    if int(major) != 3 or int(minor) < 8:
        print("WARNING: Python 3.8 or higher is recommended for PyTorch and Transformers")
        return False
    return True

def check_pip():
    """Check if pip is available"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        print("ERROR: pip is not available. Please install pip first.")
        return False

def install_package(package_name):
    """Install a package using pip"""
    print(f"Installing {package_name}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
        print(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install {package_name}: {e}")
        return False

def install_pytorch():
    """Install PyTorch CPU version"""
    print("Installing PyTorch (CPU version)...")
    try:
        # Install PyTorch CPU version
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio", 
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ], check=True)
        print("Successfully installed PyTorch (CPU version)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install PyTorch: {e}")
        return False

def install_transformers():
    """Install Transformers"""
    return install_package("transformers")

def install_sentence_transformers():
    """Install Sentence Transformers"""
    return install_package("sentence-transformers")

def install_accelerate():
    """Install Accelerate"""
    return install_package("accelerate")

def test_imports():
    """Test importing PyTorch and Transformers"""
    print("\nTesting imports...")
    
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
    except ImportError as e:
        print(f"Failed to import PyTorch: {e}")
        return False
    
    try:
        import transformers
        print(f"Transformers version: {transformers.__version__}")
    except ImportError as e:
        print(f"Failed to import Transformers: {e}")
        return False
    
    try:
        import sentence_transformers
        print(f"Sentence-Transformers version: {sentence_transformers.__version__}")
    except ImportError as e:
        print(f"Failed to import Sentence-Transformers: {e}")
        return False
    
    return True

def test_minilm():
    """Test loading the MiniLM model"""
    print("\nTesting MiniLM model...")
    try:
        from sentence_transformers import SentenceTransformer
        
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

def main():
    """Main function"""
    print("=" * 60)
    print("General Pulse - PyTorch and Transformers Compatibility Fixer")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        print("WARNING: Continuing with unsupported Python version")
    
    # Check pip
    if not check_pip():
        print("ERROR: pip is required to install packages")
        return False
    
    # Install packages
    success = True
    success = success and install_pytorch()
    success = success and install_transformers()
    success = success and install_sentence_transformers()
    success = success and install_accelerate()
    
    if not success:
        print("\nERROR: Failed to install some packages")
        return False
    
    # Test imports
    if not test_imports():
        print("\nERROR: Failed to import some packages")
        return False
    
    # Test MiniLM model
    if not test_minilm():
        print("\nERROR: Failed to load MiniLM model")
        return False
    
    print("\n" + "=" * 60)
    print("SUCCESS: PyTorch and Transformers are now compatible with General Pulse!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
