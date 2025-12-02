# Fly.io Deployment Guide

Complete step-by-step guide to deploy your Patriot Center Backend to Fly.io - a platform that **doesn't sleep** and is **actually free**.

**Time to deploy:** ~10 minutes
**Difficulty:** Easy

---

## Why Fly.io?

- ✅ **No auto-sleep** - Your API stays running 24/7
- ✅ **Truly free tier** - 3 VMs with 256MB RAM each
- ✅ **Fast deployment** - One command to deploy
- ✅ **No capacity issues** - Unlike Oracle Cloud
- ✅ **Great DX** - Simple CLI, clear docs
- ✅ **Auto SSL** - HTTPS included free

---

## Prerequisites

- GitHub account (for your code)
- Credit card (required for signup but **won't be charged** on free tier)
- Terminal access

---

## Part 1: Install Fly.io CLI

### macOS
```bash
curl -L https://fly.io/install.sh | sh
```

After installation, add to your PATH (the installer will tell you how), then:
```bash
# Restart your terminal or run:
export PATH="$HOME/.fly/bin:$PATH"

# Verify installation
flyctl version
```

### Linux
```bash
curl -L https://fly.io/install.sh | sh
```

### Windows
```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

---

## Part 2: Sign Up & Login

### Step 1: Create Account
```bash
flyctl auth signup
```

This will open a browser window:
1. Sign up with GitHub (recommended) or email
2. Enter credit card info (required but **free tier won't charge**)
3. Verify email if needed

### Step 2: Login
```bash
flyctl auth login
```

Verify you're logged in:
```bash
flyctl auth whoami
```

---

## Part 3: Prepare Your Application

### Step 3: Review Configuration Files

I've already created these files for you:

1. **[Dockerfile](Dockerfile)** - Builds your Python app
2. **[fly.toml](fly.toml)** - Fly.io configuration
3. **[.dockerignore](.dockerignore)** - Excludes unnecessary files

### Step 4: Commit These Files

```bash
cd ~/Documents/patriot-center

# Add new files
git add Dockerfile fly.toml .dockerignore FLY_IO_DEPLOYMENT.md

# Commit
git commit -m "Add Fly.io deployment configuration"

# Push to GitHub
git push origin main
```

---

## Part 4: Deploy to Fly.io

### Step 5: Launch Your App

From your project directory:
```bash
cd ~/Documents/patriot-center

# Launch app (this deploys it!)
flyctl launch
```

**Answer the prompts:**

1. **App Name:** Press Enter to accept default or type: `patriot-center-api`
2. **Select Organization:** Choose your personal org (default)
3. **Choose a region:** Select closest to your users (e.g., `iad` for East Coast US, `lax` for West Coast)
4. **Would you like to set up a PostgreSQL database?** → **No**
5. **Would you like to set up an Upstash Redis database?** → **No**
6. **Would you like to deploy now?** → **Yes**

The deployment will:
- Build your Docker container
- Push it to Fly.io's registry
- Deploy to a VM
- Give you a URL

**This takes 2-3 minutes.** ☕

### Step 6: Wait for Deployment

You'll see output like:
```
==> Building image
==> Pushing image to registry
==> Deploying
--> v0 deployed successfully
```

When you see: **"Visit your newly deployed app at https://patriot-center-api.fly.dev"**

**You're live! 🎉**

---

## Part 5: Verify Deployment

### Step 7: Test Your API

```bash
# Check deployment status
flyctl status

# Test health endpoint
curl https://your-app-name.fly.dev/health

# Test API
curl https://your-app-name.fly.dev/get_aggregated_players/2025
```

### Step 8: View Logs

```bash
# Stream live logs
flyctl logs

# View recent logs
flyctl logs --recent
```

### Step 9: Check Your App URL

```bash
flyctl info
```

Your API is now live at: `https://your-app-name.fly.dev`

---

## Part 6: Update Your Frontend

### Step 10: Update Frontend to Use Fly.io URL

In your frontend code, update the API URL to:
```
https://your-app-name.fly.dev
```

For example, if your app is `patriot-center-api.fly.dev`, use:
```
https://patriot-center-api.fly.dev
```

---

## Part 7: Custom Domain (Optional)

### Step 11: Add Your Own Domain

If you have a domain:

```bash
# Add domain
flyctl certs add api.yourdomain.com

# Get DNS instructions
flyctl certs show api.yourdomain.com
```

Then add the DNS records shown to your domain provider.

SSL certificates are automatically provisioned!

---

## Part 8: Updating Your App

### Step 12: Deploy Updates

When you make code changes:

```bash
# Make your changes
# Commit to git
git add .
git commit -m "Your update message"
git push

# Deploy to Fly.io
flyctl deploy
```

**That's it!** New version deployed in 1-2 minutes.

---

## Part 9: Auto-Deploy with GitHub Actions

### Step 13: Set Up Automatic Deployments

Your repo already has a GitHub Actions workflow ([.github/workflows/fly-deploy.yml](.github/workflows/fly-deploy.yml)) that will automatically deploy to Fly.io when you push to main!

You just need to add your Fly.io API token as a GitHub secret:

**1. Get your Fly.io API token:**
```bash
flyctl auth token
```

Copy the token that's printed.

**2. Add it to GitHub:**
1. Go to your GitHub repo: `https://github.com/YOUR_USERNAME/patriot-center`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `FLY_API_TOKEN`
5. Value: Paste the token from step 1
6. Click **Add secret**

**3. Test it:**
```bash
# Make a small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "Test auto-deploy"
git push origin main
```

Go to your repo's **Actions** tab on GitHub and watch the deployment happen automatically! 🎉

Now every time you push to `main`, your API will auto-deploy to Fly.io.

---

## Part 10: Monitoring & Management

### Useful Commands

```bash
# Check app status
flyctl status

# View logs (live stream)
flyctl logs

# View app info
flyctl info

# SSH into your app
flyctl ssh console

# Open app in browser
flyctl open

# View resource usage
flyctl status --all

# Scale to more machines (still free up to 3)
flyctl scale count 2

# Check which apps you have
flyctl apps list
```

### Viewing Metrics

```bash
# Open monitoring dashboard
flyctl dashboard
```

This opens a web dashboard with:
- Request metrics
- Response times
- Error rates
- Resource usage

---

## Part 11: Troubleshooting

### App Won't Start

```bash
# Check logs for errors
flyctl logs

# Common issues:
# 1. Port mismatch - Make sure Dockerfile uses PORT 8080
# 2. Missing dependencies - Check requirements.txt
# 3. Import errors - Make sure patriot_center_backend/ is included
```

### Health Check Failing

```bash
# SSH into the machine
flyctl ssh console

# Test locally
curl localhost:8080/health

# Check if gunicorn is running
ps aux | grep gunicorn
```

### Deployment Failed

```bash
# View deployment logs
flyctl logs --recent

# Try deploying with verbose output
flyctl deploy --verbose

# If Docker build fails locally, test:
docker build -t test .
docker run -p 8080:8080 test
```

### App Keeps Stopping

Check your [fly.toml](fly.toml) has:
```toml
[http_service]
  auto_stop_machines = false
  min_machines_running = 1
```

Update if needed, then redeploy:
```bash
flyctl deploy
```

---

## Cost & Free Tier Details

**Fly.io Free Tier includes:**
- **3 shared-cpu-1x VMs** (256MB RAM each)
- **3GB persistent storage**
- **160GB outbound data transfer/month**

**Your current setup uses:**
- 1 VM (256MB RAM) = 33% of free allocation
- Minimal storage
- Light traffic = Well under data limits

**Bottom line:** Should be **100% free** forever! 🎉

---

## Performance Notes

Your app is lightweight and will run great on:
- **1 VM with 256MB RAM**
- Single Gunicorn worker with 2 threads
- Handles dozens of concurrent requests easily

If you need more:
```bash
# Add a second VM (still free!)
flyctl scale count 2

# Increase memory (uses more of free tier)
flyctl scale memory 512
```

---

## Comparison: Fly.io vs Others

| Feature | Fly.io | Oracle Cloud | Koyeb |
|---------|--------|--------------|-------|
| Auto-sleep | ❌ Never | ❌ Never | ✅ 1 min (bad!) |
| Setup time | 10 min | 30+ min | 5 min |
| Capacity issues | ❌ None | ✅ Major | ❌ None |
| Free forever | ✅ Yes | ✅ Yes | ⚠️ Limited |
| SSL included | ✅ Yes | ❌ Manual | ✅ Yes |
| Deploy time | 2 min | Manual | 2 min |

---

## Quick Reference

**Deploy app:**
```bash
flyctl deploy
```

**View logs:**
```bash
flyctl logs
```

**Check status:**
```bash
flyctl status
```

**Open app:**
```bash
flyctl open
```

**SSH to machine:**
```bash
flyctl ssh console
```

**Your API URL:**
```
https://your-app-name.fly.dev
```

---

## Need Help?

- Fly.io Docs: https://fly.io/docs
- Community Forum: https://community.fly.io
- Status Page: https://status.fly.io

---

## Next Steps After Deployment

1. ✅ Update your frontend to use new Fly.io URL
2. ✅ Test all endpoints work
3. ✅ Set up custom domain (optional)
4. ✅ Monitor logs for any issues
5. ✅ Celebrate! Your API is live and won't sleep! 🎉

---

**That's it!** You now have a production-ready API that:
- Never sleeps
- Auto-scales
- Has SSL
- Deploys in seconds
- Costs $0

Much better than fighting with Oracle's capacity issues! 🚀
