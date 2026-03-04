@echo off
REM Push to GitHub - Open Weather Model
REM Repository: https://github.com/candle02/Open-Weather-Model.git

echo ========================================
echo Pushing to GitHub: Open-Weather-Model
echo ========================================
echo.

cd /d %~dp0

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not in PATH yet.
    echo.
    echo Please:
    echo 1. Close this terminal/command prompt
    echo 2. Open a NEW terminal
    echo 3. Run this script again
    echo.
    echo Git was just installed and needs a fresh terminal to work!
    pause
    exit /b 1
)

echo [1/6] Initializing Git repository...
git init

echo [2/6] Adding all files...
git add .

echo [3/6] Creating initial commit...
git commit -m "Initial commit: AI Weather Forecast with Ollama

- Multi-source weather aggregation (Weather.gov, Open-Meteo, wttr.in)
- AI summaries via Ollama (local, open-source LLM)
- Trend analysis and anomaly detection  
- Custom ML predictions with Prophet
- Smart home recommendations for Home Assistant
- K3s/Kubernetes deployment ready
- 100%% free and open source
- No API keys required!"

echo [4/6] Adding GitHub remote...
git remote add origin https://github.com/candle02/Open-Weather-Model.git

echo [5/6] Setting main branch...
git branch -M main

echo [6/6] Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo SUCCESS! 
echo ========================================
echo.
echo Your code is now on GitHub:
echo https://github.com/candle02/Open-Weather-Model
echo.
echo You can access it anytime from any computer!
echo.
pause
