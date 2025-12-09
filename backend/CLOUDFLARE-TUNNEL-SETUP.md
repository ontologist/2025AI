# Cloudflare Tunnel Setup for AI-300 Bot

## Why Cloudflare Tunnel?

- ✅ Free HTTPS for your backend
- ✅ No need to expose ports on your router
- ✅ Works from anywhere (home, campus, etc.)
- ✅ Permanent URL (unlike ngrok free tier)
- ✅ Automatic SSL certificate

---

## Step 1: Install Cloudflared (if not already installed)

```powershell
# Option A: Using winget (recommended)
winget install --id Cloudflare.cloudflared

# Option B: Download manually from:
# https://github.com/cloudflare/cloudflared/releases/latest
# Download: cloudflared-windows-amd64.exe
# Rename to cloudflared.exe and add to PATH
```

Verify installation:
```powershell
cloudflared --version
```

---

## Step 2: Login to Cloudflare (if not already logged in)

```powershell
cloudflared tunnel login
```

This opens your browser. Select your **tijerino.ai** domain and authorize.

---

## Step 3: Create the AI-300 Bot Tunnel

```powershell
cloudflared tunnel create ai300bot
```

**⚠️ SAVE THE OUTPUT!** You'll see something like:
```
Created tunnel ai300bot with id a1b2c3d4-e5f6-7890-abcd-1234567890ab
```

Copy that tunnel ID — you'll need it next.

---

## Step 4: Create the Configuration File

First, find your credentials file:
```powershell
dir $env:USERPROFILE\.cloudflared\*.json
```

You should see a file like `a1b2c3d4-e5f6-7890-abcd-1234567890ab.json`

Now create/edit the config file:

```powershell
notepad $env:USERPROFILE\.cloudflared\config.yml
```

Add this content (replace the values):

```yaml
# AI-300 Bot Tunnel Configuration
tunnel: YOUR_TUNNEL_ID_HERE
credentials-file: C:\Users\yuri\.cloudflared\YOUR_TUNNEL_ID_HERE.json

ingress:
  # AI-300 Bot (port 8003)
  - hostname: ai300bot.tijerino.ai
    service: http://localhost:8003
  
  # Catch-all (required)
  - service: http_status:404
```

**Replace:**
- `YOUR_TUNNEL_ID_HERE` with your actual tunnel ID (e.g., `a1b2c3d4-e5f6-7890-abcd-1234567890ab`)

---

## Step 5: Add DNS Record in Cloudflare

Go to your Cloudflare dashboard: https://dash.cloudflare.com

1. Select **tijerino.ai** domain
2. Go to **DNS** → **Records**
3. Click **Add record**:
   - **Type:** `CNAME`
   - **Name:** `ai300bot`
   - **Target:** `YOUR_TUNNEL_ID_HERE.cfargotunnel.com`
   - **Proxy status:** **Proxied** (orange cloud ON)
   - **TTL:** Auto
4. Click **Save**

Example:
| Type | Name | Target | Proxy |
|------|------|--------|-------|
| CNAME | ai300bot | a1b2c3d4-e5f6-7890-abcd-1234567890ab.cfargotunnel.com | Proxied |

---

## Step 6: Start the Tunnel

Make sure your backend is running first:
```powershell
# Terminal 1: Start the backend
cd C:\Users\yuri\OneDrive\Documents\GitHub\2025AI\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003
```

Then start the tunnel:
```powershell
# Terminal 2: Start the tunnel
cloudflared tunnel run ai300bot
```

You should see output like:
```
INF Starting tunnel tunnelID=a1b2c3d4...
INF Connection established connIndex=0 ...
```

---

## Step 7: Test the HTTPS URL

Wait 1-2 minutes for DNS propagation, then test:

**In browser:**
```
https://ai300bot.tijerino.ai/
```

Should return:
```json
{
  "message": "AI-300 Course Bot API",
  "course": "AI-300 Basic Artificial Intelligence | 人工知能基礎",
  "version": "1.0.0",
  "features": ["RAG", "Web Search", "Ollama LLM"]
}
```

**Health check:**
```
https://ai300bot.tijerino.ai/health
```

---

## Step 8: Update Frontend (Already Done!)

The `docs/bot-chat.js` already has the correct default URL:
```javascript
return 'https://ai300bot.tijerino.ai/api';
```

No changes needed! 🎉

---

## Step 9: Test from GitHub Pages

1. Go to: https://2025ai.tijerino.ai/#bot-portal
2. Type a message like: "What is artificial intelligence?"
3. Should get a response from the bot!

---

## Step 10: Run Tunnel as Windows Service (Optional)

To auto-start the tunnel on boot:

```powershell
# Run as Administrator
cloudflared service install
cloudflared service start
```

To check status:
```powershell
cloudflared service status
```

To remove the service later:
```powershell
cloudflared service uninstall
```

---

## Quick Reference Commands

```powershell
# List all tunnels
cloudflared tunnel list

# Check tunnel status
cloudflared tunnel info ai300bot

# Run tunnel manually
cloudflared tunnel run ai300bot

# Delete tunnel (if needed)
cloudflared tunnel delete ai300bot
```

---

## Troubleshooting

### "Bad gateway" or 502 Error
- Make sure the backend is running on port 8003
- Check: `curl http://localhost:8003/health`

### DNS not resolving
- Wait 2-5 minutes for DNS propagation
- Check Cloudflare DNS dashboard for the CNAME record
- Verify the tunnel ID matches

### Tunnel not connecting
- Check Cloudflare dashboard → Zero Trust → Tunnels
- Verify `config.yml` syntax (YAML is space-sensitive!)
- Try: `cloudflared tunnel run ai300bot --loglevel debug`

### Mixed content error on GitHub Pages
- Make sure you're using `https://` URL
- Check browser console for errors
- Verify the tunnel is running

---

## Your Configuration Summary

| Item | Value |
|------|-------|
| Domain | tijerino.ai |
| Subdomain | ai300bot |
| Full URL | https://ai300bot.tijerino.ai |
| Backend Port | 8003 |
| Tunnel Name | ai300bot |

---

**Once complete, your AI-300 bot will be accessible from the GitHub Pages site!** 🎉

