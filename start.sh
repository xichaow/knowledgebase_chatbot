#!/bin/bash

# Start script for Render deployment
echo "🚀 Starting APRA Information Chatbot..."

# Ensure Python version is correct
python --version

# Install dependencies if not already installed
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set default port if not provided by Render
export PORT=${PORT:-8000}

# Start the application
echo "🌐 Starting Chainlit app on port $PORT..."
chainlit run app.py --host 0.0.0.0 --port $PORT