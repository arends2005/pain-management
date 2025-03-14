#!/bin/bash
# Script to rebuild the Discord bot and database

echo "📦 Rebuilding Discord Bot and Database..."
echo "This will delete all existing data! Press Ctrl+C to cancel."
echo "Waiting 5 seconds..."
sleep 5

echo "🛑 Stopping and removing existing containers..."
docker compose down -v

echo "🏗️ Building new containers..."
docker compose up --build -d

echo "🔄 Waiting for database to initialize..."
sleep 10

echo "🔧 Applying database schema changes..."
docker compose exec web python db_init_with_upgrades.py

echo "✅ Rebuild complete!"
echo ""
echo "To test the Discord bot connection, use:"
echo "docker compose exec web python test_discord_channel.py <channel_id> <bot_token>"
echo ""
echo "Make sure to update your Discord preferences in the app to add a channel ID" 