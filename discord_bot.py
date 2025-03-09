import os
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Load environment variables
load_dotenv()

# Configure database connection
engine = create_engine(os.environ.get('DATABASE_URL'))
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Import models inside functions to avoid circular dependency issues
def get_models():
    from app.models.injury import Injury
    from app.models.user import User, DiscordPreference, SystemSettings
    from app.models.recovery_plan import RecoveryPlan, Medication, Exercise, DiscordInteractionLog, MedicationDose, ExerciseSession
    return {
        'User': User,
        'DiscordPreference': DiscordPreference,
        'SystemSettings': SystemSettings,
        'Injury': Injury,
        'RecoveryPlan': RecoveryPlan,
        'Medication': Medication,
        'Exercise': Exercise,
        'DiscordInteractionLog': DiscordInteractionLog,
        'MedicationDose': MedicationDose,
        'ExerciseSession': ExerciseSession
    }

# Configure Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    # Start background tasks
    check_reminders.start()

@bot.command(name='cleanup')
async def cleanup_command(ctx, user_id=None):
    """Command to clean up bot messages for a user"""
    if not user_id:
        user_id = str(ctx.author.id)
    
    # Only allow this to be run in DMs or by admin users
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("This command can only be used in DMs for privacy reasons.")
        return
    
    await ctx.send("🧹 Starting message cleanup. This may take a moment...")
    count = await delete_user_messages(user_id)
    await ctx.send(f"✅ Cleanup complete! Deleted {count} messages.")

async def delete_user_messages(discord_user_id):
    """Delete all bot DM messages for a specific user"""
    models = get_models()
    
    # Get all logs with message IDs for this user
    logs = db_session.query(models['DiscordInteractionLog']).filter(
        models['DiscordInteractionLog'].discord_user_id == discord_user_id,
        models['DiscordInteractionLog'].discord_message_id != None
    ).all()
    
    deleted_count = 0
    
    try:
        # Fetch the Discord user
        discord_user = await bot.fetch_user(int(discord_user_id))
        dm_channel = await discord_user.create_dm()
        
        print(f"🧹 Starting cleanup for Discord user {discord_user_id}")
        
        for log in logs:
            try:
                # Try to fetch and delete the message
                message = await dm_channel.fetch_message(int(log.discord_message_id))
                await message.delete()
                deleted_count += 1
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.5)
            except discord.errors.NotFound:
                # Message already deleted or not found
                print(f"Message {log.discord_message_id} not found (already deleted)")
            except Exception as e:
                print(f"Error deleting message {log.discord_message_id}: {e}")
        
        print(f"✅ Cleanup complete for {discord_user_id} - Deleted {deleted_count} messages")
        return deleted_count
    except Exception as e:
        print(f"❌ Error in cleanup process: {e}")
        return deleted_count

# Add a command to test direct connection
@bot.command(name='test')
async def test_command(ctx):
    """Test command to verify the bot is working"""
    await ctx.send("The bot is working! You can receive notifications.")

@tasks.loop(minutes=1)  # Check every minute
async def check_reminders():
    """Check for reminders to send every minute"""
    print(f"Checking reminders at {datetime.now()}")
    
    models = get_models()
    
    # First, check for any test messages that need to be sent
    await check_test_messages(models)
    
    # Next, check for any cleanup requests
    await check_cleanup_requests(models)
    
    # Get all active users with Discord preferences enabled
    discord_prefs = db_session.query(models['DiscordPreference']).filter_by(enabled=True).all()
    
    for pref in discord_prefs:
        # Skip if no Discord user ID
        if not pref.discord_user_id:
            continue
            
        # Get user and their active recovery plans
        user = db_session.query(models['User']).get(pref.user_id)
        if not user:
            continue
            
        # Check if user has reached daily limit
        logs_today = db_session.query(models['DiscordInteractionLog']).filter(
            models['DiscordInteractionLog'].user_id == user.id,
            models['DiscordInteractionLog'].timestamp >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        if logs_today >= pref.daily_limit:
            print(f"User {user.username} has reached daily limit of {pref.daily_limit} messages")
            continue
            
        # Check if current time is within quiet hours
        current_time = datetime.now().time()
        in_quiet_hours = False
        
        if pref.quiet_hours_start and pref.quiet_hours_end:
            if pref.quiet_hours_start <= pref.quiet_hours_end:
                # Normal case: quiet_hours_start < quiet_hours_end
                in_quiet_hours = pref.quiet_hours_start <= current_time <= pref.quiet_hours_end
            else:
                # Overnight case: quiet_hours_start > quiet_hours_end
                in_quiet_hours = current_time >= pref.quiet_hours_start or current_time <= pref.quiet_hours_end
                
        if in_quiet_hours:
            print(f"Skipping reminders for {user.username} during quiet hours")
            continue
            
        # Get active recovery plans
        recovery_plans = db_session.query(models['RecoveryPlan']).filter_by(
            user_id=user.id,
            is_active=True
        ).all()
        
        for plan in recovery_plans:
            # Check medications
            await check_medications(user, plan, pref, models)
            
            # Check exercises
            await check_exercises(user, plan, pref, models)

async def check_test_messages(models):
    """Check for test messages and send them immediately"""
    # Get any system messages that haven't been processed yet
    test_logs = db_session.query(models['DiscordInteractionLog']).filter(
        models['DiscordInteractionLog'].message_type == 'system',
        models['DiscordInteractionLog'].completed == False
    ).all()
    
    if test_logs:
        print("\n===== PROCESSING TEST MESSAGES =====")
        
    for log in test_logs:
        try:
            # Get user information
            user = db_session.query(models['User']).get(log.user_id)
            username = user.username if user else "Unknown User"
            
            # Get user's Discord preferences
            discord_prefs = db_session.query(models['DiscordPreference']).filter_by(user_id=log.user_id).first()
            message_mode = 'both'  # Default to both if no preference exists
            
            if discord_prefs:
                message_mode = discord_prefs.message_mode
            
            print(f"🔔 TEST CONNECTION: Sending test message to {username} (Discord ID: {log.discord_user_id})")
            print(f"Message delivery mode: {message_mode}")
            
            # Fetch the Discord user
            discord_user = await bot.fetch_user(int(log.discord_user_id))
            
            # Send direct message if mode is 'dm' or 'both'
            if message_mode in ['dm', 'both']:
                dm_channel = await discord_user.create_dm()
                sent_message = await dm_channel.send(log.sent_message)
                
                # Store the message ID for potential deletion later
                log.discord_message_id = str(sent_message.id)
                
                # Send a follow-up confirmation message
                confirm_message = await dm_channel.send("✅ **Test Connection Successful!**\nYour Discord connection is working correctly. You will now receive notifications from the Pain Management App.")
                
                # Create additional log for the confirmation message
                confirm_log = models['DiscordInteractionLog'](
                    user_id=log.user_id,
                    discord_user_id=log.discord_user_id,
                    message_type='system',
                    sent_message="✅ **Test Connection Successful!**\nYour Discord connection is working correctly. You will now receive notifications from the Pain Management App.",
                    timestamp=datetime.now(),
                    completed=True,
                    discord_message_id=str(confirm_message.id)
                )
                db_session.add(confirm_log)
                
                print(f"✅ Direct message sent to {username}")
            
            # Try to send to a shared server channel if mode is 'channel' or 'both'
            if message_mode in ['channel', 'both']:
                try:
                    # Look for shared servers with the user
                    shared_servers = discord_user.mutual_guilds
                    
                    if shared_servers:
                        # Use the first shared server
                        guild = shared_servers[0]
                        
                        # Look for a general, bot, or test channel (common names)
                        target_channel = None
                        channel_names = ['general', 'bot', 'bots', 'bot-commands', 'test', 'chat']
                        
                        for channel in guild.text_channels:
                            if channel.permissions_for(guild.me).send_messages:
                                # First check if any channel has a matching name
                                if any(name in channel.name.lower() for name in channel_names):
                                    target_channel = channel
                                    break
                        
                        # If no named channel found, use the first channel where we can send messages
                        if not target_channel:
                            for channel in guild.text_channels:
                                if channel.permissions_for(guild.me).send_messages:
                                    target_channel = channel
                                    break
                        
                        if target_channel:
                            # Send message to the server channel
                            server_message = f"**Test Message for {username}**\n\nHello! This is a test message to verify that the Pain Management App Discord bot is working correctly in this server. <@{log.discord_user_id}> requested this test."
                            sent_server_message = await target_channel.send(server_message)
                            
                            # Create a log for the server message
                            server_log = models['DiscordInteractionLog'](
                                user_id=log.user_id,
                                discord_user_id=log.discord_user_id,
                                message_type='system',
                                sent_message=server_message,
                                timestamp=datetime.now(),
                                completed=True,
                                discord_message_id=str(sent_server_message.id)
                            )
                            db_session.add(server_log)
                            
                            print(f"✅ Server channel message sent to #{target_channel.name} in {guild.name}")
                        else:
                            print(f"⚠️ Could not find a suitable channel to send a message in {guild.name}")
                    else:
                        print(f"⚠️ No shared servers found with user {username}")
                except Exception as channel_error:
                    print(f"⚠️ Error sending to server channel: {channel_error}")
                    # We don't want to fail the whole test if server message fails
                    # Just log it and continue
            
            # Update the log
            log.response = f"Delivered (mode: {message_mode})"
            log.response_time = datetime.now()
            log.completed = True
            db_session.commit()
            
            print(f"✅ TEST CONNECTION SUCCESSFUL: Message(s) delivered to {username} (Discord ID: {log.discord_user_id})")
            print(f"Time: {datetime.now()}")
            
        except Exception as e:
            print(f"❌ TEST CONNECTION FAILED: Error sending test message to Discord user {log.discord_user_id}")
            print(f"Error details: {e}")
            # Update the log with the error
            log.response = f"Error: {str(e)}"
            log.response_time = datetime.now()
            log.completed = True
            db_session.commit()
    
    if test_logs:
        print("===== TEST MESSAGES PROCESSING COMPLETE =====\n")

async def check_medications(user, plan, pref, models):
    """Check if any medications need reminders"""
    medications = db_session.query(models['Medication']).filter_by(
        recovery_plan_id=plan.id,
        is_active=True,
        discord_notifications=True
    ).all()
    
    for med in medications:
        # Skip if medication is not active or not due
        if not is_medication_due(med):
            continue
            
        # Check if we've already sent a reminder recently
        recent_log = db_session.query(models['DiscordInteractionLog']).filter(
            models['DiscordInteractionLog'].user_id == user.id,
            models['DiscordInteractionLog'].medication_id == med.id,
            models['DiscordInteractionLog'].timestamp >= datetime.now() - timedelta(hours=1)
        ).first()
        
        if recent_log:
            continue
            
        # Send reminder
        try:
            message = f"**Medication Reminder**\n\nIt's time to take your medication: **{med.name}** ({med.dosage})\n\nInstructions: {med.instructions or 'None provided'}\n\nHave you taken this medication? Reply with YES or NO."
            
            # Get the message mode preference
            message_mode = pref.message_mode if hasattr(pref, 'message_mode') else 'both'
            
            # Create log entry first (we'll update message ID later)
            log = models['DiscordInteractionLog'](
                user_id=user.id,
                discord_user_id=pref.discord_user_id,
                message_type='medication',
                medication_id=med.id,
                sent_message=message,
                timestamp=datetime.now(),
                completed=False
            )
            db_session.add(log)
            db_session.commit()
            
            # Handle DM delivery if enabled
            if message_mode in ['dm', 'both']:
                discord_user = await bot.fetch_user(int(pref.discord_user_id))
                dm_channel = await discord_user.create_dm()
                sent_message = await dm_channel.send(message)
                
                # Store message ID
                log.discord_message_id = str(sent_message.id)
                db_session.commit()
                
                print(f"Sent medication reminder DM to {user.username} for {med.name}")
            
            # Handle server channel delivery if enabled
            if message_mode in ['channel', 'both']:
                try:
                    discord_user = await bot.fetch_user(int(pref.discord_user_id))
                    shared_servers = discord_user.mutual_guilds
                    
                    if shared_servers:
                        # Use the first shared server
                        guild = shared_servers[0]
                        
                        # Look for a general, bot, or test channel
                        target_channel = None
                        channel_names = ['general', 'bot', 'bots', 'bot-commands', 'test', 'chat']
                        
                        for channel in guild.text_channels:
                            if channel.permissions_for(guild.me).send_messages:
                                if any(name in channel.name.lower() for name in channel_names):
                                    target_channel = channel
                                    break
                        
                        # If no named channel found, use the first channel where we can send messages
                        if not target_channel:
                            for channel in guild.text_channels:
                                if channel.permissions_for(guild.me).send_messages:
                                    target_channel = channel
                                    break
                        
                        if target_channel:
                            # Send message to the server channel
                            server_message = f"**Medication Reminder for {user.username}**\n\n<@{pref.discord_user_id}>, it's time to take your medication: **{med.name}** ({med.dosage})\n\nPlease check your Direct Messages to respond to this reminder."
                            sent_message = await target_channel.send(server_message)
                            
                            # Create a log for the server message
                            server_log = models['DiscordInteractionLog'](
                                user_id=user.id,
                                discord_user_id=pref.discord_user_id,
                                message_type='medication',
                                medication_id=med.id,
                                sent_message=server_message,
                                timestamp=datetime.now(),
                                completed=True,
                                discord_message_id=str(sent_message.id)
                            )
                            db_session.add(server_log)
                            db_session.commit()
                            
                            print(f"Sent medication reminder to server channel for {user.username}")
                except Exception as channel_error:
                    print(f"Error sending to server channel: {channel_error}")
                    # Continue even if server message fails
            
            print(f"Logged medication reminder for {user.username} for {med.name}")
        except Exception as e:
            print(f"Error sending medication reminder: {e}")

async def check_exercises(user, plan, pref, models):
    """Check if any exercises need reminders"""
    exercises = db_session.query(models['Exercise']).filter_by(
        recovery_plan_id=plan.id,
        is_active=True,
        discord_notifications=True
    ).all()
    
    for exercise in exercises:
        # Skip if exercise is not active or not due
        if not is_exercise_due(exercise):
            continue
            
        # Check if we've already sent a reminder recently
        recent_log = db_session.query(models['DiscordInteractionLog']).filter(
            models['DiscordInteractionLog'].user_id == user.id,
            models['DiscordInteractionLog'].exercise_id == exercise.id,
            models['DiscordInteractionLog'].timestamp >= datetime.now() - timedelta(hours=1)
        ).first()
        
        if recent_log:
            continue
            
        # Send reminder
        try:
            message = f"**Exercise Reminder**\n\nIt's time for your exercise: **{exercise.name}**\n\nDetails: {exercise.description or 'None provided'}\nDuration: {exercise.duration or 'Not specified'}\nRepetitions: {exercise.repetitions or 'Not specified'}\n\nInstructions: {exercise.instructions or 'None provided'}\n\nHave you completed this exercise? Reply with YES or NO."
            
            # Get the message mode preference
            message_mode = pref.message_mode if hasattr(pref, 'message_mode') else 'both'
            
            # Create log entry first (we'll update message ID later)
            log = models['DiscordInteractionLog'](
                user_id=user.id,
                discord_user_id=pref.discord_user_id,
                message_type='exercise',
                exercise_id=exercise.id,
                sent_message=message,
                timestamp=datetime.now(),
                completed=False
            )
            db_session.add(log)
            db_session.commit()
            
            # Handle DM delivery if enabled
            if message_mode in ['dm', 'both']:
                discord_user = await bot.fetch_user(int(pref.discord_user_id))
                dm_channel = await discord_user.create_dm()
                sent_message = await dm_channel.send(message)
                
                # Store message ID
                log.discord_message_id = str(sent_message.id)
                db_session.commit()
                
                print(f"Sent exercise reminder DM to {user.username} for {exercise.name}")
            
            # Handle server channel delivery if enabled
            if message_mode in ['channel', 'both']:
                try:
                    discord_user = await bot.fetch_user(int(pref.discord_user_id))
                    shared_servers = discord_user.mutual_guilds
                    
                    if shared_servers:
                        # Use the first shared server
                        guild = shared_servers[0]
                        
                        # Look for a general, bot, or test channel
                        target_channel = None
                        channel_names = ['general', 'bot', 'bots', 'bot-commands', 'test', 'chat']
                        
                        for channel in guild.text_channels:
                            if channel.permissions_for(guild.me).send_messages:
                                if any(name in channel.name.lower() for name in channel_names):
                                    target_channel = channel
                                    break
                        
                        # If no named channel found, use the first channel where we can send messages
                        if not target_channel:
                            for channel in guild.text_channels:
                                if channel.permissions_for(guild.me).send_messages:
                                    target_channel = channel
                                    break
                        
                        if target_channel:
                            # Send message to the server channel
                            server_message = f"**Exercise Reminder for {user.username}**\n\n<@{pref.discord_user_id}>, it's time for your exercise: **{exercise.name}**\n\nPlease check your Direct Messages to respond to this reminder."
                            sent_message = await target_channel.send(server_message)
                            
                            # Create a log for the server message
                            server_log = models['DiscordInteractionLog'](
                                user_id=user.id,
                                discord_user_id=pref.discord_user_id,
                                message_type='exercise',
                                exercise_id=exercise.id,
                                sent_message=server_message,
                                timestamp=datetime.now(),
                                completed=True,
                                discord_message_id=str(sent_message.id)
                            )
                            db_session.add(server_log)
                            db_session.commit()
                            
                            print(f"Sent exercise reminder to server channel for {user.username}")
                except Exception as channel_error:
                    print(f"Error sending to server channel: {channel_error}")
                    # Continue even if server message fails
            
            print(f"Logged exercise reminder for {user.username} for {exercise.name}")
        except Exception as e:
            print(f"Error sending exercise reminder: {e}")

def is_medication_due(medication):
    """Check if a medication is due based on its frequency"""
    # This is a simplified implementation
    # In a real application, you would need more sophisticated logic
    # based on the medication frequency and last dose
    return True

def is_exercise_due(exercise):
    """Check if an exercise is due based on its frequency"""
    # This is a simplified implementation
    # In a real application, you would need more sophisticated logic
    # based on the exercise frequency and last session
    return True

@bot.event
async def on_message(message):
    """Handle direct message responses"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
        
    # Only process direct messages
    if not isinstance(message.channel, discord.DMChannel):
        return
        
    # Find the most recent unanswered interaction for this user
    try:
        discord_user_id = str(message.author.id)
        models = get_models()
        
        # Find the user by Discord ID
        discord_pref = db_session.query(models['DiscordPreference']).filter_by(
            discord_user_id=discord_user_id,
            enabled=True
        ).first()
        
        if not discord_pref:
            await message.channel.send("I don't recognize you. Please set up your Discord preferences in the Pain Management App.")
            return
            
        # Find the most recent unanswered interaction
        log = db_session.query(models['DiscordInteractionLog']).filter(
            models['DiscordInteractionLog'].discord_user_id == discord_user_id,
            models['DiscordInteractionLog'].completed == False
        ).order_by(models['DiscordInteractionLog'].timestamp.desc()).first()
        
        if not log:
            await message.channel.send("I don't have any pending reminders for you. You can manage your recovery plan in the Pain Management App.")
            return
            
        # Process the response
        response_text = message.content.strip().upper()
        log.response = response_text
        log.response_time = datetime.now()
        
        if response_text in ['YES', 'Y']:
            log.completed = True
            
            if log.message_type == 'medication':
                # Record medication dose
                dose = models['MedicationDose'](
                    medication_id=log.medication_id,
                    taken=True,
                    timestamp=datetime.now(),
                    response_time=datetime.now()
                )
                db_session.add(dose)
                await message.channel.send("Great! I've recorded that you've taken your medication.")
                
            elif log.message_type == 'exercise':
                # Record exercise session
                session = models['ExerciseSession'](
                    exercise_id=log.exercise_id,
                    completed=True,
                    timestamp=datetime.now(),
                    response_time=datetime.now()
                )
                db_session.add(session)
                await message.channel.send("Great! I've recorded that you've completed your exercise.")
                
        elif response_text in ['NO', 'N']:
            log.completed = True
            
            if log.message_type == 'medication':
                # Record skipped medication
                dose = models['MedicationDose'](
                    medication_id=log.medication_id,
                    taken=False,
                    timestamp=datetime.now(),
                    response_time=datetime.now()
                )
                db_session.add(dose)
                await message.channel.send("I've recorded that you haven't taken your medication. Remember that following your medication schedule is important for your recovery.")
                
            elif log.message_type == 'exercise':
                # Record skipped exercise
                session = models['ExerciseSession'](
                    exercise_id=log.exercise_id,
                    completed=False,
                    timestamp=datetime.now(),
                    response_time=datetime.now()
                )
                db_session.add(session)
                await message.channel.send("I've recorded that you haven't completed your exercise. Remember that following your exercise routine is important for your recovery.")
                
        else:
            await message.channel.send("I didn't understand your response. Please reply with YES or NO.")
            return
            
        db_session.commit()
        
    except Exception as e:
        print(f"Error processing message: {e}")
        await message.channel.send("Sorry, there was an error processing your response. Please try again later.")

    # Process commands
    await bot.process_commands(message)

async def check_cleanup_requests(models):
    """Check for any requests to clean up bot messages"""
    # Get any cleanup requests that haven't been processed yet
    cleanup_logs = db_session.query(models['DiscordInteractionLog']).filter(
        models['DiscordInteractionLog'].message_type == 'cleanup',
        models['DiscordInteractionLog'].completed == False
    ).all()
    
    if cleanup_logs:
        print("\n===== PROCESSING CLEANUP REQUESTS =====")
        
    for log in cleanup_logs:
        try:
            # Get user information
            user = db_session.query(models['User']).get(log.user_id)
            username = user.username if user else "Unknown User"
            
            print(f"🧹 CLEANUP REQUEST: Processing cleanup for {username} (Discord ID: {log.discord_user_id})")
            
            # Delete the messages
            deleted_count = await delete_user_messages(log.discord_user_id)
            
            # Update the log
            log.response = f"Completed - Deleted {deleted_count} messages"
            log.response_time = datetime.now()
            log.completed = True
            db_session.commit()
            
            # Send a confirmation message
            try:
                discord_user = await bot.fetch_user(int(log.discord_user_id))
                dm_channel = await discord_user.create_dm()
                confirmation = await dm_channel.send(f"✅ **Message Cleanup Complete**\n\nI've deleted {deleted_count} messages from our conversation. If you want to permanently delete all message history, you can also delete this conversation from your Discord client.")
                
                # We need to log this message too so it can be deleted in future cleanup requests
                confirm_log = models['DiscordInteractionLog'](
                    user_id=log.user_id,
                    discord_user_id=log.discord_user_id,
                    message_type='system',
                    sent_message="Cleanup confirmation message",
                    timestamp=datetime.now(),
                    completed=True,
                    discord_message_id=str(confirmation.id)
                )
                db_session.add(confirm_log)
                db_session.commit()
            except Exception as e:
                print(f"Error sending cleanup confirmation: {e}")
            
            print(f"✅ CLEANUP COMPLETE: Deleted {deleted_count} messages for {username} (Discord ID: {log.discord_user_id})")
            print(f"Time: {datetime.now()}")
            
        except Exception as e:
            print(f"❌ CLEANUP FAILED: Error cleaning up messages for Discord user {log.discord_user_id}")
            print(f"Error details: {e}")
            # Update the log with the error
            log.response = f"Error: {str(e)}"
            log.response_time = datetime.now()
            log.completed = True
            db_session.commit()
    
    if cleanup_logs:
        print("===== CLEANUP REQUESTS PROCESSING COMPLETE =====\n")

if __name__ == '__main__':
    bot.run(os.environ.get('DISCORD_BOT_TOKEN')) 