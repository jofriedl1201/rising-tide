#!/bin/bash
# CodeDeploy: Before Install Hook
# Prepares the system before installation

echo "Running pre-installation tasks..."

# Create application directory if it doesn't exist
sudo mkdir -p /home/ubuntu/rising-tide
sudo chown ubuntu:ubuntu /home/ubuntu/rising-tide

# Remove old virtual environment
rm -rf /home/ubuntu/rising-tide/backend/venv

echo "Pre-installation complete"
