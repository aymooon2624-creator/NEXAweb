#!/bin/bash

# Render build script for NEXAweb application
# This script runs during deployment to prepare the application

set -e  # Exit on any error

echo "🚀 Starting NEXAweb deployment build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories if they don't exist
echo "📁 Creating necessary directories..."
mkdir -p static/uploads
mkdir -p instance

# Set proper permissions for uploads directory
echo "🔒 Setting permissions for uploads directory..."
chmod 755 static/uploads

# Check if MongoDB URI is set
if [ -z "$MONGO_URI" ]; then
    echo "⚠️  WARNING: MONGO_URI environment variable not set"
    echo "   Please ensure MONGO_URI is configured in your Render environment"
else
    echo "✅ MongoDB URI is configured"
fi

# Check if SECRET_KEY is set
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  WARNING: SECRET_KEY environment variable not set"
    echo "   Please ensure SECRET_KEY is configured in your Render environment"
else
    echo "✅ SECRET_KEY is configured"
fi

# Print environment info
echo "📋 Environment Information:"
echo "   Python version: $(python --version)"
echo "   Working directory: $(pwd)"
echo "   PORT: ${PORT:-5000}"
echo "   FLASK_ENV: ${FLASK_ENV:-development}"

echo "✅ Build process completed successfully!"
echo "🎯 Application is ready for deployment"
