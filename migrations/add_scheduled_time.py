"""Add scheduled_time to Discord Interaction Logs

This migration adds a scheduled_time column to the discord_interaction_logs table
to store the scheduled time for medication/exercise reminders.
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Rev identifiers
revision = 'add_scheduled_time'
down_revision = 'update_discord_logs'  # Assuming this is the previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Add the scheduled_time column
    op.add_column('discord_interaction_logs', 
                  sa.Column('scheduled_time', sa.DateTime, nullable=True))
    
    # Update existing records to use timestamp as scheduled_time (optional)
    conn = op.get_bind()
    conn.execute("""
    UPDATE discord_interaction_logs
    SET scheduled_time = timestamp
    WHERE message_type IN ('medication', 'exercise')
    """)

def downgrade():
    # Drop the scheduled_time column
    op.drop_column('discord_interaction_logs', 'scheduled_time') 