#!/bin/bash
# CodeDeploy: Application Start Hook
# Starts the Rising Tide service

echo "Starting Rising Tide service..."

# Reload systemd daemon
sudo systemctl daemon-reload

# Start the service
sudo systemctl start rising-tide

# Enable auto-start on boot
sudo systemctl enable rising-tide

echo "Service started successfully"
