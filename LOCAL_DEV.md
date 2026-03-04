# Local Development Setup (No K8s Required)

Want to try the weather forecast service without deploying to K8s? Here's how to run it locally!

## Quick Setup

### 1. Install Ollama

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows (WSL2)
wsl
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a Model

```bash
# Recommended: Llama 3.2 3B (fits in 4-6GB VRAM)
ollama pull llama3.2:3b

# Start Ollama server (if not auto-started)
ollama serve
```

### 3. Clone/Setup Project

```bash
cd weather-forecast-k3s

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure

```bash
# Copy example config
cp .env.example .env

# Edit .env with your details
nano .env  # or vim, code, etc.
```

**Minimal .env for local development:**
```env
# Your location (example: Nashville, TN)
LATITUDE=36.1627
LONGITUDE=-86.7816
LOCATION_NAME=Nashville, TN

# Ollama (local)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Database (local)
DATABASE_PATH=./data/weather.db

# Optional: Adjust update frequency
UPDATE_INTERVAL=10
ML_RETRAIN_INTERVAL=24
```

### 5. Create Data Directory

```bash
mkdir -p data models
```

### 6. Run the Service

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Weather Forecast Service started successfully
```

### 7. Test It!

**Open your browser:**
- Dashboard: http://localhost:8000
- Current weather: http://localhost:8000/api/current
- Full forecast: http://localhost:8000/api/forecast
- Health check: http://localhost:8000/api/health

**Or use curl:**
```bash
# Health check
curl http://localhost:8000/api/health | jq

# Current weather with AI summary
curl http://localhost:8000/api/current | jq

# Full forecast
curl http://localhost:8000/api/forecast | jq
```

## What You Should See

### First Startup

```
INFO:     Starting Weather Forecast Service...
INFO:     Database initialized at ./data/weather.db
INFO:     Using Ollama at http://localhost:11434 with model llama3.2:3b
INFO:     Weather Forecast Service started successfully
INFO:     Updating weather data...
INFO:     Weather update complete. Sources: open-meteo, wttr.in
```

### Sample API Response

```json
{
  "location": "Nashville, TN",
  "latitude": 36.1627,
  "longitude": -86.7816,
  "timestamp": "2024-01-15T14:30:00",
  "conditions": {
    "temperature": 72.5,
    "humidity": 65,
    "conditions": "Partly cloudy",
    "wind_speed": 5.2
  },
  "ai_summary": {
    "summary": "Pleasant afternoon with partly cloudy skies at 72°F. Moderate humidity and light winds make for comfortable conditions. Good day for outdoor activities.",
    "key_points": [
      "Temperature: 72.5°F",
      "Partly cloudy skies",
      "Light winds at 5mph"
    ],
    "warnings": []
  },
  "recommendations": [
    {
      "action": "Optimize for solar energy generation",
      "reason": "Clear skies with 30% cloud cover",
      "priority": "low"
    }
  ]
}
```

## Development Workflow

### Auto-Reload Enabled

With `--reload`, FastAPI automatically restarts when you edit code:

```bash
# Edit a file
nano app/services/ai_summary.py

# Save it - server auto-restarts!
INFO:     Detected file change, reloading...
```

### View Logs

```bash
# Server logs show:
# - Weather updates every 10 minutes
# - Anomaly detections
# - AI summary generation
# - API requests
```

### Test Individual Services

```bash
# Python REPL testing
python

>>> from app.services.aggregator import WeatherAggregator
>>> import asyncio
>>> 
>>> agg = WeatherAggregator(36.1627, -86.7816, "Nashville")
>>> conditions, sources = asyncio.run(agg.get_current_conditions())
>>> print(conditions)
>>> print(sources)
```

## Troubleshooting

### "Connection refused" to Ollama

```bash
# Check if Ollama is running
ps aux | grep ollama

# Start it if not running
ollama serve

# Test connection
curl http://localhost:11434/api/version
```

### "No module named 'app'"

```bash
# Make sure you're in the project root
pwd  # Should show .../weather-forecast-k3s

# Activate venv
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Insufficient data for ML predictions"

This is normal! You need:
- 7+ days for trend analysis
- 14+ days for ML predictions

Just let it run and collect data.

### Weather APIs Failing

```bash
# Test APIs manually
curl "https://api.open-meteo.com/v1/forecast?latitude=36.16&longitude=-86.78&current=temperature_2m"

curl "https://wttr.in/36.16,-86.78?format=j1"

# Check if you need a proxy or firewall rules
```

## Advanced: Hot Reloading AI Prompts

Edit the AI system prompt without restarting:

```python
# app/services/ai_summary.py
system_prompt="""
You are a SASSY weather assistant. 😎
Give weather summaries with ATTITUDE.
"""
```

Save → auto-reloads → next API call uses new prompt!

## Development Tips

### 1. Reduce Update Frequency

During development, update less often:

```env
UPDATE_INTERVAL=60  # Every hour instead of 10 min
```

### 2. Use Smaller Model for Speed

Faster iteration during dev:

```bash
ollama pull phi3:mini
```

```env
OLLAMA_MODEL=phi3:mini
```

### 3. Enable Debug Logging

```env
LOG_LEVEL=DEBUG
```

### 4. Skip ML Training Initially

Comment out ML training in `app/main.py`:

```python
# scheduler.add_job(
#     retrain_ml_models,
#     "interval",
#     hours=settings.ml_retrain_interval,
#     id="ml_retrain",
# )
```

## Testing with Different Locations

Quickly test multiple locations:

```bash
# Create multiple .env files
cp .env .env.nashville
cp .env .env.seattle
cp .env .env.miami

# Edit each with different coords

# Run with specific .env
cp .env.seattle .env
uvicorn app.main:app --reload
```

## Integration Testing

### Home Assistant (Local)

Add to your HA `configuration.yaml`:

```yaml
sensor:
  - platform: rest
    name: "Weather AI Local"
    resource: "http://YOUR_COMPUTER_IP:8000/api/current"
    value_template: "{{ value_json.conditions.temperature }}"
    unit_of_measurement: "°F"
```

### N8n (Local)

1. Create HTTP Request node
2. URL: `http://localhost:8000/api/webhook/forecast`
3. Method: POST
4. Test it!

## Going to Production

When ready to deploy to K3s:

```bash
# Build Docker image
./deploy.sh build

# Deploy to K3s
./deploy.sh apply
```

## Performance Monitoring

```bash
# Watch requests in real-time
tail -f *.log

# Monitor database size
ls -lh data/weather.db

# Check memory usage
ps aux | grep uvicorn
```

## Clean Up

```bash
# Stop the server: Ctrl+C

# Remove database to start fresh
rm data/weather.db

# Deactivate venv
deactivate
```

## Next Steps

1. ✅ Get it running locally
2. ✅ Test all API endpoints
3. ✅ Verify AI summaries work
4. ✅ Let it collect 7+ days of data
5. ✅ Build custom dashboard UI
6. ✅ Deploy to K3s when ready

---

**Happy hacking!** 🐶🌦️
