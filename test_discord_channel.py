#!/usr/bin/env python3
"""
Discord Channel Connection Test Script

This script tests the connection to a Discord channel by sending a test message.
Usage: python test_discord_channel.py <channel_id> <bot_token>
"""

import sys
import asyncio
import discord
from datetime import datetime

async def test_channel_connection(channel_id, token):
    """Test sending a message to a specific Discord channel"""
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        try:
            print(f"Logged in as {client.user.name} ({client.user.id})")
            print(f"Testing connection to channel ID: {channel_id}")
            
            # Try to get the channel
            channel = client.get_channel(int(channel_id))
            
            if not channel:
                # If get_channel fails, try fetch_channel
                try:
                    channel = await client.fetch_channel(int(channel_id))
                except discord.errors.NotFound:
                    print("❌ Error: Channel not found! Please check the channel ID.")
                    await client.close()
                    return
                except discord.errors.Forbidden:
                    print("❌ Error: Bot doesn't have permission to access this channel!")
                    await client.close()
                    return
            
            # Verify channel type
            if not isinstance(channel, discord.TextChannel):
                print(f"❌ Error: The provided ID is not a text channel (it's a {type(channel).__name__}).")
                await client.close()
                return
            
            # Verify permissions
            permissions = channel.permissions_for(channel.guild.me)
            if not permissions.send_messages:
                print("❌ Error: Bot doesn't have permission to send messages in this channel!")
                await client.close()
                return
            
            # Send test message
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = await channel.send(f"**This is a test of the bot connection** ⏰ {timestamp}\nYour Discord channel is now connected to the Pain Management App.")
            
            print(f"✅ Success! Test message sent to channel '{channel.name}' in server '{channel.guild.name}'")
            print(f"Message ID: {message.id}")
            
            # Wait a bit and then delete the message
            await asyncio.sleep(3)
            await message.delete()
            print("Test message deleted.")
            
        except Exception as e:
            print(f"❌ Error testing channel connection: {e}")
        
        # Close the client connection
        await client.close()
    
    # Start the client
    await client.start(token)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_discord_channel.py <channel_id> <bot_token>")
        sys.exit(1)
    
    channel_id = sys.argv[1]
    token = sys.argv[2]
    
    # Validate channel_id format
    if not channel_id.isdigit() or len(channel_id) < 17 or len(channel_id) > 19:
        print("❌ Error: Channel ID must be a 17-19 digit number.")
        sys.exit(1)
    
    # Run the test
    print(f"Testing Discord channel connection to channel ID: {channel_id}")
    asyncio.run(test_channel_connection(channel_id, token)) 