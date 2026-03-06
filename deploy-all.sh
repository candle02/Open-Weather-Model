#!/bin/bash
# ============================================================================
# Weather Forecast K3s - Complete Deployment Script
# ============================================================================
# This script deploys EVERYTHING you need to K3s in one go:
# - Ollama (local LLM)
# - Weather Forecast service
# - Ingress for external access
#
# Run this on your K3s homelab server!
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - EDIT THESE!
LATITUDE="36.1627"           # Your latitude
LONGITUDE="-86.7816"          # Your longitude
LOCATION_NAME="Nashville, TN"  # Your city
OLLAMA_MODEL="llama3.2:3b"    # LLM model to use
DOMAIN="weather.local"        # Domain/hostname for ingress

# Advanced options (usually don't need to change)
WEATHER_NAMESPACE="weather-forecast"
OLLAMA_NAMESPACE="default"
IMAGE_NAME="weather-forecast:latest"

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════"
echo "  AI Weather Forecast - K3s Deployment"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo ""
echo "This will deploy:"
echo "  ✓ Ollama (local LLM) to ${OLLAMA_NAMESPACE} namespace"
echo "  ✓ Weather Forecast service to ${WEATHER_NAMESPACE} namespace"
echo "  ✓ Ingress at http://${DOMAIN}"
echo ""
echo "Location: ${LOCATION_NAME} (${LATITUDE}, ${LONGITUDE})"
echo "Model: ${OLLAMA_MODEL}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

echo ""
echo -e "${GREEN}[1/8] Checking prerequisites...${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}ERROR: kubectl not found${NC}"
    echo "Please install kubectl first"
    exit 1
fi

# Check if we can connect to K3s
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}ERROR: Cannot connect to Kubernetes cluster${NC}"
    echo "Please ensure K3s is running and KUBECONFIG is set"
    exit 1
fi

echo "✓ kubectl found and cluster accessible"

# Check if docker is available for building image
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}WARNING: docker not found${NC}"
    echo "You'll need to build the image manually or use a pre-built one"
    BUILD_IMAGE=false
else
    echo "✓ docker found"
    BUILD_IMAGE=true
fi

echo ""
echo -e "${GREEN}[2/8] Deploying Ollama...${NC}"

# Deploy Ollama
kubectl apply -f ollama-deployment.yaml

echo "Waiting for Ollama pod to be ready..."
kubectl wait --for=condition=ready pod -l app=ollama -n ${OLLAMA_NAMESPACE} --timeout=300s || {
    echo -e "${YELLOW}WARNING: Ollama pod not ready yet, check with: kubectl get pods -l app=ollama${NC}"
}

echo "✓ Ollama deployed"

echo ""
echo -e "${GREEN}[3/8] Pulling LLM model (${OLLAMA_MODEL})...${NC}"
echo "This may take a few minutes..."

# Pull model - retry if pod isn't ready yet
for i in {1..5}; do
    if kubectl exec -n ${OLLAMA_NAMESPACE} deployment/ollama -- ollama pull ${OLLAMA_MODEL}; then
        echo "✓ Model ${OLLAMA_MODEL} pulled successfully"
        break
    else
        if [ $i -eq 5 ]; then
            echo -e "${YELLOW}WARNING: Could not pull model automatically${NC}"
            echo "You can pull it manually later with:"
            echo "  kubectl exec -n ${OLLAMA_NAMESPACE} deployment/ollama -- ollama pull ${OLLAMA_MODEL}"
        else
            echo "Retrying in 10 seconds..."
            sleep 10
        fi
    fi
done

echo ""
echo -e "${GREEN}[4/8] Building weather forecast image...${NC}"

if [ "$BUILD_IMAGE" = true ]; then
    echo "Building Docker image..."
    docker build -t ${IMAGE_NAME} .
    
    echo "Importing image into K3s..."
    docker save ${IMAGE_NAME} | sudo k3s ctr images import -
    
    echo "✓ Image built and imported"
else
    echo -e "${YELLOW}Skipping image build (docker not available)${NC}"
    echo "Make sure the image ${IMAGE_NAME} is available in your cluster"
fi

echo ""
echo -e "${GREEN}[5/8] Creating configuration...${NC}"

# Update configmap with user's location
cat > /tmp/weather-configmap.yaml <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ${WEATHER_NAMESPACE}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: weather-config
  namespace: ${WEATHER_NAMESPACE}
data:
  LATITUDE: "${LATITUDE}"
  LONGITUDE: "${LONGITUDE}"
  LOCATION_NAME: "${LOCATION_NAME}"
  LLM_PROVIDER: "ollama"
  OLLAMA_BASE_URL: "http://ollama.${OLLAMA_NAMESPACE}.svc.cluster.local:11434"
  OLLAMA_MODEL: "${OLLAMA_MODEL}"
  DATABASE_PATH: "/data/weather.db"
  UPDATE_INTERVAL: "10"
  ML_RETRAIN_INTERVAL: "24"
  HISTORY_RETENTION_DAYS: "365"
  HOST: "0.0.0.0"
  PORT: "8000"
  LOG_LEVEL: "INFO"
EOF

kubectl apply -f /tmp/weather-configmap.yaml
echo "✓ Configuration created"

echo ""
echo -e "${GREEN}[6/8] Deploying weather forecast service...${NC}"

kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

echo "Waiting for weather forecast pod to be ready..."
kubectl wait --for=condition=ready pod -l app=weather-forecast -n ${WEATHER_NAMESPACE} --timeout=180s || {
    echo -e "${YELLOW}WARNING: Weather forecast pod not ready yet${NC}"
}

echo "✓ Weather forecast service deployed"

echo ""
echo -e "${GREEN}[7/8] Setting up ingress...${NC}"

# Update ingress with user's domain
cat > /tmp/weather-ingress.yaml <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: weather-forecast-ingress
  namespace: ${WEATHER_NAMESPACE}
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  rules:
  - host: ${DOMAIN}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: weather-forecast
            port:
              number: 8000
EOF

kubectl apply -f /tmp/weather-ingress.yaml
echo "✓ Ingress configured for http://${DOMAIN}"

echo ""
echo -e "${GREEN}[8/8] Verifying deployment...${NC}"

# Check all pods
echo ""
echo "Pod Status:"
kubectl get pods -l app=ollama -n ${OLLAMA_NAMESPACE}
kubectl get pods -l app=weather-forecast -n ${WEATHER_NAMESPACE}

# Test health endpoint
echo ""
echo "Testing health endpoint..."
sleep 5  # Give it a moment

if kubectl exec -n ${WEATHER_NAMESPACE} deployment/weather-forecast -- curl -s http://localhost:8000/api/health | grep -q "healthy\|degraded"; then
    echo -e "${GREEN}✓ Service is responding!${NC}"
else
    echo -e "${YELLOW}⚠ Service may still be starting up${NC}"
fi

echo ""
echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════"
echo "  🎉 DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo ""
echo "Your AI Weather Forecast is now running on K3s!"
echo ""
echo -e "${GREEN}Access your service:${NC}"
echo "  • URL: http://${DOMAIN}"
echo "  • Or port-forward: kubectl port-forward -n ${WEATHER_NAMESPACE} svc/weather-forecast 8000:8000"
echo "    Then visit: http://localhost:8000"
echo ""
echo -e "${GREEN}Useful endpoints:${NC}"
echo "  • Current weather: http://${DOMAIN}/api/current"
echo "  • Full forecast: http://${DOMAIN}/api/forecast"
echo "  • Health check: http://${DOMAIN}/api/health"
echo "  • Recommendations: http://${DOMAIN}/api/recommendations"
echo ""
echo -e "${GREEN}Management commands:${NC}"
echo "  • View logs: kubectl logs -n ${WEATHER_NAMESPACE} -l app=weather-forecast -f"
echo "  • Check status: kubectl get pods -n ${WEATHER_NAMESPACE}"
echo "  • Restart: kubectl rollout restart deployment/weather-forecast -n ${WEATHER_NAMESPACE}"
echo ""
echo -e "${GREEN}Home Assistant integration:${NC}"
echo "  • Add REST sensor with URL: http://weather-forecast.${WEATHER_NAMESPACE}.svc.cluster.local:8000/api/current"
echo ""
echo -e "${YELLOW}Note:${NC}"
echo "  • It takes 7+ days to collect enough data for trend analysis"
echo "  • ML predictions available after 14+ days"
echo "  • Weather updates every 10 minutes automatically"
echo ""
echo -e "${GREEN}Troubleshooting:${NC}"
echo "  • If domain doesn't resolve, add to /etc/hosts:"
echo "    echo \"YOUR_K3S_IP ${DOMAIN}\" | sudo tee -a /etc/hosts"
echo ""
echo "Enjoy your AI weather station! 🌦️ 🐶"
echo ""
