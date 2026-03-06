# AI Weather Forecast for K3s Homelab

🌦️ **Complete weather forecasting system with local AI - 100% self-hosted on K3s!**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![K3s](https://img.shields.io/badge/K3s-Compatible-green)](https://k3s.io/)
[![Ollama](https://img.shields.io/badge/Ollama-Powered-blue)](https://ollama.com/)

## ✨ What Is This?

A **complete AI-powered weather forecasting service** that runs entirely on your K3s homelab cluster. No cloud dependencies, no API costs, no data leaving your network.

**Features:**
- 🔮 Multi-source weather aggregation (Weather.gov, Open-Meteo, wttr.in)
- 🤖 AI summaries via local LLM (Ollama)
- 📊 Trend analysis & anomaly detection
- 🧠 Custom ML predictions (Prophet time series)
- 🏠 Smart Home Assistant recommendations
- 🔄 N8n workflow integration
- 🆓 **100% Free - $0/month forever!**

## 🚀 Quick Deploy (3 minutes)

```bash
# On your K3s server:
git clone https://github.com/candle02/Open-Weather-Model.git
cd Open-Weather-Model

# Edit your location
nano deploy-all.sh  # Set LATITUDE, LONGITUDE, LOCATION_NAME

# Deploy!
chmod +x deploy-all.sh
./deploy-all.sh

# Access at http://weather.local
```

**Done!** Everything deploys automatically to K3s. ✅

## 🏛️ Architecture

**Everything runs on K3s. Nothing external needed.**

```
┌─────────────────────────────┐
│   Your K3s Homelab Cluster   │
├─────────────────────────────┤
│ ┌───────────────────────┐ │
│ │ Ollama (Local LLM)   │ │
│ │ llama3.2:3b          │ │
│ └──────────┬────────────┘ │
│            │              │
│            ▼              │
│ ┌───────────────────────┐ │
│ │ Weather Forecast    │ │
│ │ FastAPI + ML + AI   │ │
│ └──────────┬────────────┘ │
│            │              │
│            ▼              │
│ ┌───────────────────────┐ │
│ │ Ingress (Traefik)   │ │
│ │ weather.local       │ │
│ └───────────────────────┘ │
└─────────────────────────────┘
        │
        ▼
   Home Assistant / N8n
```

**See [DEPLOYMENT.md](DEPLOYMENT.md) for complete architecture details.**

## 📚 Documentation

| File | What's In It |
|------|-------------|
| **[QUICKREF.md](QUICKREF.md)** | 🚀 Quick reference - commands, URLs, troubleshooting |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | 🏛️ What runs where - complete architecture guide |
| **[OLLAMA_SETUP.md](OLLAMA_SETUP.md)** | 🤖 Ollama installation & model selection |
| **[WHY_OLLAMA.md](WHY_OLLAMA.md)** | 💡 Why local LLMs save you $180/year |
| **[LOCAL_DEV.md](LOCAL_DEV.md)** | 💻 Run locally without K3s |
| **[SETUP.md](SETUP.md)** | 🔧 Detailed manual setup (if you don't use deploy-all.sh) |
| **[README.md](README.md)** | 📖 Full project documentation |

## ✅ Requirements

**Minimum:**
- K3s cluster (or any Kubernetes)
- 2 CPU cores, 6GB RAM, 25GB storage
- Internet (for weather APIs only)

**Recommended:**
- 4 CPU cores, 8GB RAM, 30GB storage  
- 4-6GB VRAM (NVIDIA GPU for faster LLM)

**Cost:** $0/month (all free APIs + local processing)

## 💡 What Makes This Special?

### vs Cloud Weather Services
- ✅ **Free forever** (no $9.99/month subscriptions)
- ✅ **100% private** (your data never leaves your network)
- ✅ **No vendor lock-in** (runs on any K8s cluster)
- ✅ **Customizable** (add your own weather sources, tweak AI prompts)

### vs DIY Weather Scripts
- ✅ **AI-powered** (natural language summaries)
- ✅ **Production-ready** (K8s deployment, health checks, monitoring)
- ✅ **ML predictions** (learns from your local weather patterns)
- ✅ **HA integration** (REST sensors, automations)
- ✅ **Anomaly detection** (alerts on unusual weather)

## 🔌 Integrations

### Home Assistant

```yaml
# Add to configuration.yaml
sensor:
  - platform: rest
    name: "AI Weather"
    resource: "http://weather-forecast.weather-forecast.svc.cluster.local:8000/api/current"
    json_attributes:
      - ai_summary
      - recommendations
    value_template: "{{ value_json.conditions.temperature }}"
```

Get AI summaries, smart recommendations, and automatic sensors!

### N8n Workflows

Webhook endpoint: `POST /api/webhook/forecast`

Example workflow:
1. Schedule trigger (every 6 hours)
2. HTTP request to webhook
3. Check for anomalies
4. Send notification if unusual weather detected

## 📊 Example Output

**AI Summary:**
> "Pleasant afternoon with partly cloudy skies at 72°F. Moderate humidity and light winds make for comfortable conditions. Rain likely in 3 hours - consider closing windows."

**Smart Recommendations:**
- ⚠️ "Close windows before rain in 2 hours"
- 🌡️ "Pre-cool home before peak heat at 2pm"
- ☀️ "Clear skies - good for solar charging"

**Anomaly Detection:**
- "Temperature is 15°F higher than usual (3.2 std devs)"
- "Unusual combination of weather conditions detected"

## 🔧 Management

```bash
# Check status
kubectl get pods -n weather-forecast

# View logs
kubectl logs -n weather-forecast -l app=weather-forecast -f

# Restart
kubectl rollout restart deployment/weather-forecast -n weather-forecast

# Update
cd Open-Weather-Model
git pull
./deploy-all.sh
```

## 🔥 API Endpoints

- `GET /api/current` - Current weather + AI summary + recommendations
- `GET /api/forecast` - Full forecast with ML predictions & trends
- `GET /api/trends` - Historical trend analysis
- `GET /api/anomalies` - Detected weather anomalies
- `GET /api/recommendations` - Smart home automation suggestions
- `POST /api/webhook/forecast` - N8n webhook endpoint
- `GET /api/health` - Health check

## 📈 Timeline

- **Day 1:** Basic weather + AI summaries
- **Day 3-7:** Trend analysis becomes useful
- **Day 14+:** ML predictions available (needs historical data)

## 🐛 Troubleshooting

See **[QUICKREF.md](QUICKREF.md)** for common issues and fixes.

**Quick checks:**
```bash
# Service health
curl http://weather.local/api/health

# Check Ollama
kubectl exec deployment/ollama -- ollama list

# View logs
kubectl logs -n weather-forecast -l app=weather-forecast --tail=50
```

## 🚀 Deployment Options

### 1. One-Click K3s Deploy (Recommended)
```bash
./deploy-all.sh  # Everything automated!
```

### 2. Manual K3s Deploy
See [SETUP.md](SETUP.md)

### 3. Local Development
See [LOCAL_DEV.md](LOCAL_DEV.md)

### 4. Docker Compose
```bash
docker-compose up -d  # (compose file coming soon)
```

## 🔒 Security

- All data stays in your K3s cluster
- No external API keys required (Ollama is local)
- Weather APIs don't require authentication
- Add ingress auth if exposing to internet

## 🌟 Contributing

Contributions welcome! Ideas:
- [ ] Add more weather sources
- [ ] Build fancy dashboard UI
- [ ] Create Home Assistant custom component
- [ ] Add Prometheus metrics
- [ ] Support more LLM models
- [ ] Docker Compose deployment

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## ❤️ Built For

- Homelab enthusiasts
- Home automation nerds
- Privacy-conscious folks
- People tired of $9.99/month weather apps
- Anyone who wants AI without cloud dependencies

## 🐶 Credits

Built with Code Puppy on a rainy weekend to prove you don't need expensive cloud services for smart home automation!

**Weather APIs:**
- [Weather.gov](https://weather.gov) (NWS)
- [Open-Meteo](https://open-meteo.com)
- [wttr.in](https://wttr.in)

**Technology:**
- [Ollama](https://ollama.com) - Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com) - Web framework
- [Prophet](https://facebook.github.io/prophet/) - Time series ML
- [K3s](https://k3s.io) - Lightweight Kubernetes

---

**Questions? Issues? Star the repo and open an issue!** ⭐

**Enjoy your AI weather station!** 🌦️🐶
