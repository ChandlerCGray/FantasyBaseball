#!/usr/bin/env python3
"""
Fantasy Baseball Hub - Unified Startup Script
Cross-platform launcher for the Fantasy Baseball application.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_virtual_environment():
    """Check if virtual environment exists and is activated."""
    if not os.path.exists("venv"):
        print("❌ Virtual environment not found.")
        print("Please run setup first:")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # Linux/macOS")
        print("  venv\\Scripts\\activate     # Windows")
        return False
    return True


def check_environment_file():
    """Check and create .env file if needed."""
    if not os.path.exists(".env"):
        print("Warning: .env file not found. Creating from example...")
        if os.path.exists("env.example"):
            import shutil
            shutil.copy("env.example", ".env")
            print("✅ Created .env file from env.example")
            print("📝 Please edit .env with your ESPN credentials")
        else:
            print("❌ env.example not found. Please create .env file manually")
            return False
    return True


def create_output_directory():
    """Create output directory if it doesn't exist."""
    if not os.path.exists("output"):
                    print("Creating output directory...")
        os.makedirs("output", exist_ok=True)


def get_network_url():
    """Get network URL for the application."""
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return f"http://{local_ip}:8501"
    except:
        return None


def main():
    """Main startup function."""
    print("⚾ Starting Fantasy Baseball Hub...")
    
    # Check prerequisites
    if not check_virtual_environment():
        sys.exit(1)
    
    if not check_environment_file():
        sys.exit(1)
    
    create_output_directory()
    
    # Get network URL
    network_url = get_network_url()
    
    print("Launching Fantasy Baseball Hub...")
    print("📍 Local URL: http://localhost:8501")
    if network_url:
        print(f"🌐 Network URL: {network_url}")
    print("")
    print("Press Ctrl+C to stop the application")
    print("")
    
    try:
        # Run the application
        subprocess.run([
            "python3", "app.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\nApp stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error running app: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 