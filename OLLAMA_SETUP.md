# Ollama Setup Guide for Weather Forecast

## Why Ollama?

Ollama is a **lightweight, open-source LLM runtime** that makes it super easy to run local language models. Perfect for homelabs!

## System Requirements

- **VRAM**: 4-6GB (you're good!)
- **RAM**: 8GB+ recommended
- **Storage**: ~5GB per model
- **OS**: Linux, macOS, or Windows (WSL2)

## Installation

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS
```bash
brew install ollama
```

### Windows (WSL2)
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Docker (Recommended for K3s)

Deploy Ollama as a service in your K3s cluster:

```yaml
# ollama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
        resources:
          limits:
            nvidia.com/gpu: 1  # If you have GPU
          requests:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: ollama-data
        persistentVolumeClaim:
          claimName: ollama-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: default
spec:
  selector:
    app: ollama
  ports:
  - port: 11434
    targetPort: 11434
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

Deploy:
```bash
kubectl apply -f ollama-deployment.yaml
```

## Recommended Models (4-6GB VRAM)

### Best Overall: Llama 3.2 (3B)
```bash
ollama pull llama3.2:3b
```
- **VRAM**: ~3.5GB
- **Quality**: Excellent
- **Speed**: Fast
- **Perfect for weather summaries**

### Smallest: Phi-3 Mini
```bash
ollama pull phi3:mini
```
- **VRAM**: ~2.5GB
- **Quality**: Very good
- **Speed**: Very fast
- **Great for constrained systems**

### Best Quality (if you have 6GB): Mistral 7B (Quantized)
```bash
ollama pull mistral:7b-instruct-q4_0
```
- **VRAM**: ~5GB
- **Quality**: Excellent
- **Speed**: Moderate
- **Best summaries, but slower**

### Ultra-Lightweight: Gemma 2B
```bash
ollama pull gemma:2b
```
- **VRAM**: ~2GB
- **Quality**: Good
- **Speed**: Very fast
- **Backup option if others don't fit**

## Testing Your Setup

### Test Ollama Installation
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Should return something like:
# {"version":"0.1.x"}
```

### Pull a Model
```bash
# Pull the recommended model
ollama pull llama3.2:3b

# List installed models
ollama list
```

### Test the Model
```bash
# Quick test
ollama run llama3.2:3b "Summarize: It's 72°F and sunny with light winds."

# Should output something like:
# "Pleasant weather with clear skies, 72°F, and calm winds. Great day to be outside!"
```

### Test with curl (API test)
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Summarize this weather: 72°F, sunny, light winds",
  "stream": false
}'
```

## Configure Weather Forecast to Use Ollama

### Update .env
```bash
cd weather-forecast-k3s
cp .env.example .env
```

Edit `.env`:
```env
# Location
LATITUDE=36.1627
LONGITUDE=-86.7816
LOCATION_NAME=Your City

# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

### For K3s Deployment

If Ollama is running in your K3s cluster, update `k8s/configmap.yaml`:

```yaml
OLLAMA_BASE_URL: "http://ollama.default.svc.cluster.local:11434"
OLLAMA_MODEL: "llama3.2:3b"
```

## Performance Tuning

### Optimd
Use smaller, faster models:
```bash
ollama pull phi3:mini
```

Update `.env`:
```env
OLLAMA_MODEL=phi3:mini
```

### Optimize for Quality
Use larger models if you have 6GB VRAM:
```bash
ollama pull mistral:7b-instruct-q4_0
```

Update `.env`:
```env
OLLAMA_MODEL=mistral:7b-instruct-q4_0
```

### Reduce Context Length (Save VRAM)
Ollama automatically manages this, but you can tune it:

```bash
# Run with lower context (uses less VRAM)
ollama run llama3.2:3b --ctx-size 2048
```

## Troubleshooting

### "Connection refused" Error

**Check if Ollama is running:**
```bash
ps aux | grep ollama
# or
systemctl status ollama  # Linux
```

**Start Ollama:**
```bash
ollama serve  # Foreground
# or
systemctl start ollama  # Linux background
```

### "Out of Memory" Error

**Use a smaller model:**
```bash
ollama pull gemma:2b
```

**Or use quantization:**
```bash
ollama pull llama3.2:3b-q4_0  # More quantized = less memory
```

### Model Download Stuck

**Check storage space:**
```bash
df -h
```

**Retry download:**
```bash
ollama rm llama3.2:3b  # Remove partial download
ollama pull llama3.2:3b  # Try again
```

### Slow Inference

**Enable GPU acceleration (if available):**
```bash
# Check GPU detection
ollama list

# Should show GPU info if detected
```

**Use a faster model:**
```bash
ollama pull phi3:mini
```

## Advanced: Running Multiple Models

You can switch models dynamically:

```bash
# Pull multiple models
ollama pull llama3.2:3b      # Balanced
ollama pull phi3:mini         # Fast
ollama pull mistral:7b-q4_0   # Quality

# Weather service will use whichever is configured in .env
```

## Cost Comparison

| Solution | Cost | Privacy | Speed | Quality |
|----------|------|---------|-------|---------|
| **Ollama (local)** | Free | 100% private | Fast | Good-Excellent |
| OpenAI GPT-3.5 | $0.50/1M tokens | Cloud | Very fast | Excellent |
| OpenAI GPT-4 | $30/1M tokens | Cloud | Moderate | Best |
| Claude | $15/1M tokens | Cloud | Fast | Excellent |

**For weather summaries (estimate):**
- ~100 tokens per summary
- ~144 summaries/day (every 10 min)
- ~4,320 summaries/month
- **Ollama: $0/month** 🎉
- OpenAI GPT-3.5: ~$0.22/month
- OpenAI GPT-4: ~$13/month

## Recommended Setup

**For your 4-6GB VRAM homelab:**

1. **Deploy Ollama in K3s** (use the YAML above)
2. **Pull Llama 3.2 3B**: `kubectl exec -it ollama-pod -- ollama pull llama3.2:3b`
3. **Configure weather service** to use `http://ollama.default.svc.cluster.local:11434`
4. **Enjoy free, private AI weather summaries!** 🌦️

## Alternative: CPU-Only Mode

If you don't have GPU/VRAM, Ollama works on CPU (slower but functional):

```bash
# Install normally
curl -fsSL https://ollama.com/install.sh | sh

# Pull a tiny model for CPU
ollama pull phi3:mini

# Works, but slower (3-5 seconds per summary vs <1 second on GPU)
```

## Questions?

Check:
- Ollama docs: https://ollama.com/docs
- Model library: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama

Built with ❤️ for homelabs! 🐶
