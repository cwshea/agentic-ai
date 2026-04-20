#!/bin/bash
# Installation script for AI Agent Learning Series

set -e

echo "=========================================="
echo "AI Agent Learning Series - Installation"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✓ Virtual environment already exists"
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

echo "✓ Virtual environment activated"
echo ""

echo "Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Then try running the demos:"
echo "  AGENT_MOCK_REPO=true python demos/module2_demo.py"
echo "  AGENT_MOCK_GCP=true python demos/module1_demo.py"
echo ""
