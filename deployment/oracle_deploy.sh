#!/bin/bash
# Oracle Cloud Deployment Script for Patriot Center Backend
# Run this script on your Oracle Cloud Ubuntu instance

set -e

echo "=========================================="
echo "Patriot Center Backend - Oracle Cloud Setup"
echo "=========================================="

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip git nginx iptables-persistent

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/patriot-center
sudo chown -R ubuntu:ubuntu /opt/patriot-center

# Check if files already exist in current directory
if [ -f "requirements.txt" ] && [ -d "patriot_center_backend" ]; then
    echo "Found project files in current directory, copying to /opt/patriot-center..."
    cp -r . /opt/patriot-center/
elif [ -d "$HOME/patriot-center-upload" ]; then
    echo "Found uploaded files, copying to /opt/patriot-center..."
    cp -r $HOME/patriot-center-upload/* /opt/patriot-center/
else
    # Clone or copy your repository
    echo "Setting up application..."
    echo "Note: You can either:"
    echo "  1. Clone from GitHub"
    echo "  2. Use upload_to_oracle.sh script first to copy files"
    echo ""
    read -p "Do you want to clone from GitHub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your GitHub repository URL: " REPO_URL
        cd /opt/patriot-center
        git clone "$REPO_URL" .
    else
        echo "Please upload your files first using the upload_to_oracle.sh script"
        exit 0
    fi
fi

cd /opt/patriot-center

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Configure firewall
echo "Configuring firewall..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save || echo "Firewall rules saved (ignore warnings)"

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/patriot-center.service > /dev/null <<EOF
[Unit]
Description=Patriot Center Backend API
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/patriot-center
Environment="PATH=/opt/patriot-center/venv/bin"
ExecStart=/opt/patriot-center/venv/bin/gunicorn \\
    patriot_center_backend.app:app \\
    --bind 127.0.0.1:8080 \\
    --workers 1 \\
    --threads 2 \\
    --timeout 120 \\
    --access-logfile /var/log/patriot-center/access.log \\
    --error-logfile /var/log/patriot-center/error.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log/patriot-center
sudo chown ubuntu:ubuntu /var/log/patriot-center

# Configure nginx
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/patriot-center > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/patriot-center /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Start the service
echo "Starting Patriot Center service..."
sudo systemctl daemon-reload
sudo systemctl enable patriot-center
sudo systemctl start patriot-center

# Check status
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Service Status:"
sudo systemctl status patriot-center --no-pager
echo ""
echo "Your API should now be accessible at: http://$(curl -s ifconfig.me)"
echo ""
echo "Useful commands:"
echo "  - Check logs: sudo journalctl -u patriot-center -f"
echo "  - Restart service: sudo systemctl restart patriot-center"
echo "  - Check nginx: sudo systemctl status nginx"
echo ""
