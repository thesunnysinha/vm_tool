#!/bin/bash

# EC2 Setup Script for GitHub Actions Deployment
# Run this on your EC2 instance

set -e

echo "🚀 Setting up EC2 for GitHub Actions Deployment"
echo "================================================"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Create deploy user
echo "👤 Creating deploy user..."
if ! id "deploy" &>/dev/null; then
    sudo adduser --disabled-password --gecos "" deploy
    sudo usermod -aG docker deploy
    sudo usermod -aG sudo deploy
    echo "✅ Deploy user created"
else
    echo "✅ Deploy user already exists"
fi

# Add current user to docker group
echo "👤 Adding $USER to docker group..."
sudo usermod -aG docker $USER

# Create app directory
echo "📁 Creating app directory..."
sudo mkdir -p /home/deploy/app
sudo chown -R deploy:deploy /home/deploy/app

# Create backups directory
echo "📁 Creating backups directory..."
sudo mkdir -p /home/deploy/backups
sudo chown -R deploy:deploy /home/deploy/backups

# Install useful tools
echo "🛠️  Installing useful tools..."
sudo apt install -y git curl wget htop ncdu

# Configure firewall
echo "🔒 Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    sudo ufw allow 8000/tcp  # App port (adjust as needed)
    echo "✅ Firewall configured (not enabled yet)"
    echo "⚠️  To enable: sudo ufw enable"
else
    echo "⚠️  UFW not installed"
fi

# Print SSH public key location
echo ""
echo "================================================"
echo "✅ EC2 Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Add your GitHub Actions public key to ~/.ssh/authorized_keys"
echo "2. Test SSH connection from your local machine"
echo "3. Configure your GitHub repository secrets"
echo ""
echo "To add SSH key:"
echo "  mkdir -p ~/.ssh"
echo "  echo 'YOUR_PUBLIC_KEY' >> ~/.ssh/authorized_keys"
echo "  chmod 600 ~/.ssh/authorized_keys"
echo "  chmod 700 ~/.ssh"
echo ""
echo "Logout and login again to apply docker group changes"
