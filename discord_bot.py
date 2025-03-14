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

# Import models
from app.models.injury import Injury
from app.models.user import User, DiscordPreference, SystemSettings
from app.models.recovery_plan import RecoveryPlan, Medication, Exercise, DiscordInteractionLog, MedicationDose, ExerciseSession

# Import models inside functions to avoid circular dependency issues
def get_models():
    return {
        'Injury': Injury,
        'User': User,
        'DiscordPreference': DiscordPreference,
        'SystemSettings': SystemSettings,
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

@bot.command(name='test')
async def test_command(ctx):
    """Test command to verify the bot is working"""
    await ctx.send("Bot is working! 👋")

@tasks.loop(minutes=1)  # Check every minute
async def check_reminders():
    """Background task to check for pending reminders"""
    try:
        now = datetime.utcnow()
        print(f"\n⏰ check_reminders task running at {now}")
        models = get_models()
        
        # Check for test messages first
        await check_test_messages(models)
        
        # Get all active users with Discord preferences
        users = db_session.query(models['User']).join(
            models['DiscordPreference'],
            models['User'].id == models['DiscordPreference'].user_id
        ).filter(
            models['DiscordPreference'].enabled == True,
            models['DiscordPreference'].discord_channel_id != None
        ).all()
        
        print(f"👥 Found {len(users)} users with active Discord preferences")
        
        # Print detailed info for each user
        for user in users:
            pref = user.discord_preferences
            print(f"  - User {user.username} (ID: {user.id}): Channel ID: {pref.discord_channel_id}, TimeZone: {pref.time_zone}, Daily Limit: {pref.daily_limit}")
            
            # Get active recovery plans
            plans = db_session.query(models['RecoveryPlan']).filter(
                models['RecoveryPlan'].user_id == user.id,
                models['RecoveryPlan'].is_active == True
            ).all()
            
            print(f"    Has {len(plans)} active recovery plans")
            
            for plan in plans:
                # Get medications with discord notifications enabled
                medications = db_session.query(models['Medication']).filter(
                    models['Medication'].recovery_plan_id == plan.id,
                    models['Medication'].is_active == True,
                    models['Medication'].discord_notifications == True
                ).all()
                
                # Get exercises with discord notifications enabled
                exercises = db_session.query(models['Exercise']).filter(
                    models['Exercise'].recovery_plan_id == plan.id,
                    models['Exercise'].is_active == True,
                    models['Exercise'].discord_notifications == True
                ).all()
                
                print(f"    - Plan {plan.name} (ID: {plan.id}): {len(medications)} medications, {len(exercises)} exercises with Discord notifications")
        
        for user in users:
            try:
                # Get user preferences
                pref = user.discord_preferences
                
                # Skip if no discord channel ID
                if not pref.discord_channel_id:
                    print(f"⚠️ User {user.id} has no Discord channel ID set")
                    continue
                
                print(f"👤 Processing user {user.username} (ID: {user.id}) with channel ID: {pref.discord_channel_id}")
                
                # Check quiet hours
                user_now = convert_timezone(now, pref.time_zone)
                if is_quiet_hours(user_now, pref):
                    print(f"🌙 Quiet hours active for user {user.id} - skipping")
                    continue
                
                # Check daily limit
                today_start = user_now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_start_utc = convert_to_utc(today_start, pref.time_zone)
                
                sent_today = db_session.query(models['DiscordInteractionLog']).filter(
                    models['DiscordInteractionLog'].user_id == user.id,
                    models['DiscordInteractionLog'].timestamp >= today_start_utc
                ).count()
                
                print(f"📊 User {user.id} has received {sent_today}/{pref.daily_limit} notifications today")
                
                if sent_today >= pref.daily_limit:
                    print(f"⚠️ Daily limit reached for user {user.id} - skipping")
                    continue
                
                # Get active recovery plans
                plans = db_session.query(models['RecoveryPlan']).filter(
                    models['RecoveryPlan'].user_id == user.id,
                    models['RecoveryPlan'].is_active == True
                ).all()
                
                print(f"📋 Found {len(plans)} active recovery plans for user {user.id}")
                
                for plan in plans:
                    print(f"📌 Processing plan: {plan.name} (ID: {plan.id})")
                    # Check medications
                    await check_medications(user, plan, pref, models)
                    
                    # Check exercises
                    await check_exercises(user, plan, pref, models)
            
            except Exception as e:
                print(f"❌ Error processing user {user.id}: {e}")
                continue
        
    except Exception as e:
        print(f"❌ Error in check_reminders: {e}")
    
    finally:
        db_session.remove()

async def check_test_messages(models):
    """Check for test connection messages"""
    print(f"🔍 Checking for test messages at {datetime.utcnow()}")
    
    test_logs = db_session.query(models['DiscordInteractionLog']).filter(
        models['DiscordInteractionLog'].message_type == 'test',
        models['DiscordInteractionLog'].response_time == None
    ).all()
    
    print(f"📋 Found {len(test_logs)} pending test messages")
    
    for log in test_logs:
        try:
            print(f"📝 Processing test message id={log.id} for user_id={log.user_id}")
            
            # Skip if no discord_channel_id
            if not hasattr(log, 'discord_channel_id') or not log.discord_channel_id:
                print(f"⚠️ No discord_channel_id for log id={log.id}, available attributes: {dir(log)}")
                continue
            
            user = db_session.query(models['User']).filter(
                models['User'].id == log.user_id
            ).first()
            
            if not user:
                print(f"⚠️ User not found for user_id={log.user_id}")
                continue
                
            print(f"👤 Found user {user.username} (id={user.id})")
            
            pref = user.discord_preferences
            
            # Skip if no discord_channel_id
            if not pref or not pref.discord_channel_id:
                print(f"⚠️ No discord_channel_id in user preferences for user {user.username}")
                continue
            
            print(f"🔗 Using Discord channel ID: {pref.discord_channel_id}")
            
            # Attempt to get the channel
            try:
                target_channel = await bot.fetch_channel(int(pref.discord_channel_id))
                print(f"🎯 Found channel {target_channel.name} in server {target_channel.guild.name}")
                
                # Send the test message to the channel
                server_message = "**This is a test of the bot connection**\nYour Discord channel is now connected to the Pain Management App."
                
                # If this is for a specific medication or exercise, include details
                if hasattr(log, 'medication_id') and log.medication_id:
                    med = db_session.query(models['Medication']).get(log.medication_id)
                    if med:
                        plan = db_session.query(models['RecoveryPlan']).get(med.recovery_plan_id)
                        server_message = f"**Medication Reminder TEST**\n\n📋 Plan: {plan.name}\n📋 {med.name}\n💊 Dosage: {med.dosage}\n⏰ Every {med.frequency} hours\n\n{med.instructions if med.instructions else ''}\n\nThis is a TEST message. No response is required."
                
                elif hasattr(log, 'exercise_id') and log.exercise_id:
                    ex = db_session.query(models['Exercise']).get(log.exercise_id)
                    if ex:
                        plan = db_session.query(models['RecoveryPlan']).get(ex.recovery_plan_id)
                        details = []
                        if hasattr(ex, 'duration') and ex.duration:
                            details.append(f"⏱️ Duration: {ex.duration}")
                        if hasattr(ex, 'repetitions') and ex.repetitions:
                            details.append(f"🔄 Repetitions: {ex.repetitions}")
                        
                        details_str = "\n".join(details) if details else ""
                        server_message = f"**Exercise Reminder TEST**\n\n📋 Plan: {plan.name}\n🏋️ {ex.name}\n{details_str}\n⏰ Every {ex.frequency} hours\n\n{ex.instructions if ex.instructions else ''}\n\nThis is a TEST message. No response is required."
                
                print(f"📤 Sending test message to channel")
                sent_server_message = await target_channel.send(server_message)
                
                # Update the log
                log.response_time = datetime.utcnow()
                log.completed = True
                log.discord_message_id = str(sent_server_message.id)
                db_session.commit()
                
                print(f"✅ Test message sent to channel {pref.discord_channel_id} for user {user.id}, message ID: {sent_server_message.id}")
                
            except Exception as e:
                print(f"❌ Error sending test message to channel: {e}")
                # Don't mark as completed so it can be retried
        
        except Exception as e:
            print(f"❌ Error processing test log {log.id}: {e}")
            continue

def is_quiet_hours(user_time, preferences):
    """Check if current time is within quiet hours"""
    if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
        return False
    
    current_time = user_time.time()
    start = preferences.quiet_hours_start
    end = preferences.quiet_hours_end
    
    if start <= end:
        return start <= current_time <= end
    else:  # Handles overnight quiet hours (e.g., 22:00 to 07:00)
        return start <= current_time or current_time <= end

def convert_timezone(dt, timezone_str):
    """Convert a datetime from UTC to the specified timezone"""
    if not timezone_str:
        return dt
    
    try:
        utc = pytz.UTC
        user_tz = pytz.timezone(timezone_str)
        
        # Make datetime aware of UTC timezone
        dt_aware = utc.localize(dt)
        
        # Convert to user's timezone
        return dt_aware.astimezone(user_tz)
    except Exception as e:
        print(f"Error converting timezone: {e}")
        return dt

def convert_to_utc(dt, timezone_str):
    """Convert a datetime to UTC"""
    try:
        # If the datetime already has a timezone, skip this conversion
        if dt.tzinfo is not None:
            print(f"Warning: convert_to_utc received a non-naive datetime - returning as is")
            return dt
            
        # Get the timezone
        tz = pytz.timezone(timezone_str)
        
        # Localize the datetime
        dt_with_tz = tz.localize(dt)
        
        # Convert to UTC
        utc_dt = dt_with_tz.astimezone(pytz.UTC)
        
        # Return a naive datetime in UTC
        return utc_dt.replace(tzinfo=None)
    except Exception as e:
        print(f"Error converting to UTC: {e}")
        return dt  # Return the original datetime as a fallback

async def check_medications(user, plan, pref, models):
    """Check if user has any medications due for reminders"""
    try:
        # Get medications with discord notifications enabled
        medications = db_session.query(models['Medication']).filter(
            models['Medication'].recovery_plan_id == plan.id,
            models['Medication'].is_active == True,
            models['Medication'].discord_notifications == True
        ).all()
        
        print(f"💊 Found {len(medications)} medications with Discord notifications in plan {plan.id}")
        
        for med in medications:
            print(f"🔍 Checking medication: {med.name} (ID: {med.id}, Frequency: {med.frequency} hours)")
            
            # Check if medication should be sent based on reminder frequency
            should_send, reason = should_send_reminder(user.id, med.id, 'medication', med.frequency)
            
            if not should_send:
                print(f"⏳ Skipping medication {med.name}: {reason}")
                continue
            
            print(f"✅ Medication {med.name} is due for a reminder")
            
            # Attempt to get the channel
            try:
                target_channel = await bot.fetch_channel(int(pref.discord_channel_id))
                
                # Calculate scheduled time based on frequency and last dose
                now = datetime.utcnow()
                scheduled_time = now
                
                # Try to find the most recent dose or reminder to calculate the scheduled time
                last_reminder = db_session.query(models['DiscordInteractionLog']).filter(
                    models['DiscordInteractionLog'].user_id == user.id,
                    models['DiscordInteractionLog'].medication_id == med.id,
                    models['DiscordInteractionLog'].message_type == 'medication'
                ).order_by(models['DiscordInteractionLog'].timestamp.desc()).first()
                
                if last_reminder:
                    # Calculate based on the last reminder plus the frequency
                    scheduled_time = last_reminder.timestamp + timedelta(hours=med.frequency)
                
                # Convert to user's timezone
                user_scheduled_time = convert_timezone(scheduled_time, pref.time_zone)
                formatted_time = user_scheduled_time.strftime('%I:%M %p on %b %d, %Y')
                
                # Prepare the message with scheduled time
                message = f"**Medication Reminder**\n\n📋 Plan: {plan.name}\n📋 {med.name}\n💊 Dosage: {med.dosage}\n⏰ Every {med.frequency} hours\n\n{med.instructions if med.instructions else ''}\n\n⏰ Your scheduled time to take medication is {formatted_time}\n\nPlease reply with **YES** if you've taken this medication, or **NO** if you haven't."
                
                # Send the message
                sent_message = await target_channel.send(message)
                
                # Log the interaction with scheduled time
                log = models['DiscordInteractionLog'](
                    user_id=user.id,
                    discord_channel_id=pref.discord_channel_id,
                    message_type='medication',
                    medication_id=med.id,
                    sent_message=message,
                    timestamp=datetime.utcnow(),
                    discord_message_id=str(sent_message.id),
                    scheduled_time=scheduled_time  # Store scheduled time for reference
                )
                db_session.add(log)
                db_session.commit()
                
                print(f"📩 Sent medication reminder for {med.name} to channel {pref.discord_channel_id}")
                
            except Exception as e:
                print(f"❌ Error sending medication reminder: {e}")
        
    except Exception as e:
        print(f"❌ Error checking medications: {e}")

async def check_exercises(user, plan, pref, models):
    """Check if user has any exercises due for reminders"""
    try:
        # Get exercises with discord notifications enabled
        exercises = db_session.query(models['Exercise']).filter(
            models['Exercise'].recovery_plan_id == plan.id,
            models['Exercise'].is_active == True,
            models['Exercise'].discord_notifications == True
        ).all()
        
        print(f"🏋️ Found {len(exercises)} exercises with Discord notifications in plan {plan.id}")
        
        for ex in exercises:
            print(f"🔍 Checking exercise: {ex.name} (ID: {ex.id}, Frequency: {ex.frequency} hours)")
            
            # Check if exercise should be sent based on reminder frequency
            should_send, reason = should_send_reminder(user.id, ex.id, 'exercise', ex.frequency)
            
            if not should_send:
                print(f"⏳ Skipping exercise {ex.name}: {reason}")
                continue
            
            print(f"✅ Exercise {ex.name} is due for a reminder")
            
            # Attempt to get the channel
            try:
                target_channel = await bot.fetch_channel(int(pref.discord_channel_id))
                
                # Calculate scheduled time based on frequency and last session
                now = datetime.utcnow()
                scheduled_time = now
                
                # Try to find the most recent session or reminder to calculate the scheduled time
                last_reminder = db_session.query(models['DiscordInteractionLog']).filter(
                    models['DiscordInteractionLog'].user_id == user.id,
                    models['DiscordInteractionLog'].exercise_id == ex.id,
                    models['DiscordInteractionLog'].message_type == 'exercise'
                ).order_by(models['DiscordInteractionLog'].timestamp.desc()).first()
                
                if last_reminder:
                    # Calculate based on the last reminder plus the frequency
                    scheduled_time = last_reminder.timestamp + timedelta(hours=ex.frequency)
                
                # Convert to user's timezone
                user_scheduled_time = convert_timezone(scheduled_time, pref.time_zone)
                formatted_time = user_scheduled_time.strftime('%I:%M %p on %b %d, %Y')
                
                # Prepare the message
                details = []
                if ex.duration:
                    details.append(f"⏱️ Duration: {ex.duration}")
                if ex.repetitions:
                    details.append(f"🔄 Repetitions: {ex.repetitions}")
                
                details_str = "\n".join(details) if details else ""
                
                message = f"**Exercise Reminder**\n\n📋 Plan: {plan.name}\n🏋️ {ex.name}\n{details_str}\n⏰ Every {ex.frequency} hours\n\n{ex.description if ex.description else ''}\n\n{ex.instructions if ex.instructions else ''}\n\n⏰ Your scheduled time to do this exercise is {formatted_time}\n\nPlease reply with **YES** if you've completed this exercise, or **NO** if you haven't."
                
                # Send the message
                sent_message = await target_channel.send(message)
                
                # Log the interaction
                log = models['DiscordInteractionLog'](
                    user_id=user.id,
                    discord_channel_id=pref.discord_channel_id,
                    message_type='exercise',
                    exercise_id=ex.id,
                    sent_message=message,
                    timestamp=datetime.utcnow(),
                    discord_message_id=str(sent_message.id),
                    scheduled_time=scheduled_time  # Store scheduled time for reference
                )
                db_session.add(log)
                db_session.commit()
                
                print(f"📩 Sent exercise reminder for {ex.name} to channel {pref.discord_channel_id}")
                
            except Exception as e:
                print(f"❌ Error sending exercise reminder: {e}")
        
    except Exception as e:
        print(f"❌ Error checking exercises: {e}")

# Add a new unified function to determine if a reminder should be sent
def should_send_reminder(user_id, item_id, item_type, frequency_hours):
    """
    Determine if a reminder should be sent based on frequency and past reminders
    
    Args:
        user_id (int): User ID
        item_id (int): Medication or Exercise ID
        item_type (str): 'medication' or 'exercise'
        frequency_hours (int): Frequency in hours
        
    Returns:
        (bool, str): Tuple of (should_send, reason)
    """
    try:
        # Import models here to avoid circular dependencies
        from app.models.recovery_plan import DiscordInteractionLog
        
        # Get the most recent reminder sent for this item
        filter_kwargs = {
            'user_id': user_id,
            'message_type': item_type
        }
        
        if item_type == 'medication':
            filter_kwargs['medication_id'] = item_id
        elif item_type == 'exercise':
            filter_kwargs['exercise_id'] = item_id
        
        recent_reminder = db_session.query(DiscordInteractionLog).filter_by(
            **filter_kwargs
        ).order_by(DiscordInteractionLog.timestamp.desc()).first()
        
        # If no reminders have been sent, we should send one
        if not recent_reminder:
            return True, "No previous reminders found"
        
        # Check if enough time has passed since the last reminder
        now = datetime.utcnow()
        time_since_last = now - recent_reminder.timestamp
        hours_since_last = time_since_last.total_seconds() / 3600
        
        if hours_since_last >= frequency_hours:
            return True, f"Last reminder was {hours_since_last:.1f} hours ago (>= {frequency_hours})"
        else:
            # Calculate the next reminder time
            next_reminder_time = recent_reminder.timestamp + timedelta(hours=frequency_hours)
            hours_until_next = (next_reminder_time - now).total_seconds() / 3600
            next_reminder_formatted = next_reminder_time.strftime('%Y-%m-%d %H:%M')
            
            return False, f"Last reminder was only {hours_since_last:.1f} hours ago (< {frequency_hours}). Next reminder at {next_reminder_formatted} (in {hours_until_next:.1f} hours)"
            
    except Exception as e:
        print(f"❌ Error in should_send_reminder: {e}")
        # Default to True to ensure reminders don't get suppressed due to errors
        return True, f"Error checking reminder status: {e}"

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    # Don't respond to messages from bots (including self)
    if message.author.bot:
        return
    
    # Process commands
    await bot.process_commands(message)
    
    # Only handle server channel messages
    if isinstance(message.channel, discord.DMChannel):
        return
        
    try:
        # Import models to avoid circular dependencies
        from app.models.recovery_plan import MedicationDose, ExerciseSession
        models = get_models()
        
        # Find the user by Discord channel ID
        pref = db_session.query(models['DiscordPreference']).filter(
            models['DiscordPreference'].discord_channel_id == str(message.channel.id)
        ).first()
        
        if not pref:
            # This channel is not registered
            return
        
        user = db_session.query(models['User']).filter(
            models['User'].id == pref.user_id
        ).first()
        
        if not user:
            await message.channel.send("I don't recognize you. Please set up your Discord preferences in the Pain Management App.")
            return
        
        # Find the most recent unresponded interaction for this user
        recent_log = db_session.query(models['DiscordInteractionLog']).filter(
            models['DiscordInteractionLog'].user_id == user.id,
            models['DiscordInteractionLog'].response_time == None,
            models['DiscordInteractionLog'].message_type.in_(['medication', 'exercise'])
        ).order_by(models['DiscordInteractionLog'].timestamp.desc()).first()
        
        if not recent_log:
            await message.channel.send("I don't have any pending reminders for you. You can manage your recovery plan in the Pain Management App.")
            return
        
        # Determine the type of reminder
        reminder_type = "activity"
        if recent_log.message_type == 'medication':
            reminder_type = "medication"
            if recent_log.medication_id:
                med = db_session.query(models['Medication']).get(recent_log.medication_id)
                if med:
                    reminder_type = f"medication '{med.name}'"
        elif recent_log.message_type == 'exercise':
            reminder_type = "exercise"
            if recent_log.exercise_id:
                ex = db_session.query(models['Exercise']).get(recent_log.exercise_id)
                if ex:
                    reminder_type = f"exercise '{ex.name}'"
        
        # Process response
        response_text = message.content.strip().lower()
        response_time = datetime.utcnow()
        
        # Update the log with the response
        recent_log.response = response_text
        recent_log.response_time = response_time
        
        if response_text in ['yes', 'y', 'done', 'complete', 'completed']:
            recent_log.completed = True
            db_session.commit()
            
            # Record the dose or session
            if recent_log.message_type == 'medication' and recent_log.medication_id:
                dose = MedicationDose(
                    medication_id=recent_log.medication_id,
                    timestamp=response_time,
                    taken=True,
                    response_time=response_time
                )
                db_session.add(dose)
                db_session.commit()
                
                # Get scheduled time
                scheduled_time = getattr(recent_log, 'scheduled_time', recent_log.timestamp)
                
                # Format times for display
                user_scheduled_time = convert_timezone(scheduled_time, pref.time_zone)
                user_response_time = convert_timezone(response_time, pref.time_zone)
                
                formatted_scheduled = user_scheduled_time.strftime('%I:%M %p on %b %d, %Y')
                formatted_response = user_response_time.strftime('%I:%M %p on %b %d, %Y')
                
                await message.channel.send(f"Great! You were scheduled to take your {reminder_type} at {formatted_scheduled} and I recorded you took it at {formatted_response}. Keep up the good work! 👍")
            
            elif recent_log.message_type == 'exercise' and recent_log.exercise_id:
                session = ExerciseSession(
                    exercise_id=recent_log.exercise_id,
                    timestamp=response_time,
                    completed=True,
                    response_time=response_time
                )
                db_session.add(session)
                db_session.commit()
                
                # Get scheduled time
                scheduled_time = getattr(recent_log, 'scheduled_time', recent_log.timestamp)
                
                # Format times for display
                user_scheduled_time = convert_timezone(scheduled_time, pref.time_zone)
                user_response_time = convert_timezone(response_time, pref.time_zone)
                
                formatted_scheduled = user_scheduled_time.strftime('%I:%M %p on %b %d, %Y')
                formatted_response = user_response_time.strftime('%I:%M %p on %b %d, %Y')
                
                await message.channel.send(f"Awesome! You were scheduled to do your {reminder_type} at {formatted_scheduled} and I recorded you completed it at {formatted_response}. Keep up the good work! 💪")
            
            else:
                await message.channel.send(f"Thanks for letting me know you've completed your {reminder_type}!")
        
        elif response_text in ['no', 'n', 'not done', 'incomplete', 'not completed']:
            recent_log.completed = False
            db_session.commit()
            
            if recent_log.message_type == 'medication' and recent_log.medication_id:
                dose = MedicationDose(
                    medication_id=recent_log.medication_id,
                    timestamp=response_time,
                    taken=False,
                    response_time=response_time
                )
                db_session.add(dose)
                db_session.commit()
                
                # Get scheduled time
                scheduled_time = getattr(recent_log, 'scheduled_time', recent_log.timestamp)
                
                # Format times for display
                user_scheduled_time = convert_timezone(scheduled_time, pref.time_zone)
                user_response_time = convert_timezone(response_time, pref.time_zone)
                
                formatted_scheduled = user_scheduled_time.strftime('%I:%M %p on %b %d, %Y')
                formatted_response = user_response_time.strftime('%I:%M %p on %b %d, %Y')
                
                await message.channel.send(f"I understand you haven't taken your {reminder_type}. You were scheduled to take it at {formatted_scheduled} and I recorded you missed it at {formatted_response}. Remember, your recovery plan is important for your health! 🙂")
            
            elif recent_log.message_type == 'exercise' and recent_log.exercise_id:
                session = ExerciseSession(
                    exercise_id=recent_log.exercise_id,
                    timestamp=response_time,
                    completed=False,
                    response_time=response_time
                )
                db_session.add(session)
                db_session.commit()
                
                # Get scheduled time
                scheduled_time = getattr(recent_log, 'scheduled_time', recent_log.timestamp)
                
                # Format times for display
                user_scheduled_time = convert_timezone(scheduled_time, pref.time_zone)
                user_response_time = convert_timezone(response_time, pref.time_zone)
                
                formatted_scheduled = user_scheduled_time.strftime('%I:%M %p on %b %d, %Y')
                formatted_response = user_response_time.strftime('%I:%M %p on %b %d, %Y')
                
                await message.channel.send(f"I understand you haven't completed your {reminder_type}. You were scheduled to do it at {formatted_scheduled} and I recorded you missed it at {formatted_response}. Remember, your recovery plan is important for your health! 🙂")
            
            else:
                await message.channel.send(f"I understand you haven't completed your {reminder_type}. I've recorded this. Remember, your recovery plan is important for your health! 🙂")
        
        else:
            await message.channel.send(f"I'm not sure what you mean. For your {reminder_type}, please reply with 'YES' if you've completed it, or 'NO' if you haven't.")
    
    except Exception as e:
        print(f"Error processing message: {e}")
        try:
            await message.channel.send("Sorry, I encountered an error processing your message. Please try again later.")
        except:
            pass
    finally:
        db_session.remove()

if __name__ == '__main__':
    token = os.environ.get('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN not found in environment variables!")
        exit(1)
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}") 