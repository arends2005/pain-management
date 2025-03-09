#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Wait for web service to be ready (to ensure database migrations have been applied)
echo "Waiting for web service to be ready..."
sleep 10
echo "Starting Discord bot..."

# Start the Discord bot
exec python discord_bot.py 