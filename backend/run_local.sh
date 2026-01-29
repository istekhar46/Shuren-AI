#!/bin/bash

# Shuren Backend - Local Development Startup Script
# This script sets up and starts the backend service for local development

set -e  # Exit on error

echo "=========================================="
echo "Shuren Backend - Local Development Setup"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please update it with your configuration."
        echo ""
        echo "Required variables to configure:"
        echo "  - DATABASE_URL"
        echo "  - JWT_SECRET_KEY"
        echo "  - GOOGLE_CLIENT_ID"
        echo "  - GOOGLE_CLIENT_SECRET"
        echo ""
        read -p "Press Enter to continue after updating .env file..."
    else
        echo "❌ Error: .env.example not found!"
        exit 1
    fi
fi

echo "📦 Installing dependencies..."
poetry install --no-root

echo ""
echo "🗄️  Running database migrations..."
poetry run alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Shuren Backend API..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/api/docs"
echo "   ReDoc: http://localhost:8000/api/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the development server with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
