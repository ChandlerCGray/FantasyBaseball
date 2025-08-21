#!/bin/bash

# Fantasy Baseball Server Startup Script
# This script ensures proper environment setup for the FastAPI server

set -e

# Set the project directory
PROJECT_DIR="/home/chandlergray/FantasyBaseball"
cd "$PROJECT_DIR"

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Set Python path
export PYTHONPATH="$PROJECT_DIR/src:$PYTHONPATH"

# Start the server
exec python -m uvicorn src.server.main:app --host 0.0.0.0 --port 8000
