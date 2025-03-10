# Discord Bot Setup

This document explains how to set up and configure the Discord bot for the Pain Management App.

## Prerequisites

1. You must have a Discord account
2. You need to create a Discord bot in the Developer Portal
3. You need to add the bot to your server

## Creating a Bot

1. Go to the Discord Developer Portal: https://discord.com/developers/applications
2. Click "New Application" and give it a name (e.g., "Pain Management Bot")
3. Go to the "Bot" tab and click "Add Bot"
4. Under the "TOKEN" section, click "Copy" to copy your bot token
5. Add this token to your `.env` file as `DISCORD_BOT_TOKEN`

## Bot Permissions

The bot needs the following permissions:
- Read Messages/View Channels
- Send Messages
- Read Message History

These permissions have a bit value of `68608`. You'll need this when creating the invite URL.

## Adding the Bot to Your Server

1. Go to the "OAuth2" tab in the Developer Portal
2. In the "URL Generator" section, select "bot" under "SCOPES"
3. Select the permissions mentioned above
4. Copy the generated URL
5. Paste it in a browser and select the server you want to add the bot to

## Server Channel Setup

1. Create a dedicated text channel for the bot (e.g., #pain-management-bot)
2. Make sure the bot has permission to send messages in this channel
3. Right-click on the channel and select "Copy ID" (you need Developer Mode enabled in Discord settings)
4. This channel ID will be needed in the app's Discord preferences

## Testing the Bot Connection

You can test if your bot can connect to a specific channel using the included test script:

```
python test_discord_channel.py <channel_id> <bot_token>
```

For example:
```
python test_discord_channel.py 1234567890123456789 your_bot_token_here
```

If successful, you'll see a test message appear in the channel briefly.

## User Setup

Users need to:

1. Go to their profile in the app
2. Navigate to "Discord Preferences"
3. Enter the Channel ID of the Discord channel where they want to receive notifications
4. Enable Discord notifications and save their preferences
5. Click the "Test Discord Connection" button to verify everything is working

## Bot Features

The bot provides the following features:

- Medication reminders sent to the server channel
- Exercise reminders sent to the server channel
- Response tracking for completed/missed medications and exercises
- Respects quiet hours and daily message limits set by users

## Troubleshooting

If the bot isn't working:

1. Verify your bot token is correctly set in the `.env` file
2. Check that the bot has been added to your server
3. Ensure the bot has permission to send messages in the channel
4. Make sure the channel ID is correct (it should be a 17-19 digit number)
5. Run the test script to verify connectivity
6. Check the logs using `docker compose logs discord-bot` 