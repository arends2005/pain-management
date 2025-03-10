"""Update Discord Interaction Logs

This migration updates the discord_interaction_logs table to change the 
column name from discord_user_id to discord_channel_id to reflect the
usage of server channels instead of direct messages.
"""

from alembic import op
import sqlalchemy as sa

# Rev identifiers
revision = 'update_discord_logs'
down_revision = 'discord_bot_update'
branch_labels = None
depends_on = None

def upgrade():
    # First add the new column
    op.add_column('discord_interaction_logs', 
                  sa.Column('discord_channel_id', sa.String(50), nullable=True))
    
    # Then copy data from old column to new column
    conn = op.get_bind()
    conn.execute("""
    UPDATE discord_interaction_logs
    SET discord_channel_id = discord_user_id
    """)
    
    # Make the new column non-nullable
    op.alter_column('discord_interaction_logs', 'discord_channel_id', 
                    existing_type=sa.String(50),
                    nullable=False)
    
    # Finally drop the old column
    op.drop_column('discord_interaction_logs', 'discord_user_id')


def downgrade():
    # First add the old column back
    op.add_column('discord_interaction_logs', 
                  sa.Column('discord_user_id', sa.String(50), nullable=True))
    
    # Then copy data from new column to old column
    conn = op.get_bind()
    conn.execute("""
    UPDATE discord_interaction_logs
    SET discord_user_id = discord_channel_id
    """)
    
    # Make the old column non-nullable again
    op.alter_column('discord_interaction_logs', 'discord_user_id', 
                    existing_type=sa.String(50),
                    nullable=False)
    
    # Finally drop the new column
    op.drop_column('discord_interaction_logs', 'discord_channel_id') 