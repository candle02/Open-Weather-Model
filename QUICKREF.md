# 🚀 Quick Reference - AI Weather Forecast

## One-Liner Deploy

```bash
git clone https://github.com/candle02/Open-Weather-Model.git && cd Open-Weather-Model && nano deploy-all.sh && chmod +x deploy-all.sh && ./deploy-all.sh
```

## What Runs Where?

| Component | Where | Purpose | Resources |
|-----------|-------|---------|----------|
| **Ollama** | K3s (`default` namespace) | Local LLM for AI summaries | 4GB RAM, 20GB storage |
| **Weather Service** | K3s (`weather-forecast` namespace) | Main app + API | 1GB RAM, 2GB storage |
| **Ingress** | K3s (Traefik) | External access | Minimal |

**Everything runs on K3s. Nothing external needed!** ✅

## Access Points

```bash
# Dashboard
http://weather.local

# API Endpoints
http://weather.local/api/current        # Current weather + AI summary
http://weather.local/api/forecast       # Full forecast with ML
http://weather.local/api/health         # Health check
http://weather.local/api/recommendations # Smart home suggestions
```

## Essential Commands

### Check Status
```bash
kubectl get pods -n weather-forecast
kubectl get pods -l app=ollama
```

### View Logs
```bash
kubectl logs -n weather-forecast -l app=weather-forecast -f
kubectl logs -l app=ollama -f
```

### Restart
```bash
kubectl rollout restart deployment/weather-forecast -n weather-forecast
kubectl rollout restart deployment/ollama
```

### Port Forward (Testing)
```bash
kubectl port-forward -n weather-forecast svc/weather-forecast 8000:8000
# Then: http://localhost:8000
```

### Test API
```bash
curl http://weather.local/api/health | jq
curl http://weather.local/api/current | jq
```

## Home Assistant Integration

```yaml
# configuration.yaml
sensor:
  - platform: rest
    name: "AI Weather"
    resource: "http://weather-forecast.weather-forecast.svc.cluster.local:8000/api/current"
    value_template: "{{ value_json.conditions.temperature }}"
    json_attributes:
      - ai_summary
      - recommendations
    scan_interval: 300
```

## Troubleshooting

### Pod won't start
```bash
kubectl describe pod -n weather-forecast -l app=weather-forecast
kubectl get events -n weather-forecast
```

### Can't connect to Ollama
```bash
# Test from weather pod
kubectl exec -n weather-forecast deployment/weather-forecast -- \
  curl http://ollama.default.svc.cluster.local:11434/api/version
```

### No weather data
```bash
# Check logs for API errors
kubectl logs -n weather-forecast -l app=weather-forecast | grep ERROR
```

### Redeploy everything
```bash
cd Open-Weather-Model
git pull
./deploy-all.sh
```

## File Locations

| File | Purpose |
|------|----------|
| `deploy-all.sh` | 🚀 One-click deployment script |
| `DEPLOYMENT.md` | 🏛️ Complete architecture guide |
| `OLLAMA_SETUP.md` | 🤖 Ollama installation guide |
| `LOCAL_DEV.md` | 💻 Run locally without K3s |
| `WHY_OLLAMA.md` | 💡 Why use local LLMs |
| `SETUP.md` | 🔧 Detailed setup instructions |

## Configuration

Edit `deploy-all.sh` before deploying:

```bash
LATITUDE="36.1627"              # Your latitude
LONGITUDE="-86.7816"             # Your longitude
LOCATION_NAME="Nashville, TN"    # Your city
OLLAMA_MODEL="llama3.2:3b"       # LLM model
DOMAIN="weather.local"           # Your domain
```

## Resource Usage

| Metric | Value |
|--------|-------|
| **Total CPU** | 2-4 cores |
| **Total RAM** | 6-8GB |
| **Total Storage** | 25-30GB |
| **VRAM** | 4-6GB (optional, CPU works too) |
| **Network** | Minimal (only weather API calls) |
| **Cost** | **$0 forever!** 🎉 |

## Timeline

- **Day 1:** Weather data + AI summaries work
- **Day 3-7:** Trend analysis becomes useful
- **Day 14+:** ML predictions available

## Update Frequency

- **Weather fetch:** Every 10 minutes
- **ML retrain:** Every 24 hours
- **Data retention:** 365 days

## URLs

- **GitHub:** https://github.com/candle02/Open-Weather-Model
- **Ollama:** https://ollama.com
- **Weather.gov:** https://weather.gov
- **Open-Meteo:** https://open-meteo.com

## Support

Check these docs:
1. `DEPLOYMENT.md` - Architecture & what runs where
2. `TROUBLESHOOTING.md` - Common issues
3. `SETUP.md` - Detailed setup

---

**Built with ❤️ for homelabs! 🐶🌦️**
