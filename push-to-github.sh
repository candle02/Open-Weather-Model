#!/bin/bash
# Push to GitHub - Open Weather Model
# Repository: https://github.com/candle02/Open-Weather-Model.git

set -e

echo "========================================"
echo "Pushing to GitHub: Open-Weather-Model"
echo "========================================"
echo ""

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed"
    echo "Please install git first:"
    echo "  - Ubuntu/Debian: sudo apt install git"
    echo "  - macOS: brew install git"
    exit 1
fi

echo "[1/6] Initializing Git repository..."
git init

echo "[2/6] Adding all files..."
git add .

echo "[3/6] Creating initial commit..."
git commit -m "Initial commit: AI Weather Forecast with Ollama

- Multi-source weather aggregation (Weather.gov, Open-Meteo, wttr.in)
- AI summaries via Ollama (local, open-source LLM)
- Trend analysis and anomaly detection
- Custom ML predictions with Prophet
- Smart home recommendations for Home Assistant
- K3s/Kubernetes deployment ready
- 100% free and open source
- No API keys required!"

echo "[4/6] Adding GitHub remote..."
git remote add origin https://github.com/candle02/Open-Weather-Model.git

echo "[5/6] Setting main branch..."
git branch -M main

echo "[6/6] Pushing to GitHub..."
git push -u origin main

echo ""
echo "========================================"
echo "SUCCESS!"
echo "========================================"
echo ""
echo "Your code is now on GitHub:"
echo "https://github.com/candle02/Open-Weather-Model"
echo ""
echo "You can access it anytime from any computer!"
echo ""
