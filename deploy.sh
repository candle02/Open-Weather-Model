#!/bin/bash

# Deploy Weather Forecast to K3s
# Usage: ./deploy.sh [build|apply|delete]

set -e

COMMAND=${1:-apply}
NAMESPACE="weather-forecast"
IMAGE_NAME="weather-forecast"
IMAGE_TAG="latest"

case $COMMAND in
  build)
    echo "Building Docker image..."
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
    
    # If using a registry, push here
    # docker tag ${IMAGE_NAME}:${IMAGE_TAG} your-registry/${IMAGE_NAME}:${IMAGE_TAG}
    # docker push your-registry/${IMAGE_NAME}:${IMAGE_TAG}
    
    echo "✅ Image built successfully"
    ;;
    
  apply)
    echo "Deploying to K3s..."
    
    # Note: Secret is optional if using Ollama (no API key needed)
    if [ -f "k8s/secret.yaml" ]; then
      echo "Found k8s/secret.yaml, applying..."
      kubectl apply -f k8s/secret.yaml
    else
      echo "⚠️  k8s/secret.yaml not found (OK if using Ollama)"
    fi
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "Check status:"
    echo "  kubectl get pods -n ${NAMESPACE}"
    echo ""
    echo "View logs:"
    echo "  kubectl logs -f -n ${NAMESPACE} -l app=weather-forecast"
    echo ""
    echo "Port forward to access locally:"
    echo "  kubectl port-forward -n ${NAMESPACE} svc/weather-forecast 8000:8000"
    echo "  Then visit http://localhost:8000"
    ;;
    
  delete)
    echo "Deleting deployment..."
    kubectl delete -f k8s/service.yaml --ignore-not-found=true
    kubectl delete -f k8s/deployment.yaml --ignore-not-found=true
    kubectl delete -f k8s/configmap.yaml --ignore-not-found=true
    
    # Only delete secret if it exists
    if kubectl get secret weather-secrets -n weather-forecast &> /dev/null; then
      kubectl delete -f k8s/secret.yaml --ignore-not-found=true
    fi
    
    echo "✅ Deployment deleted"
    ;;
    
  *)
    echo "Usage: $0 [build|apply|delete]"
    echo ""
    echo "Commands:"
    echo "  build  - Build Docker image"
    echo "  apply  - Deploy to K3s (default)"
    echo "  delete - Remove deployment from K3s"
    exit 1
    ;;
esac
