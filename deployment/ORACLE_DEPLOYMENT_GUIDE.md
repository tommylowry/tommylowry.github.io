# Oracle Cloud Deployment Guide

## Step 1: Create Compute Instance

### Deal with "No Capacity" Issue:
- **Try different times**: Late night/early morning US time typically has capacity
- **Try different regions**: Switch region in top-right of Oracle Console
- **Keep checking**: Capacity can open up suddenly

### Instance Configuration:
1. Go to: **Compute → Instances → Create Instance**
2. Settings:
   - **Name:** `patriot-center-api`
   - **Image:** Canonical Ubuntu 22.04 or 24.04
   - **Shape:** VM.Standard.E2.1.Micro (Always Free)
   - **VCN:** `patriot-center-vcn`
   - **Subnet:** `public subnet-patriot-center-vcn` (10.0.0.0/24)
   - **Public IP:** ✅ Assign public IPv4 address
   - **SSH Keys:** Download the private key or paste your public key

3. **Copy the Public IP address** - you'll need this!

---

## Step 2: Configure Security Rules

### A. VCN Security List (In Oracle Console):
1. Go to: **Networking → Virtual Cloud Networks → patriot-center-vcn**
2. Click: **Security Lists → Default Security List**
3. Click: **Add Ingress Rules**
4. Add these rules:

**Rule 1 - HTTP:**
- Source CIDR: `0.0.0.0/0`
- IP Protocol: `TCP`
- Destination Port: `80`

**Rule 2 - HTTPS:**
- Source CIDR: `0.0.0.0/0`
- IP Protocol: `TCP`
- Destination Port: `443`

### B. Ubuntu Firewall (You'll run this on the instance):
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## Step 3: Connect to Your Instance

```bash
# Make your SSH key usable
chmod 400 ~/path/to/your-private-key.pem

# Connect to instance (replace with your public IP)
ssh -i ~/path/to/your-private-key.pem ubuntu@YOUR_PUBLIC_IP
```

---

## Step 4: Deploy Your Application

### Option A: Automated Deployment (Recommended)

1. **Copy your project files to the instance:**
```bash
# From your local machine, in your project directory
scp -i ~/path/to/your-private-key.pem -r . ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/patriot-center/
```

2. **Copy and run the deployment script:**
```bash
# From your local machine, in the project directory
scp -i ~/path/to/your-private-key.pem deployment/oracle_deploy.sh ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/

# SSH into the instance
ssh -i ~/path/to/your-private-key.pem ubuntu@YOUR_PUBLIC_IP

# Run the deployment script
chmod +x oracle_deploy.sh
./oracle_deploy.sh
```

### Option B: Manual Step-by-Step

If the automated script has issues, follow these manual steps:

```bash
# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install required packages
sudo apt-get install -y python3.11 python3.11-venv python3-pip nginx git iptables-persistent

# 3. Create app directory
sudo mkdir -p /opt/patriot-center
sudo chown -R ubuntu:ubuntu /opt/patriot-center

# 4. Copy your files (from local machine in another terminal)
# scp -i ~/path/to/key.pem -r /Users/tommylowry/Documents/patriot-center ubuntu@YOUR_IP:/opt/patriot-center/

# 5. Set up Python virtual environment
cd /opt/patriot-center
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Configure firewall
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save

# 7. Create systemd service
sudo nano /etc/systemd/system/patriot-center.service
# Paste the content from oracle_deploy.sh

# 8. Configure nginx
sudo nano /etc/nginx/sites-available/patriot-center
# Paste the nginx config from oracle_deploy.sh

# 9. Enable and start services
sudo ln -sf /etc/nginx/sites-available/patriot-center /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl daemon-reload
sudo systemctl enable patriot-center
sudo systemctl start patriot-center

# 10. Check status
sudo systemctl status patriot-center
```

---

## Step 5: Verify Deployment

```bash
# Check if your API is running
curl http://localhost:8080/health

# Check from outside
curl http://YOUR_PUBLIC_IP/health

# View logs
sudo journalctl -u patriot-center -f
```

---

## Step 6: Update Frontend

Once your API is running, update your frontend to use the new URL:

- Replace `https://patriot-center-api.fly.dev` with `http://YOUR_PUBLIC_IP`
- If you want HTTPS, we can set up Let's Encrypt SSL later

---

## Troubleshooting

### Service won't start:
```bash
sudo journalctl -u patriot-center -n 50
```

### Port 80 not accessible:
- Check Oracle Security List (Web Console)
- Check Ubuntu firewall: `sudo iptables -L -n`
- Check nginx: `sudo systemctl status nginx`

### Check what's running on ports:
```bash
sudo netstat -tulpn | grep -E ':(80|8080)'
```

---

## Useful Commands

```bash
# Restart API
sudo systemctl restart patriot-center

# View API logs
sudo journalctl -u patriot-center -f

# Check API status
sudo systemctl status patriot-center

# Restart nginx
sudo systemctl restart nginx

# Update code
cd /opt/patriot-center
git pull  # if using git
sudo systemctl restart patriot-center
```
