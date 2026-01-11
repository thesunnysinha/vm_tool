#!/bin/bash

# Production Deployment Script
# This script demonstrates a complete production deployment workflow using vm_tool

set -e  # Exit on error

echo "🚀 Starting Production Deployment"
echo "=================================="

# Configuration
PROFILE="production"
HOST="10.0.2.10"
BACKUP_PATHS="/app /etc/nginx /var/www"

# Step 1: Create backup before deployment
echo ""
echo "📦 Step 1: Creating backup..."
vm_tool backup create \
  --host $HOST \
  --paths $BACKUP_PATHS

# Step 2: Check for configuration drift
echo ""
echo "🔍 Step 2: Checking for configuration drift..."
if ! vm_tool drift-check --host $HOST; then
    echo "⚠️  Warning: Drift detected. Review changes before proceeding."
    read -p "Continue anyway? (yes/no): " continue
    if [ "$continue" != "yes" ]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Step 3: Dry-run deployment
echo ""
echo "🔍 Step 3: Running dry-run..."
vm_tool deploy-docker --profile $PROFILE --dry-run

# Step 4: Confirm deployment
echo ""
read -p "Proceed with deployment? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Step 5: Deploy with health checks
echo ""
echo "🚀 Step 5: Deploying..."
vm_tool deploy-docker \
  --profile $PROFILE \
  --health-port 8000 \
  --health-url "http://$HOST:8000/health" \
  --health-check "docker ps | grep web"

# Step 6: Verify deployment
echo ""
echo "✅ Step 6: Verifying deployment..."
vm_tool history --host $HOST --limit 1

# Step 7: Final drift check
echo ""
echo "🔍 Step 7: Final drift check..."
vm_tool drift-check --host $HOST

echo ""
echo "=================================="
echo "✅ Production deployment complete!"
echo "=================================="
