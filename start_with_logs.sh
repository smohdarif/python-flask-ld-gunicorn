#!/bin/bash

echo "=========================================="
echo "Starting Gunicorn with detailed logging"
echo "Watch for:"
echo "  1. Master process initialization"
echo "  2. LaunchDarkly client setup"
echo "  3. Worker pre-fork events"
echo "  4. Worker post-fork events"
echo "  5. postfork() calls"
echo "=========================================="
echo ""

cd /Users/arifshaikh/Documents/GitHub/python-flask-ld-gunicorn
source venv/bin/activate
# NOT using --preload: postfork() causes SIGSEGV crashes on macOS
# Each worker initializes its own LD client (less efficient but stable)
gunicorn --config gunicorn.conf.py app:app 