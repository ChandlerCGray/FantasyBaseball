#!/usr/bin/env python3
"""
Quick launcher for the modular Fantasy Baseball app
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    try:
        # Add src directory to Python path
        src_path = os.path.join(os.path.dirname(__file__), "src")
        env = os.environ.copy()
        env["PYTHONPATH"] = src_path + ":" + env.get("PYTHONPATH", "")
        
        # Run the new modular app on default port (8501)
        subprocess.run([
            "streamlit", "run", "src/main_app.py"
        ], check=True, env=env)
    except KeyboardInterrupt:
        print("\nApp stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error running app: {e}")
        sys.exit(1)