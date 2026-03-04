**Issue: "Model too slow"**
- Use a smaller/faster model: `ollama pull phi3:mini`
- Update configmap with `OLLAMA_MODEL: phi3:mini`
- Restart deployment: `kubectl rollout restart deployment/weather-forecast -n weather-forecast`
# Setup Guide - AI Weather Forecast for K3s

## Prerequisites

- K3s cluster running (or any Kubernetes cluster)
- Docker installed for building images
- kubectl configured to access your cluster
- **Ollama installed with a model** (see step 1 below)
- Your location coordinates (latitude/longitude)

## Step-by-Step Setup

### 1. Set Up Ollama

**You have two options:**

#### Option A: Ollama on Host (Easiest)

Install Ollama on your host machine:

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model that fits in 4-6GB VRAM
ollama pull llama3.2:3b

# Test it
ollama run llama3.2:3b "test"
```

#### Option B: Ollama in K3s (Recommended)

Deploy Ollama as a service in your cluster:

```bash
# See OLLAMA_SETUP.md for full YAML
kubectl apply -f ollama-deployment.yaml

# Pull model inside the pod
kubectl exec -it deployment/ollama -- ollama pull llama3.2:3b
```

**See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for detailed instructions and model recommendations!**

### 2. Find Your Location Coordinates

You need the latitude and longitude for your location.

**Easy ways to find coordinates:**
- Google Maps: Right-click on your location → Click the coordinates
- https://www.latlong.net/
- Ask an LLM: "What are the coordinates for [your city]?"

### 3. Configure the Application

#### Update ConfigMap (k8s/configmap.yaml)

Edit `k8s/configmap.yaml` and update these values:

```yaml
LATITUDE: "36.1627"          # Your latitude
LONGITUDE: "-86.7816"         # Your longitude  
LOCATION_NAME: "Nashville, TN"  # Your location name

# Ollama configuration
LLM_PROVIDER: "ollama"
OLLAMA_BASE_URL: "http://ollama.default.svc.cluster.local:11434"  # Or http://host.docker.internal:11434
OLLAMA_MODEL: "llama3.2:3b"
```

#### No Secrets Needed! 🎉

If using Ollama (local), you don't need to create any secrets. The `k8s/secret.yaml` is **optional** and only needed if using OpenAI-compatible APIs.

### 4. Build Docker Image

```bash
# Build the image
./deploy.sh build

# OR manually:
docker build -t weather-forecast:latest .
```

**If using a container registry:**

```bash
# Tag for your registry
docker tag weather-forecast:latest your-registry.com/weather-forecast:latest

# Push to registry
docker push your-registry.com/weather-forecast:latest

# Update k8s/deployment.yaml with your registry path
```

### 5. Deploy to K3s

```bash
# Deploy everything
./deploy.sh apply

# OR manually:
kubectl apply -f k8s/configmap.yaml
# Skip secret if using Ollama
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 6. Verify Deployment

```bash
# Check if pod is running
kubectl get pods -n weather-forecast

# Expected output:
# NAME                               READY   STATUS    RESTARTS   AGE
# weather-forecast-xxxxxxxxxx-xxxxx   1/1     Running   0          30s

# Check logs
kubectl logs -f -n weather-forecast -l app=weather-forecast

# You should see:
# "Weather Forecast Service started successfully"
# "Updating weather data..."
```

### 7. Access the Service

#### Option A: Port Forward (for testing)

```bash
kubectl port-forward -n weather-forecast svc/weather-forecast 8000:8000
```

Then visit:
- Dashboard: http://localhost:8000
- Current weather: http://localhost:8000/api/current
- Full forecast: http://localhost:8000/api/forecast
- Health check: http://localhost:8000/api/health

#### Option B: Ingress (for production)

Uncomment and configure the Ingress section in `k8s/service.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: weather-forecast-ingress
  namespace: weather-forecast
spec:
  rules:
  - host: weather.yourdomain.com  # Your domain
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: weather-forecast
            port:
              number: 8000
```

Then apply:
```bash
kubectl apply -f k8s/service.yaml
```

## Home Assistant Integration

### REST Sensors

Add to your Home Assistant `configuration.yaml`:

```yaml
sensor:
  # Current weather with AI summary
  - platform: rest
    name: "Weather AI Current"
    resource: "http://weather-forecast.weather-forecast.svc.cluster.local:8000/api/current"
    json_attributes:
      - conditions
      - ai_summary
      - recommendations
    value_template: "{{ value_json.conditions.temperature }}"
    unit_of_measurement: "°F"
    scan_interval: 300  # Update every 5 minutes

  # Full forecast
  - platform: rest
    name: "Weather AI Forecast"
    resource: "http://weather-forecast.weather-forecast.svc.cluster.local:8000/api/forecast"
    json_attributes:
      - hourly
      - daily
      - trends
      - anomalies
      - ml_predictions
    value_template: "{{ value_json.ai_summary.summary }}"
    scan_interval: 600  # Update every 10 minutes

  # Recommendations
  - platform: rest
    name: "Weather Recommendations"
    resource: "http://weather-forecast.weather-forecast.svc.cluster.local:8000/api/recommendations"
    value_template: "{{ value_json.recommendations | length }}"
    json_attributes:
      - recommendations
    scan_interval: 600
```

### Example Automation

```yaml
automation:
  # Close windows before rain
  - alias: "Close windows before rain"
    trigger:
      - platform: state
        entity_id: sensor.weather_ai_forecast
    condition:
      - condition: template
        value_template: >-
          {% set hourly = state_attr('sensor.weather_ai_forecast', 'hourly') %}
          {% if hourly and hourly | length > 0 %}
            {{ 'rain' in hourly[0].conditions.conditions.lower() }}
          {% else %}
            false
          {% endif %}
    action:
      - service: notify.mobile_app
        data:
          title: "Rain Alert"
          message: "Rain predicted in 1 hour - close windows!"
          
  # Pre-cool home before heat
  - alias: "Pre-cool before extreme heat"
    trigger:
      - platform: state
        entity_id: sensor.weather_recommendations
    condition:
      - condition: template
        value_template: >-
          {% set recs = state_attr('sensor.weather_recommendations', 'recommendations') %}
          {% if recs %}
            {{ recs | selectattr('action', 'search', 'Pre-cool') | list | length > 0 }}
          {% else %}
            false
          {% endif %}
    action:
      - service: climate.set_temperature
        data:
          entity_id: climate.thermostat
          temperature: 72
      - service: notify.mobile_app
        data:
          message: "Pre-cooling home before heat wave"
```

## N8n Integration

### Webhook Workflow

1. In N8n, create a new workflow
2. Add a **Schedule Trigger** (e.g., every 6 hours)
3. Add an **HTTP Request** node:
   - Method: POST
   - URL: `http://weather-forecast.weather-forecast.svc.cluster.local:8000/api/webhook/forecast`
4. Add an **IF** node to check for anomalies:
   - Condition: `{{ $json.anomalies.length > 0 }}`
5. Add notification actions based on conditions

### Example: Weather Alert Workflow

```
Schedule (every 6h)
  → HTTP Request (/api/webhook/forecast)
    → IF (anomalies detected)
      → TRUE: Send Slack/Email alert
      → FALSE: Do nothing
```

## Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# Current weather
curl http://localhost:8000/api/current | jq

# Full forecast
curl http://localhost:8000/api/forecast | jq

# Trends
curl http://localhost:8000/api/trends | jq

# Anomalies
curl http://localhost:8000/api/anomalies | jq

# Recommendations
curl http://localhost:8000/api/recommendations | jq

# N8n webhook
curl -X POST http://localhost:8000/api/webhook/forecast | jq
```

### Manual ML Training

```bash
# Trigger ML model training (requires 14+ days of data)
curl -X POST http://localhost:8000/api/admin/train
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl get pods -n weather-forecast

# Describe pod for events
kubectl describe pod -n weather-forecast -l app=weather-forecast

# Check logs
kubectl logs -n weather-forecast -l app=weather-forecast
```

### Common Issues

**Issue: "Ollama connection failed"**
- Verify Ollama is running: `curl http://localhost:11434/api/version`
- Check model is downloaded: `ollama list`
- Test connectivity from pod: `kubectl exec -it <pod> -- curl http://ollama:11434/api/version`
- If using host Ollama, ensure K3s can reach host network

**Issue: "Insufficient data for ML predictions"**
- This is normal for the first 7-14 days
- The service needs historical data to train models
- ML predictions will become available after 2 weeks

**Issue: "Weather data not updating"**
- Check pod logs for API errors
- Verify latitude/longitude are correct
- Test weather APIs manually (Open-Meteo, Weather.gov)

**Issue: "Database locked error"**
- SQLite has issues with multiple writers
- Make sure `replicas: 1` in deployment.yaml
- For multiple replicas, switch to PostgreSQL

## Monitoring

### Check Health

```bash
kubectl exec -it -n weather-forecast $(kubectl get pod -n weather-forecast -l app=weather-forecast -o name) -- curl localhost:8000/api/health
```

### View Metrics

```bash
# Last update time
kubectl exec -it -n weather-forecast $(kubectl get pod -n weather-forecast -l app=weather-forecast -o name) -- sh -c '
  curl -s localhost:8000/api/health | grep last_update
'

# Data count
kubectl exec -it -n weather-forecast $(kubectl get pod -n weather-forecast -l app=weather-forecast -o name) -- sh -c '
  curl -s localhost:8000/api/historical?days=1 | grep count
'
```

## Updating

### Update Configuration

```bash
# Edit configmap
kubectl edit configmap weather-config -n weather-forecast

# Restart pod to apply changes
kubectl rollout restart deployment/weather-forecast -n weather-forecast
```

### Update Image

```bash
# Build new image
./deploy.sh build

# Force pod to pull new image
kubectl rollout restart deployment/weather-forecast -n weather-forecast
```

## Cleanup

```bash
# Delete everything
./deploy.sh delete

# OR manually:
kubectl delete namespace weather-forecast
```

## Next Steps

1. **Build the dashboard UI** - Create a proper HTML dashboard with charts
2. **Add more metrics** - Extend to predict humidity, wind, etc.
3. **Integrate with more sources** - Add additional weather APIs
4. **Export to Prometheus** - Add metrics endpoint for monitoring
5. **Create HA custom component** - Build a proper Home Assistant integration

## Support

If you run into issues:
1. Check the logs: `kubectl logs -f -n weather-forecast -l app=weather-forecast`
2. Verify health: `curl http://localhost:8000/api/health`
3. Review Walmart-specific network requirements (VPN/Eagle WiFi)

Built with ❤️ by Code Puppy 🐶
