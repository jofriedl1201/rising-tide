#!/bin/bash
# CodeDeploy: Application Stop Hook
# Stops the Rising Tide service before deployment

echo "Stopping Rising Tide service..."

# Stop the systemd service
sudo systemctl stop rising-tide || true

echo "Service stopped successfully"
