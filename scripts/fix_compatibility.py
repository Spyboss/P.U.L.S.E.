"""
Fix compatibility issues between PyTorch, Transformers, and Sentence-Transformers
"""

import subprocess
import sys
import platform

def main():
    """Install compatible versions of PyTorch, Transformers, and Sentence-Transformers"""
    print("=" * 60)
    print("General Pulse - Compatibility Fixer")
    print("=" * 60)
    
    print("Installing compatible versions of PyTorch, Transformers, and Sentence-Transformers...")
    
    # Step 1: Uninstall current packages
    print("\nStep 1: Uninstalling current packages...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio", "transformers", "sentence-transformers"], check=False)
        print("Successfully uninstalled packages")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to uninstall packages: {e}")
    
    # Step 2: Install compatible versions
    print("\nStep 2: Installing compatible versions...")
    try:
        # Install PyTorch 1.13.1 (CPU version)
        print("Installing PyTorch 1.13.1 (CPU version)...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "torch==1.13.1", "torchvision==0.14.1", "torchaudio==0.13.1",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ], check=True)
        
        # Install Transformers 4.26.1
        print("Installing Transformers 4.26.1...")
        subprocess.run([sys.executable, "-m", "pip", "install", "transformers==4.26.1"], check=True)
        
        # Install Sentence-Transformers 2.2.2
        print("Installing Sentence-Transformers 2.2.2...")
        subprocess.run([sys.executable, "-m", "pip", "install", "sentence-transformers==2.2.2"], check=True)
        
        print("Successfully installed compatible versions")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install compatible versions: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
