#!/bin/bash
set -e
exec venv/bin/uvicorn src.server.main:app --host 0.0.0.0 --port 8000
