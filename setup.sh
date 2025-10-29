#!/bin/bash

# Setup script for Radiology Report Generator Docker

echo "=========================================="
echo "Radiology Report Generator - Setup"
echo "=========================================="
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p credentials output temp_pdfs

echo "✓ Created ./credentials/ directory"
echo "✓ Created ./output/ directory"
echo ""

# Check for Python script
if [ ! -f "radiology_report_generator.py" ]; then
    echo "⚠️  WARNING: radiology_report_generator.py not found!"
    echo "   Please place the Python script in this directory."
    echo ""
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GOOGLE_API_KEY"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check for credentials
echo "Checking for Google Drive API credentials..."
if [ -f "credentials/service-account.json" ]; then
    echo "✓ Found service-account.json"
elif [ -f "credentials/credentials.json" ]; then
    echo "✓ Found credentials.json"
else
    echo "⚠️  No Google Drive credentials found!"
    echo ""
    echo "Please place one of the following in ./credentials/:"
    echo "  • service-account.json (recommended for Docker)"
    echo "  • credentials.json (OAuth 2.0)"
    echo ""
    echo "How to get credentials:"
    echo "  1. Go to: https://console.cloud.google.com/"
    echo "  2. Enable Google Drive API"
    echo "  3. Create credentials (Service Account or OAuth)"
    echo "  4. Download JSON file and place in ./credentials/"
    echo ""
fi

# Check for Docker
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed ($(docker --version))"
else
    echo "✗ Docker is not installed"
    echo "  Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "✓ Docker Compose is installed ($(docker-compose --version))"
elif docker compose version &> /dev/null 2>&1; then
    echo "✓ Docker Compose (plugin) is installed"
else
    echo "✗ Docker Compose is not installed"
    echo "  Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GOOGLE_API_KEY"
echo "2. Place Google Drive credentials in ./credentials/"
echo "3. Run: docker-compose build"
echo "4. Run: docker-compose up"
echo ""
echo "For detailed instructions, see README.md"
echo ""
