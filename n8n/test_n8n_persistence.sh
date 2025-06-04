#!/bin/bash

# Test script for N8N data persistence
# This script helps verify that N8N data persists across container restarts and removals

echo "===== N8N Data Persistence Test ====="
echo ""

# Step 1: Start the containers
echo "Step 1: Starting containers with docker-compose..."
docker-compose up -d
echo ""

# Step 2: Wait for N8N to be ready
echo "Step 2: Waiting for N8N to be ready (30 seconds)..."
sleep 30
echo ""

# Step 3: Check if N8N is running
echo "Step 3: Checking if N8N is running..."
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ N8N is running successfully!"
else
    echo "❌ N8N is not running. Please check the logs with 'docker-compose logs n8n'"
    exit 1
fi
echo ""

# Step 4: Instructions for creating a test workflow
echo "Step 4: Please create a test workflow in N8N:"
echo "1. Open http://localhost:5678 in your browser"
echo "2. Create a new workflow (e.g., 'Persistence Test')"
echo "3. Add a simple node (e.g., a 'Cron' trigger and a 'NoOp' action)"
echo "4. Save the workflow"
echo ""
echo "After creating the workflow, press Enter to continue..."
read -p ""

# Step 5: Stop and remove containers (but keep volumes)
echo "Step 5: Stopping and removing containers (keeping volumes)..."
docker-compose down
echo ""

# Step 6: Start containers again
echo "Step 6: Starting containers again..."
docker-compose up -d
echo ""

# Step 7: Wait for N8N to be ready again
echo "Step 7: Waiting for N8N to be ready again (30 seconds)..."
sleep 30
echo ""

# Step 8: Check if N8N is running again
echo "Step 8: Checking if N8N is running again..."
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ N8N is running successfully!"
else
    echo "❌ N8N is not running. Please check the logs with 'docker-compose logs n8n'"
    exit 1
fi
echo ""

# Step 9: Instructions for verifying persistence
echo "Step 9: Please verify that your test workflow still exists:"
echo "1. Open http://localhost:5678 in your browser"
echo "2. Check if your 'Persistence Test' workflow is still there"
echo ""
echo "If the workflow is still there, data persistence is working correctly! 🎉"
echo "If the workflow is missing, there might be an issue with the volume configuration. 😢"
echo ""

echo "===== Test Complete ====="