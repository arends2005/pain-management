Your are a full stack developer of Discord Bots, review discord bot functions.

Fix the current discord bot @discord_bot.py
1. Don't post Bot messages to Direct Message Channels like the bot currenlty does.
2. remove all code and forms related to Direct Messages
3. update the database schema to remove Direct Messages and rebuild the container from scratch docker compose down -v && docker compose up --build
4. Only post messages to Server Channels the bot has been added to.

Features
1.  In order for the bot to post messages to the Channel ID of the Server the webapp should allow input in the Discord Bot Preferences by the USER or ADMIN page
2.  The Discord User ID may not be needed as that is used for Direct Messages which we are removing that feature, no Direct Messages.
3.  The Test Discord Connection feature should post a message to the Server Channels its added to saying "This is a test of the bot connection"
4.  User should receive reminders with a requesed response, and when the response is submitted, a follow up message should confirm the response with details.

Database Schema changes
1. Remove Direct Message catagories and related information
2. update the Frequency field type to be a number or integer that relates to the frequency discription so that recurring reminders work better with the code
 frequency = SelectField('Frequency', validators=[DataRequired()],
                          choices=[
                              (1, 'Every 1 Hour'),
                              (2, 'Every 2 Hours'),
                              (4, 'Every 4 Hours'),
                              (6, 'Every 6 Hours'),
                              (8, 'Every 8 Hours'),
                              (12, 'Every 12 Hours'),
                              (24, 'Every 24 Hours'),
                              ('weekly', 'Weekly'),
                              ('biweekly', 'Twice Weekly'),
                              ('monthly', 'Monthly')
                          ])

3. Determine how to deal properly with freqency that is longer than 24 hours, weekly, biweekly, monthly
4. Remind users if they haven't responded to a requested response, if a frequency passes without a response before the next request mark it as not completed and contiune with future requests.
5. Allow Users to update past responses in the dashboard 