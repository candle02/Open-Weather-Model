#!/bin/bash
# Git setup script for Weather Forecast K3s
# Run this to initialize Git and prepare for GitHub

set -e

echo "========================================"
echo "Weather Forecast K3s - GitHub Setup"
echo "========================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed or not in PATH"
    echo "Please install git and try again:"
    echo "  - Linux: sudo apt install git"
    echo "  - macOS: brew install git"
    echo "  - Windows: Download from https://git-scm.com/"
    exit 1
fi

# Initialize Git repo
echo "[1/5] Initializing Git repository..."
git init

# Add all files
echo "[2/5] Adding files to Git..."
git add .

# Create initial commit
echo "[3/5] Creating initial commit..."
git commit -m "Initial commit: AI Weather Forecast with Ollama support

- Multi-source weather aggregation (Weather.gov, Open-Meteo, wttr.in)
- AI summaries via Ollama (local LLM)
- Trend analysis and anomaly detection
- Custom ML predictions with Prophet
- Smart home recommendations for Home Assistant
- K3s/Kubernetes deployment ready
- 100% free and open source"

echo ""
echo "[4/5] Repository initialized!"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. Go to https://github.com/new"
echo "2. Create a new repository (name it whatever you want)"
echo "3. DO NOT initialize with README (we already have one)"
echo ""
echo "4. Run these commands:"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "Replace YOUR_USERNAME and YOUR_REPO_NAME with your GitHub info!"
echo ""
echo "========================================"
echo ""
