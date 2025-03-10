"""Discord Bot Update Migration

This migration will:
1. Remove Discord direct message functionality
2. Add Discord channel ID support
3. Update frequency fields to use numeric values
4. Update existing data to fit the new schema
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Rev identifiers
revision = 'discord_bot_update'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Update discord_preferences table
    op.drop_column('discord_preferences', 'discord_user_id')
    op.drop_column('discord_preferences', 'message_mode')
    op.add_column('discord_preferences', sa.Column('discord_channel_id', sa.String(50), nullable=True))
    
    # Update medications table
    # First create a new column
    op.add_column('medications', sa.Column('frequency_hours', sa.Integer(), nullable=True))
    
    # Then update the data (convert string frequency to hours)
    conn = op.get_bind()
    
    # Update frequency values to hours based on string values
    conn.execute("""
    UPDATE medications
    SET frequency_hours = 
        CASE 
            WHEN frequency LIKE '%1 hour%' OR frequency LIKE '%every_1_hour%' THEN 1
            WHEN frequency LIKE '%2 hour%' OR frequency LIKE '%every_2_hours%' THEN 2
            WHEN frequency LIKE '%4 hour%' OR frequency LIKE '%every_4_hours%' THEN 4
            WHEN frequency LIKE '%6 hour%' OR frequency LIKE '%every_6_hours%' THEN 6
            WHEN frequency LIKE '%8 hour%' OR frequency LIKE '%every_8_hours%' THEN 8
            WHEN frequency LIKE '%12 hour%' OR frequency LIKE '%every_12_hours%' THEN 12
            WHEN frequency LIKE '%daily%' OR frequency LIKE '%once_daily%' THEN 24
            WHEN frequency LIKE '%twice daily%' OR frequency LIKE '%twice_daily%' THEN 12
            WHEN frequency LIKE '%three times daily%' OR frequency LIKE '%three_times_daily%' THEN 8
            WHEN frequency LIKE '%four times daily%' OR frequency LIKE '%four_times_daily%' THEN 6
            WHEN frequency LIKE '%weekly%' THEN 168
            WHEN frequency LIKE '%biweekly%' OR frequency LIKE '%twice weekly%' THEN 84
            WHEN frequency LIKE '%monthly%' THEN 672
            ELSE 24  -- Default to daily
        END
    """)
    
    # Drop old column and rename new one
    op.drop_column('medications', 'frequency')
    op.alter_column('medications', 'frequency_hours', new_column_name='frequency', nullable=False)
    
    # Update exercises table
    # First create a new column
    op.add_column('exercises', sa.Column('frequency_hours', sa.Integer(), nullable=True))
    
    # Then update the data (convert string frequency to hours)
    conn.execute("""
    UPDATE exercises
    SET frequency_hours = 
        CASE 
            WHEN frequency LIKE '%daily%' THEN 24
            WHEN frequency LIKE '%twice daily%' OR frequency LIKE '%twice_daily%' THEN 12
            WHEN frequency LIKE '%three times daily%' OR frequency LIKE '%three_times_daily%' THEN 8
            WHEN frequency LIKE '%every other day%' OR frequency LIKE '%every_other_day%' THEN 48
            WHEN frequency LIKE '%weekly%' THEN 168
            WHEN frequency LIKE '%twice weekly%' OR frequency LIKE '%twice_weekly%' THEN 84
            WHEN frequency LIKE '%three times weekly%' OR frequency LIKE '%three_times_weekly%' THEN 56
            ELSE 24  -- Default to daily
        END
    """)
    
    # Drop old column and rename new one
    op.drop_column('exercises', 'frequency')
    op.alter_column('exercises', 'frequency_hours', new_column_name='frequency', nullable=False)


def downgrade():
    # This migration is not reversible because we're losing data in the conversion.
    # But for completeness, we'll provide a downgrade path that restores the original schema
    # with default values.
    
    # Restore discord_preferences table
    op.drop_column('discord_preferences', 'discord_channel_id')
    op.add_column('discord_preferences', sa.Column('discord_user_id', sa.String(50), nullable=True))
    op.add_column('discord_preferences', sa.Column('message_mode', sa.String(20), nullable=False, server_default=sa.text("'both'")))
    
    # Restore medications table
    op.add_column('medications', sa.Column('frequency_str', sa.String(50), nullable=True))
    
    # Convert hours back to strings (lossy conversion)
    conn = op.get_bind()
    conn.execute("""
    UPDATE medications
    SET frequency_str = 
        CASE 
            WHEN frequency = 1 THEN 'every_1_hour'
            WHEN frequency = 2 THEN 'every_2_hours'
            WHEN frequency = 4 THEN 'every_4_hours'
            WHEN frequency = 6 THEN 'every_6_hours'
            WHEN frequency = 8 THEN 'every_8_hours'
            WHEN frequency = 12 THEN 'every_12_hours'
            WHEN frequency = 24 THEN 'once_daily'
            WHEN frequency = 168 THEN 'weekly'
            WHEN frequency = 84 THEN 'biweekly'
            WHEN frequency = 672 THEN 'monthly'
            ELSE 'once_daily'  -- Default
        END
    """)
    
    op.drop_column('medications', 'frequency')
    op.alter_column('medications', 'frequency_str', new_column_name='frequency', nullable=False)
    
    # Restore exercises table
    op.add_column('exercises', sa.Column('frequency_str', sa.String(50), nullable=True))
    
    # Convert hours back to strings (lossy conversion)
    conn.execute("""
    UPDATE exercises
    SET frequency_str = 
        CASE 
            WHEN frequency = 24 THEN 'daily'
            WHEN frequency = 12 THEN 'twice_daily'
            WHEN frequency = 8 THEN 'three_times_daily'
            WHEN frequency = 48 THEN 'every_other_day'
            WHEN frequency = 168 THEN 'weekly'
            WHEN frequency = 84 THEN 'twice_weekly'
            WHEN frequency = 56 THEN 'three_times_weekly'
            ELSE 'daily'  -- Default
        END
    """)
    
    op.drop_column('exercises', 'frequency')
    op.alter_column('exercises', 'frequency_str', new_column_name='frequency', nullable=False) 