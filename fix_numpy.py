"""
Fix NumPy compatibility issues for General Pulse
"""

import subprocess
import sys

def main():
    """Downgrade NumPy to a compatible version"""
    print("=" * 60)
    print("General Pulse - NumPy Compatibility Fixer")
    print("=" * 60)
    
    print("Downgrading NumPy to a compatible version (1.24.3)...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "numpy==1.24.3", "--force-reinstall"], check=True)
        print("Successfully downgraded NumPy to 1.24.3")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to downgrade NumPy: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
