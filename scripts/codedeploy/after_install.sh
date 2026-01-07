#!/bin/bash
# CodeDeploy: After Install Hook
# Sets up the application after files are deployed

echo "Running post-installation tasks..."

cd /home/ubuntu/rising-tide/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Ensure .env file exists (should be on server already)
if [ ! -f .env ]; then
    echo "WARNING: .env file not found! Application may fail to start."
    echo "Please create /home/ubuntu/rising-tide/backend/.env with production values"
fi

# Set proper permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/rising-tide

echo "Post-installation complete"
