"""make_updated_at_non_nullable

Revision ID: 957d7289c7c3
Revises: 3a4feffbb7a1
Create Date: 2026-01-30 19:21:28.150406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '957d7289c7c3'
down_revision: Union[str, Sequence[str], None] = '3a4feffbb7a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Make updated_at non-nullable with default value."""
    # Get connection to check which tables exist
    connection = op.get_bind()
    
    # List of all tables that inherit from BaseModel
    tables = [
        'users',
        'onboarding_states',
        'user_profiles',
        'user_profile_versions',
        'fitness_goals',
        'physical_constraints',
        'dietary_preferences',
        'meal_plans',
        'meal_schedules',
        'workout_schedules',
        'hydration_preferences',
        'lifestyle_baselines',
        'workout_plans',
        'workout_days',
        'workout_exercises',
        'exercise_library',
        'chat_sessions',
        'chat_messages'
    ]
    
    # Check which tables exist
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    for table in tables:
        # Only process tables that exist
        if table not in existing_tables:
            continue
            
        # Check if the table has an updated_at column
        columns = [col['name'] for col in inspector.get_columns(table)]
        if 'updated_at' not in columns:
            continue
        
        # First, set updated_at to created_at for rows where updated_at is NULL
        op.execute(
            f"UPDATE {table} SET updated_at = created_at WHERE updated_at IS NULL"
        )
        
        # Then alter the column to be non-nullable with server default
        op.alter_column(
            table,
            'updated_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        )


def downgrade() -> None:
    """Downgrade schema: Make updated_at nullable again."""
    tables = [
        'users',
        'onboarding_states',
        'user_profiles',
        'user_profile_versions',
        'fitness_goals',
        'physical_constraints',
        'dietary_preferences',
        'meal_plans',
        'meal_schedules',
        'workout_schedules',
        'hydration_preferences',
        'lifestyle_baselines',
        'workout_plans',
        'workout_days',
        'workout_exercises',
        'exercise_library',
        'chat_sessions',
        'chat_messages'
    ]
    
    for table in tables:
        op.alter_column(
            table,
            'updated_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            nullable=True,
            server_default=None
        )
