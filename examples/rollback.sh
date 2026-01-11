#!/bin/bash

# Emergency Rollback Script

set -e

echo "🔄 Emergency Rollback"
echo "===================="

# Get host from argument or prompt
HOST=${1:-}
if [ -z "$HOST" ]; then
    read -p "Enter host IP: " HOST
fi

# Show recent deployments
echo ""
echo "📜 Recent deployments for $HOST:"
vm_tool history --host $HOST --limit 5

# Get deployment ID
echo ""
read -p "Enter deployment ID to rollback to (or press Enter for previous): " DEPLOYMENT_ID

# Confirm rollback
echo ""
echo "⚠️  WARNING: This will rollback the deployment on $HOST"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Rollback cancelled"
    exit 1
fi

# Execute rollback
echo ""
echo "🔄 Rolling back..."
if [ -z "$DEPLOYMENT_ID" ]; then
    vm_tool rollback --host $HOST
else
    vm_tool rollback --host $HOST --to $DEPLOYMENT_ID
fi

# Verify
echo ""
echo "✅ Rollback complete. Current deployment:"
vm_tool history --host $HOST --limit 1

echo ""
echo "🔍 Checking system health..."
# Add your health check commands here
# vm_tool drift-check --host $HOST
