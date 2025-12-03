#!/bin/bash
# Quick script to upload your project to Oracle Cloud instance

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "Patriot Center - Upload to Oracle Cloud"
echo -e "==========================================${NC}"
echo ""

# Get SSH key path
echo -e "${YELLOW}Enter the path to your SSH private key:${NC}"
read -p "(e.g., ~/.ssh/oracle_key.pem): " SSH_KEY
SSH_KEY="${SSH_KEY/#\~/$HOME}"  # Expand ~ to full path

if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Make sure key has correct permissions
chmod 400 "$SSH_KEY"

# Get instance IP
echo ""
echo -e "${YELLOW}Enter your Oracle instance PUBLIC IP address:${NC}"
read -p "IP: " INSTANCE_IP

# Test connection
echo ""
echo -e "${GREEN}Testing connection...${NC}"
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@"$INSTANCE_IP" "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to instance${NC}"
    echo "Make sure:"
    echo "  1. The IP address is correct"
    echo "  2. The security list allows SSH (port 22)"
    echo "  3. The SSH key is correct"
    exit 1
fi

echo -e "${GREEN}✓ Connection successful!${NC}"
echo ""

# Create remote directory
echo -e "${GREEN}Creating remote directory...${NC}"
ssh -i "$SSH_KEY" ubuntu@"$INSTANCE_IP" "mkdir -p ~/patriot-center-upload"

# Upload files (excluding unnecessary directories)
echo ""
echo -e "${GREEN}Uploading project files...${NC}"
echo -e "${YELLOW}This may take a minute...${NC}"

rsync -avz --progress \
    -e "ssh -i $SSH_KEY" \
    --exclude 'patriot_center_frontend/node_modules' \
    --exclude 'patriot_center_frontend/build' \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache' \
    --exclude 'venv' \
    --exclude '.vscode' \
    --exclude 'fly.toml' \
    --exclude 'FLY_IO_DEPLOYMENT.md' \
    . ubuntu@"$INSTANCE_IP":~/patriot-center-upload/

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Upload complete!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Connect to your instance:"
    echo -e "   ${GREEN}ssh -i $SSH_KEY ubuntu@$INSTANCE_IP${NC}"
    echo ""
    echo "2. Run the deployment script:"
    echo -e "   ${GREEN}cd ~/patriot-center-upload${NC}"
    echo -e "   ${GREEN}chmod +x oracle_deploy.sh${NC}"
    echo -e "   ${GREEN}./oracle_deploy.sh${NC}"
    echo ""
else
    echo -e "${RED}Error: Upload failed${NC}"
    exit 1
fi
