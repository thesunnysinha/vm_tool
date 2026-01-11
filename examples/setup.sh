#!/bin/bash

# Setup Script - Configure vm_tool for your environment

echo "🔧 VM Tool Setup"
echo "================"

# Create development profile
echo ""
echo "Creating development profile..."
vm_tool config create-profile dev \
  --environment development \
  --host 192.168.1.100 \
  --user ubuntu \
  --compose-file docker-compose.dev.yml

# Create staging profile
echo ""
echo "Creating staging profile..."
vm_tool config create-profile staging \
  --environment staging \
  --host 10.0.1.5 \
  --user deploy \
  --compose-file docker-compose.yml

# Create production profile
echo ""
echo "Creating production profile..."
vm_tool config create-profile production \
  --environment production \
  --host 10.0.2.10 \
  --user prod \
  --compose-file docker-compose.yml

# Set defaults
echo ""
echo "Setting default configuration..."
vm_tool config set default-user ubuntu
vm_tool config set default-compose-file docker-compose.yml

# List all profiles
echo ""
echo "📋 Configured profiles:"
vm_tool config list-profiles

echo ""
echo "✅ Setup complete!"
echo ""
echo "Usage examples:"
echo "  vm_tool deploy-docker --profile dev"
echo "  vm_tool deploy-docker --profile staging --dry-run"
echo "  vm_tool deploy-docker --profile production --health-port 8000"
