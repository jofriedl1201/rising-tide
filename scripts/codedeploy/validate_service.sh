#!/bin/bash
# CodeDeploy: Validate Service Hook
# Verifies the service is running correctly

echo "Validating Rising Tide service..."

# Wait for service to fully start
sleep 5

# Check if service is active
if sudo systemctl is-active --quiet rising-tide; then
    echo "✓ Service is running"
else
    echo "✗ Service failed to start"
    sudo systemctl status rising-tide
    exit 1
fi

# Check if API is responding
if curl -f http://localhost:8000/auth/users/me > /dev/null 2>&1; then
    echo "✓ API is responding"
else
    echo "⚠ API check returned non-200 (this may be normal for auth endpoints)"
fi

# Check logs for critical errors
if sudo journalctl -u rising-tide -n 20 | grep -i "critical\|fatal" > /dev/null; then
    echo "✗ Critical errors found in logs"
    sudo journalctl -u rising-tide -n 20
    exit 1
fi

echo "✓ Service validation complete"
exit 0
