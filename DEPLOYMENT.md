# Complete Deployment Guide - What Runs Where

## 🏛️ Architecture Overview

### Everything Runs on K3s! ✅

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Your K3s Homelab Cluster                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Namespace: default                                              │  │
│  ├────────────────────────────────────────────────────────────────────┤  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  Ollama Pod                                             │  │  │
│  │  ├────────────────────────────────────────────────────────┤  │  │
│  │  │  • Image: ollama/ollama:latest                         │  │  │
│  │  │  • Port: 11434                                         │  │  │
│  │  │  • Model: llama3.2:3b (or your choice)                 │  │  │
│  │  │  • Storage: 20GB PVC (for models)                     │  │  │
│  │  │  • VRAM: 4-6GB                                         │  │  │
│  │  │                                                        │  │  │
│  │  │  Purpose: Local LLM inference for AI summaries         │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │                                                                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│                                   │                                           │
│                                   ▼                                           │
│                                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Namespace: weather-forecast                                     │  │
│  ├────────────────────────────────────────────────────────────────────┤  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  Weather Forecast Pod                                   │  │  │
│  │  ├────────────────────────────────────────────────────────┤  │  │
│  │  │  • Image: weather-forecast:latest                     │  │  │
│  │  │  • Port: 8000                                         │  │  │
│  │  │  • Database: SQLite (1GB PVC)                         │  │  │
│  │  │  • ML Models: Prophet (500MB PVC)                     │  │  │
│  │  │  • Connects to: Ollama pod                            │  │  │
│  │  │                                                        │  │  │
│  │  │  Components:                                            │  │  │
│  │  │  ✓ FastAPI web server                                 │  │  │
│  │  │  ✓ Weather aggregator (free APIs)                     │  │  │
│  │  │  ✓ AI summary generator (via Ollama)                 │  │  │
│  │  │  ✓ Trend analyzer                                     │  │  │
│  │  │  ✓ Anomaly detector                                   │  │  │
│  │  │  ✓ ML predictor (Prophet)                             │  │  │
│  │  │  ✓ Smart home advisor                                 │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │                                                                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│                                   │                                           │
│                                   ▼                                           │
│                                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Ingress (Traefik)                                                │  │
│  ├────────────────────────────────────────────────────────────────────┤  │
│  │  • URL: http://weather.local (or your domain)                   │  │
│  │  • Routes traffic to weather-forecast service                   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
└──────────────────────────────────────────────────────────────────────────────┘
          │                             │                       │
          ▼                             ▼                       ▼
    ┌───────────────┐     ┌───────────────┐   ┌───────────────┐
    │ Home          │     │ N8n           │   │ External      │
    │ Assistant     │     │ Workflows     │   │ Clients       │
    │ (optional)    │     │ (optional)    │   │ (browsers)    │
    └───────────────┘     └───────────────┘   └───────────────┘
```

## 📦 What Gets Deployed

### 1. Ollama (LLM Service)

**Namespace:** `default`  
**Purpose:** Runs local language models for AI summaries

- **Container:** `ollama/ollama:latest`
- **Port:** 11434
- **Storage:** 20GB PVC (stores downloaded models)
- **Model:** llama3.2:3b (or your choice)
- **Resources:** 4-6GB VRAM (or CPU-only)

**What it does:**
- Provides LLM inference API
- Generates natural language weather summaries
- Runs 100% locally (no external API calls)

### 2. Weather Forecast Service

**Namespace:** `weather-forecast`  
**Purpose:** Main application - fetches weather, runs ML, serves API

- **Container:** `weather-forecast:latest` (built from Dockerfile)
- **Port:** 8000
- **Storage:** 
  - 1GB PVC for database
  - 500MB PVC for ML models

**What it does:**
- Fetches weather from multiple free APIs every 10 minutes
- Stores historical data in SQLite
- Analyzes trends and detects anomalies
- Trains ML models (Prophet) on your local data
- Generates AI summaries via Ollama
- Provides REST API and webhook endpoints
- Gives smart home recommendations

### 3. Ingress

**Purpose:** External access to the service

- **URL:** http://weather.local (configurable)
- **Controller:** Traefik (default in K3s)
- **Routes:** All traffic to weather-forecast service

## ✅ What You DON'T Need

**Nothing external required!**

- ❌ No cloud APIs (everything is free APIs or local)
- ❌ No API keys (Ollama is local)
- ❌ No external databases (SQLite in pod)
- ❌ No separate servers (all in K3s)
- ❌ No GPU required (works on CPU, just slower)

## 🚀 One-Command Deployment

### Quick Deploy

```bash
# Clone the repo on your K3s server
git clone https://github.com/candle02/Open-Weather-Model.git
cd Open-Weather-Model

# Edit deploy-all.sh - set your location
nano deploy-all.sh
# Change LATITUDE, LONGITUDE, LOCATION_NAME at the top

# Make it executable
chmod +x deploy-all.sh

# Run it!
./deploy-all.sh
```

**That's it!** Everything deploys automatically:

1. Creates namespaces
2. Deploys Ollama
3. Pulls LLM model (llama3.2:3b)
4. Builds weather forecast image
5. Creates config with your location
6. Deploys weather forecast service
7. Sets up ingress
8. Verifies everything works

### What the Script Does

```
[1/8] Checking prerequisites (kubectl, docker, K3s connection)
[2/8] Deploying Ollama to K3s
[3/8] Pulling LLM model (llama3.2:3b)
[4/8] Building weather forecast Docker image
[5/8] Creating configuration with your location
[6/8] Deploying weather forecast service
[7/8] Setting up ingress
[8/8] Verifying deployment
```

## 🔧 Resource Requirements

### Minimum (works but slow):

- **CPU:** 2 cores
- **RAM:** 6GB
- **Storage:** 25GB
- **VRAM/GPU:** None (CPU-only Ollama)

### Recommended (smooth operation):

- **CPU:** 4 cores
- **RAM:** 8GB
- **Storage:** 30GB
- **VRAM/GPU:** 4-6GB (NVIDIA GPU)

### Ideal (best performance):

- **CPU:** 6+ cores
- **RAM:** 16GB
- **Storage:** 50GB
- **VRAM/GPU:** 8GB+ (NVIDIA GPU)

## 📊 Resource Breakdown

| Component | CPU | RAM | Storage | Notes |
|-----------|-----|-----|---------|-------|
| Ollama | 1-2 cores | 4GB | 20GB PVC | Uses GPU if available |
| Weather Service | 0.5-1 core | 512MB-1GB | 1.5GB PVC | Scales with data |
| K3s Overhead | 0.5 core | 1GB | 5GB | System components |
| **Total** | **2-4 cores** | **6-8GB** | **25-30GB** | |

## 🔌 Network Flow

```
Internet → Free Weather APIs (Weather.gov, Open-Meteo, wttr.in)
    │
    ▼
Weather Forecast Pod fetches data every 10 min
    │
    ├───> Stores in SQLite
    ├───> Analyzes trends
    ├───> Detects anomalies
    ├───> Sends to Ollama for AI summary
    │        │
    │        ▼
    │    Ollama Pod generates summary
    │        │
    │        ▼
    └───> Returns complete forecast via API
             │
             ▼
      Ingress exposes to network
             │
             ├───> Home Assistant polls API
             ├───> N8n triggers webhooks
             └───> You access dashboard
```

## 🔒 Security

**What's exposed:**
- Weather service API (port 8000) via Ingress

**What's NOT exposed:**
- Ollama API (internal cluster only)
- Database (inside pod only)
- Internal cluster communication

**Best practices:**
- Use Network Policies to restrict pod communication
- Add authentication if exposing to internet
- Keep K3s and containers updated

## 💻 Access Methods

### 1. Direct (within cluster)

```bash
# From another pod in K3s
curl http://weather-forecast.weather-forecast.svc.cluster.local:8000/api/current
```

### 2. Port Forward (for testing)

```bash
# Forward to your local machine
kubectl port-forward -n weather-forecast svc/weather-forecast 8000:8000

# Access at http://localhost:8000
```

### 3. Ingress (production)

```bash
# Access via domain
http://weather.local

# Add to /etc/hosts if needed:
echo "YOUR_K3S_IP weather.local" | sudo tee -a /etc/hosts
```

### 4. Home Assistant

```yaml
# In configuration.yaml
sensor:
  - platform: rest
    resource: "http://weather-forecast.weather-forecast.svc.cluster.local:8000/api/current"
```

## 📅 Timeline

**Day 1:** Deploy and verify
- ✓ Weather data fetching works
- ✓ AI summaries generate
- ✓ Dashboard accessible

**Day 3-7:** Initial patterns
- ✓ Trend analysis becomes meaningful
- ✓ Basic anomaly detection works

**Day 14+:** ML ready
- ✓ Prophet predictions available
- ✓ Accuracy tracking starts
- ✓ Full feature set active

## ⚙️ Maintenance

**Daily:** None required (fully automated)

**Weekly:** Check logs if desired
```bash
kubectl logs -n weather-forecast -l app=weather-forecast --tail=100
```

**Monthly:** Review and clean up if needed
```bash
# Check database size
kubectl exec -n weather-forecast deployment/weather-forecast -- \
  ls -lh /data/weather.db
```

**Updates:** Pull latest image and restart
```bash
git pull
./deploy-all.sh  # Re-run to update
```

## 🔄 Backup

**Database:**
```bash
kubectl exec -n weather-forecast deployment/weather-forecast -- \
  cat /data/weather.db > backup-$(date +%Y%m%d).db
```

**ML Models:**
```bash
kubectl exec -n weather-forecast deployment/weather-forecast -- \
  tar czf - /models > models-backup-$(date +%Y%m%d).tar.gz
```

## ❓ FAQ

**Q: Can I run this without K3s?**  
A: Yes! See `LOCAL_DEV.md` for running locally with Python + Ollama.

**Q: Do I need a GPU?**  
A: No, but it helps. Ollama works on CPU (just slower - 2-5 seconds vs <1 second).

**Q: What if I don't have Home Assistant?**  
A: No problem! The dashboard and API work standalone.

**Q: Can I use a different LLM model?**  
A: Yes! Edit `deploy-all.sh` and change `OLLAMA_MODEL`. Try `phi3:mini` for faster/smaller.

**Q: How much does this cost?**  
A: $0 forever! All free APIs and local processing.

**Q: Can I add more weather sources?**  
A: Yes! Edit `app/services/aggregator.py` to add more free APIs.

## 🎉 Summary

**Everything runs on K3s. Nothing else needed.**

Just:
1. Clone repo on your K3s server
2. Edit location in `deploy-all.sh`
3. Run `./deploy-all.sh`
4. Access at `http://weather.local`

Done! 🐶🌦️
