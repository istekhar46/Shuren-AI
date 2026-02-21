#!/bin/bash
# LiveKit Voice Agent Worker Startup Script for Linux/Mac
# This script starts the voice agent worker in development mode with hot-reload

echo "========================================"
echo "Starting LiveKit Voice Agent Worker"
echo "========================================"
echo ""

# Check if we're in the correct directory
if [ ! -f "app/livekit_agents/voice_agent_worker.py" ]; then
    echo "ERROR: Must run from backend directory"
    echo "Current directory: $(pwd)"
    echo "Please run: cd backend"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found"
    echo "Please create .env file with LiveKit credentials"
    echo "See .env.example for reference"
    exit 1
fi

echo "Starting worker in development mode..."
echo "Press Ctrl+C to stop the worker"
echo ""

poetry run python app/livekit_agents/voice_agent_worker.py dev
