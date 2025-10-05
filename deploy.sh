#!/bin/bash
# Simple deployment script for MongoDB MCP Server

echo "🚀 MongoDB MCP Server Deployment"
echo "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build the image
echo "📦 Building Docker image..."
docker-compose build

# Start the service
echo "🔧 Starting MongoDB MCP Server..."
docker-compose up -d

# Show status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ MongoDB MCP Server is ready!"
echo "📋 View logs: docker-compose logs -f"
echo "🛑 Stop server: docker-compose down"