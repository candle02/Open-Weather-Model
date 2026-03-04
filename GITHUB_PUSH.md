# Push to GitHub: Open Weather Model

Your repository is ready to push to:
**https://github.com/candle02/Open-Weather-Model.git**

## Quick Method (Automated)

### Windows:

1. **Close this terminal/command prompt**
2. **Open a NEW terminal** (so Git is in PATH)
3. **Navigate to the project:**
   ```cmd
   cd C:\Users\cms00vk\Documents\puppy_workspace\weather-forecast-k3s
   ```
4. **Run the push script:**
   ```cmd
   push-to-github.bat
   ```

Done! ✅

### Linux/macOS:

```bash
cd weather-forecast-k3s
chmod +x push-to-github.sh
./push-to-github.sh
```

---

## Manual Method (If Script Fails)

Run these commands one by one:

```bash
# Navigate to project
cd C:\Users\cms00vk\Documents\puppy_workspace\weather-forecast-k3s

# Initialize Git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: AI Weather Forecast with Ollama

- Multi-source weather aggregation (Weather.gov, Open-Meteo, wttr.in)
- AI summaries via Ollama (local, open-source LLM)
- Trend analysis and anomaly detection
- Custom ML predictions with Prophet
- Smart home recommendations for Home Assistant
- K3s/Kubernetes deployment ready
- 100% free and open source
- No API keys required!"

# Add GitHub remote
git remote add origin https://github.com/candle02/Open-Weather-Model.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## Verify It Worked

Visit: **https://github.com/candle02/Open-Weather-Model**

You should see:
- ✅ README.md displayed
- ✅ All your files
- ✅ Documentation (OLLAMA_SETUP.md, etc.)
- ✅ K8s manifests
- ✅ Python code

---

## Future Updates

When you make changes:

```bash
cd weather-forecast-k3s

# See what changed
git status

# Add changes
git add .

# Commit with message
git commit -m "Your update message here"

# Push to GitHub
git push
```

---

## Clone on Another Computer

To get this code on your homelab server or another machine:

```bash
git clone https://github.com/candle02/Open-Weather-Model.git
cd Open-Weather-Model
```

Then follow the setup instructions in `SETUP.md`!

---

## Troubleshooting

### "Git is not recognized"

**Solution:** Close terminal, open a NEW one. Git was just installed.

### "Permission denied (publickey)"

**Option 1 - HTTPS (easier):**
GitHub will prompt for username/password or token.

**Option 2 - SSH (better):**
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH Keys → New SSH key

# Change remote to SSH
git remote set-url origin git@github.com:candle02/Open-Weather-Model.git
```

### "Repository already exists"

You already pushed! Just run:
```bash
git pull origin main
```

---

**Your code is ready to go to GitHub!** 🚀🐶
