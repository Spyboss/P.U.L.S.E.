"""
Script to install spaCy and download the required language model
"""

import subprocess
import sys
import os

def install_spacy():
    """Install spaCy and download the required language model"""
    print("Installing spaCy...")
    
    # Install spaCy
    subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"])
    
    # Download the English language model
    print("Downloading English language model...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    
    print("spaCy installation complete!")

if __name__ == "__main__":
    install_spacy()
