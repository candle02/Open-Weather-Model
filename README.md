# AI Weather Forecasting Service for K3s

🌦️ **AI-powered weather forecasting dashboard with Home Assistant integration**

Aggregates multiple free weather APIs, applies ML for custom predictions, and provides natural language insights.

## Features

- 🔮 **Multi-source aggregation** - Combines Weather.gov, Open-Meteo, and wttr.in
- 📊 **Trend analysis** - Analyzes historical patterns in your local weather
- 🤖 **AI summaries** - Natural language weather briefings via **Ollama** (local, open-source)
- ⚠️ **Anomaly detection** - Alerts on unusual weather patterns
- 🧠 **Custom ML predictions** - Trains on your local historical data
- 🏠 **Smart home recommendations** - Suggests Home Assistant automations
- 📈 **Interactive dashboard** - Real-time visualization with charts
- 🔌 **HA integration** - REST API sensors for Home Assistant
- 🔄 **N8n ready** - Webhooks for workflow automation
- 🆓 **100% Free** - No API costs, all open-source

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Weather Dashboard                     │
│              (HTMX + Tailwind + Chart.js)               │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
├─────────────────────────────────────────────────────────┤
│  • Weather Aggregator                                    │
│  • Historical Data Tracker (SQLite)                      │
│  • Trend Analysis Engine                                 │
│  • Anomaly Detector                                      │
│  • ML Prediction Engine                                  │
│  • AI Summarizer (LLM)                                   │
│  • Smart Home Advisor                                    │
└─────────────────────────────────────────────────────────┘
           │                    │                 │
           ▼                    ▼                 ▼
    ┌──────────┐       ┌──────────────┐   ┌──────────┐
    │   HA     │       │  N8n         │   │  Free    │
    │ Sensors  │       │  Webhooks    │   │  APIs    │
    └──────────┘       └──────────────┘   └──────────┘
```

## Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Database**: SQLite
- **ML**: scikit-learn, Prophet (time series)
- **AI**: **Ollama** (local LLMs) + Pydantic AI
- **Frontend**: HTMX + Tailwind CSS + Chart.js
- **Container**: Docker
- **Orchestration**: K3s

## Quick Start

### Prerequisites

- K3s cluster (or Docker)
- **Ollama** installed with a small model (see [OLLAMA_SETUP.md](OLLAMA_SETUP.md))
- Location coordinates (lat/lon)

### Configuration

1. **Set up Ollama** (see [OLLAMA_SETUP.md](OLLAMA_SETUP.md)):
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull a model (fits in 4-6GB VRAM)
   ollama pull llama3.2:3b
   ```

2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your details:
   ```env
   LATITUDE=36.1627
   LONGITUDE=-86.7816
   LOCATION_NAME="Nashville, TN"
   
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2:3b
   ```

### Deploy to K3s

```bash
# Build and push image (adjust registry as needed)
docker build -t weather-forecast:latest .

# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n weather-forecast
```

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Home Assistant Integration

### REST Sensors

Add to your `configuration.yaml`:

```yaml
sensor:
  - platform: rest
    name: "Weather AI Current"
    resource: "http://weather-forecast.default.svc.cluster.local:8000/api/current"
    json_attributes:
      - temperature
      - humidity
      - conditions
      - ai_summary
      - recommendations
    value_template: "{{ value_json.temperature }}"
    unit_of_measurement: "°F"
    scan_interval: 300  # 5 minutes

  - platform: rest
    name: "Weather AI Forecast"
    resource: "http://weather-forecast.default.svc.cluster.local:8000/api/forecast"
    json_attributes:
      - hourly
      - daily
      - anomalies
      - trends
    value_template: "{{ value_json.summary }}"
    scan_interval: 600  # 10 minutes
```

### Automation Example

```yaml
automation:
  - alias: "Close windows before rain"
    trigger:
      - platform: state
        entity_id: sensor.weather_ai_forecast
    condition:
      - condition: template
        value_template: "{{ 'rain' in state_attr('sensor.weather_ai_forecast', 'hourly')[0].conditions.lower() }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Rain predicted in 1 hour - close windows!"
```

## N8n Integration

### Webhook Endpoint

`POST /api/webhook/forecast`

Returns current conditions, forecast, AI summary, and recommendations.

### Example N8n Workflow

1. **Schedule Trigger** (every 6 hours)
2. **HTTP Request** to `http://weather-forecast:8000/api/webhook/forecast`
3. **IF Node** - Check for anomalies
4. **Send Notification** if anomalies detected

## API Endpoints

### Public Endpoints

- `GET /` - Dashboard UI
- `GET /api/current` - Current weather conditions + AI insights
- `GET /api/forecast` - Full forecast with trends and predictions
- `GET /api/historical?days=7` - Historical weather data
- `GET /api/trends` - Trend analysis
- `GET /api/anomalies` - Detected anomalies
- `GET /api/recommendations` - Smart home automation suggestions
- `POST /api/webhook/forecast` - N8n webhook endpoint

### Admin Endpoints

- `POST /api/admin/train` - Retrain ML model
- `GET /api/admin/accuracy` - Forecast accuracy metrics
- `GET /api/health` - Health check

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `LATITUDE` | Location latitude | Required |
| `LONGITUDE` | Location longitude | Required |
| `LOCATION_NAME` | Display name for location | Required |
| `LLM_PROVIDER` | LLM provider ("ollama" or "openai") | `ollama` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llama3.2:3b` |
| `OPENAI_API_KEY` | OpenAI API key (if using openai) | None |
| `OPENAI_BASE_URL` | OpenAI-compatible API URL | None |
| `OPENAI_MODEL` | OpenAI model name | `gpt-3.5-turbo` |
| `DATABASE_PATH` | SQLite database path | `/data/weather.db` |
| `UPDATE_INTERVAL` | Weather update interval (minutes) | `10` |
| `HISTORY_RETENTION_DAYS` | Days to keep historical data | `365` |
| `ML_RETRAIN_INTERVAL` | Hours between ML retraining | `24` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Data Sources

### Free APIs Used

1. **Weather.gov (NWS)** - US-only, no API key needed
2. **Open-Meteo** - Global, free tier, no API key
3. **wttr.in** - Global, free, simple format

The service aggregates all sources and uses ensemble methods to improve accuracy.

## ML Components

### AI Summaries (Ollama)

- Runs locally on your hardware
- Models like Llama 3.2, Phi-3, Mistral
- 100% private, no cloud API calls
- See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for setup

### Trend Analysis

- Moving averages (7-day, 30-day)
- Seasonal decomposition
- Year-over-year comparisons

### Anomaly Detection

- Statistical z-score analysis
- Isolation Forest algorithm
- Threshold-based alerts

### Custom Predictions

- Prophet time series forecasting
- Ensemble of source predictions
- Historical accuracy weighting

## Smart Home Recommendations

The AI analyzes upcoming weather and suggests automations:

- "High heat expected - pre-cool home at 2pm"
- "Strong winds forecast - close awnings and umbrellas"
- "Clear skies predicted - good time for solar charging"
- "Freezing temps tonight - protect outdoor plants"

## Development

### Project Structure

```
weather-forecast-k3s/
├── app/
│   ├── main.py              # FastAPI app
│   ├── models.py            # Pydantic models
│   ├── database.py          # SQLite operations
│   ├── services/
│   │   ├── aggregator.py    # Multi-source weather fetching
│   │   ├── ai_summary.py    # LLM-powered summaries
│   │   ├── trends.py        # Trend analysis
│   │   ├── anomaly.py       # Anomaly detection
│   │   ├── ml_predict.py    # Custom ML predictions
│   │   └── recommendations.py  # Smart home suggestions
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       └── dashboard.html
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── secret.yaml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Testing

```bash
# Run tests
pytest tests/

# Test specific service
pytest tests/test_aggregator.py -v
```

## Monitoring

- Health check endpoint: `/api/health`
- Metrics endpoint: `/api/metrics` (Prometheus-compatible)
- Logs: Structured JSON logging

## Troubleshooting

### Weather data not updating

1. Check API connectivity: `curl http://localhost:8000/api/health`
2. Verify coordinates are valid
3. Check logs: `kubectl logs -n weather-forecast <pod-name>`

### ML predictions not available

1. Ensure at least 7 days of historical data collected
2. Manually trigger training: `curl -X POST http://localhost:8000/api/admin/train`

### LLM summaries failing

1. Verify Ollama is running: `curl http://localhost:11434/api/version`
2. Check model is installed: `ollama list`
3. Test model: `ollama run llama3.2:3b "test"`
4. Check logs for connection errors

## License

MIT

## Support

Built with ❤️ by Code Puppy 🐶

Questions? Feedback? Open an issue!
