# Discord Bot Changes

## Overview

The Discord bot has been updated to:

1. Remove all direct messaging functionality
2. Add support for server channels only
3. Update the frequency fields to use numeric values for better scheduling
4. Improve reminder handling for recurring reminders

## Database Schema Changes

### DiscordPreference Model

- Removed `discord_user_id` - No longer needed since we're not sending direct messages
- Removed `message_mode` - No longer needed since we're only using server channels
- Added `discord_channel_id` - To store the server channel ID where messages will be sent

### Medication and Exercise Models

- Changed `frequency` from string to integer (hours)
- Added better support for longer frequencies (weekly, bi-weekly, monthly)

## Form Changes

### DiscordPreferenceForm

- Replaced Discord User ID field with Channel ID field
- Removed message delivery method options

### Medication and Exercise Forms

- Updated frequency selection to use numeric values
- Added clearer descriptions for frequency options

## Discord Bot Changes

- Removed all code related to direct messages
- Added support for server channel messaging
- Added better timezone handling
- Improved recurring reminder logic
- Added proper follow-up for missed reminders

## Testing and Deployment

- Added a test script to verify channel connectivity (`test_discord_channel.py`)
- Added a rebuild script to apply database changes (`rebuild_discord_bot.sh`)
- Updated documentation with new setup instructions

## Migration

A database migration has been created to:

1. Remove deprecated columns
2. Add new columns
3. Convert string frequency values to integer hour values
4. Update existing data to fit the new schema

## How to Apply Changes

Run the rebuild script to apply all changes:

```
./rebuild_discord_bot.sh
```

This will:
1. Stop all containers
2. Remove the volumes to clean the database
3. Rebuild the containers with the new code
4. Apply the database migrations

## User Instructions

Users need to:

1. Update their Discord preferences to add a Server Channel ID
2. Re-enable Discord notifications if desired
3. Test the connection to verify it's working 