# Discord Bot Setup for Pain Management App

This guide will help you set up the Discord bot integration for the Pain Management App.

## Prerequisites

- A Discord account
- Access to the Discord Developer Portal
- The Pain Management App running

## Step 1: Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "Pain Management Bot")
3. Click "Create"

## Step 2: Set Up the Bot

1. In your application, go to the "Bot" tab
2. Click "Add Bot"
3. Under the "Privileged Gateway Intents" section, enable:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
4. Click "Save Changes"
5. Under the "TOKEN" section, click "Reset Token" and copy the new token
   - This is your `DISCORD_BOT_TOKEN` for the .env file

## Step 3: Configure Bot Permissions

1. Go to the "OAuth2" tab
2. In the "URL Generator" section, select the following scopes:
   - `bot`
   - `applications.commands`
3. Under "Bot Permissions", select:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions
4. Copy the generated URL at the bottom of the page
   - This is your `DISCORD_INVITE_URL` for the .env file

## Step 4: Update Environment Variables

Add the following variables to your `.env` file:

```
# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_APPLICATION_ID=your_application_id_from_general_information_tab
DISCORD_PUBLIC_KEY=your_public_key_from_general_information_tab
DISCORD_BOT_PERMISSIONS=274878221312  # The permissions integer from the URL generator
DISCORD_INVITE_URL=https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=YOUR_PERMISSIONS&scope=bot%20applications.commands
```

## Step 5: Run the Discord Bot

The Discord bot runs as a separate process from the main application:

```bash
python discord_bot.py
```

For production, you should set up the bot to run as a service or using a process manager like Supervisor.

## Step 6: Configure in Admin Panel

1. Log in to the Pain Management App as an admin
2. Go to "System Settings"
3. Enter the Discord Bot Invite URL (the same as `DISCORD_INVITE_URL` in your .env file)
4. Click "Save Settings"

## Step 7: User Setup

Users need to:

1. Click the "Add Bot to Discord Server" button in their Discord Preferences
2. Authorize the bot for their server
3. Find their Discord User ID:
   - Enable Developer Mode in Discord (Settings > Advanced > Developer Mode)
   - Right-click on their username and select "Copy ID"
4. Enter their Discord User ID in the Discord Preferences page
5. Configure their notification preferences

## Bot Commands

The bot currently supports the following interactions:

- Responding to medication reminders with "YES" or "NO"
- Responding to exercise reminders with "YES" or "NO"

## Troubleshooting

- **Bot not responding**: Make sure the bot is running and has the correct token
- **Can't add bot to server**: Verify the invite URL is correct and you have the necessary permissions
- **Not receiving messages**: Check that your Discord User ID is correct and you have DMs enabled for the server

## Security Considerations

- Keep your bot token secure and never commit it to version control
- The bot only needs the minimum permissions required to function
- User data is stored securely in the application database 