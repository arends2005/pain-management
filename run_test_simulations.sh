#!/bin/bash

# Check if user id is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <user_id> [days]"
    exit 1
fi

USER_ID=$1
DAYS=${2:-1}  # Default to 1 day if not specified

echo "Running Discord reminder simulation for user $USER_ID over $DAYS days"

# Copy the test script to the container
docker compose cp test_discord_reminders.py web:/app/

# Run the test script in the container
docker compose exec web python /app/test_discord_reminders.py $USER_ID $DAYS

echo "Simulation completed" 