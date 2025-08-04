#!/usr/bin/env python3
"""
Quick launcher for the modular Fantasy Baseball app
"""
import subprocess
import sys

if __name__ == "__main__":
    try:
        # Run the new modular app on default port (8501)
        subprocess.run([
            "streamlit", "run", "src/main_app.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\nApp stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error running app: {e}")
        sys.exit(1)