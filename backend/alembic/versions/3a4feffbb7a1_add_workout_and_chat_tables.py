"""add_workout_and_chat_tables

Revision ID: 3a4feffbb7a1
Revises: 0c90191dbca7
Create Date: 2026-01-30 14:47:22.925842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3a4feffbb7a1'
down_revision: Union[str, Sequence[str], None] = '0c90191dbca7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create exercise_library table (reference data, no dependencies)
    op.create_table(
        'exercise_library',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exercise_name', sa.String(length=255), nullable=False),
        sa.Column('exercise_slug', sa.String(length=255), nullable=False),
        sa.Column('exercise_type', sa.String(length=50), nullable=False),
        sa.Column('primary_muscle_group', sa.String(length=100), nullable=False),
        sa.Column('secondary_muscle_groups', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('equipment_required', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
        sa.Column('difficulty_level', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('gif_url', sa.Text(), nullable=True),
        sa.Column('video_url', sa.Text(), nullable=True),
        sa.Column('is_compound', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_unilateral', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "exercise_type IN ('strength', 'cardio', 'flexibility', 'plyometric', 'olympic')",
            name='valid_exercise_type'
        ),
        sa.CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
            name='valid_difficulty'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('exercise_name', name='unique_exercise_name'),
        sa.UniqueConstraint('exercise_slug', name='unique_exercise_slug')
    )
    op.create_index('idx_exercise_library_type', 'exercise_library', ['exercise_type'])
    op.create_index('idx_exercise_library_muscle', 'exercise_library', ['primary_muscle_group'])
    op.create_index('idx_exercise_library_difficulty', 'exercise_library', ['difficulty_level'])
    op.create_index('idx_exercise_library_equipment', 'exercise_library', ['equipment_required'], postgresql_using='gin')

    # Create workout_plans table (depends on users)
    op.create_table(
        'workout_plans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('plan_name', sa.String(length=255), nullable=False),
        sa.Column('plan_description', sa.Text(), nullable=True),
        sa.Column('duration_weeks', sa.Integer(), nullable=False),
        sa.Column('days_per_week', sa.Integer(), nullable=False),
        sa.Column('plan_rationale', sa.Text(), nullable=True),
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('duration_weeks >= 1 AND duration_weeks <= 52', name='valid_duration'),
        sa.CheckConstraint('days_per_week >= 1 AND days_per_week <= 7', name='valid_days_per_week'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='unique_user_workout_plan')
    )
    op.create_index('idx_workout_plans_user_id', 'workout_plans', ['user_id'], unique=True)
    op.create_index('idx_workout_plans_updated', 'workout_plans', [sa.text('updated_at DESC')])

    # Create workout_days table (depends on workout_plans)
    op.create_table(
        'workout_days',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workout_plan_id', sa.UUID(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('day_name', sa.String(length=255), nullable=False),
        sa.Column('muscle_groups', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column('workout_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('day_number >= 1 AND day_number <= 7', name='valid_day_number'),
        sa.CheckConstraint(
            "workout_type IN ('strength', 'cardio', 'hiit', 'active_recovery', 'rest')",
            name='valid_workout_type'
        ),
        sa.ForeignKeyConstraint(['workout_plan_id'], ['workout_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workout_plan_id', 'day_number', name='unique_plan_day')
    )
    op.create_index('idx_workout_days_plan', 'workout_days', ['workout_plan_id', 'day_number'])

    # Create workout_exercises table (depends on workout_days and exercise_library)
    op.create_table(
        'workout_exercises',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workout_day_id', sa.UUID(), nullable=False),
        sa.Column('exercise_library_id', sa.UUID(), nullable=False),
        sa.Column('exercise_order', sa.Integer(), nullable=False),
        sa.Column('sets', sa.Integer(), nullable=False),
        sa.Column('reps_min', sa.Integer(), nullable=True),
        sa.Column('reps_max', sa.Integer(), nullable=True),
        sa.Column('reps_target', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('weight_progression_type', sa.String(length=50), nullable=True),
        sa.Column('rest_seconds', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('sets >= 1 AND sets <= 20', name='valid_sets'),
        sa.CheckConstraint(
            '(reps_target IS NOT NULL AND reps_target >= 1 AND reps_target <= 100) OR '
            '(reps_min IS NOT NULL AND reps_max IS NOT NULL AND reps_min <= reps_max)',
            name='valid_reps'
        ),
        sa.CheckConstraint('rest_seconds >= 0 AND rest_seconds <= 600', name='valid_rest'),
        sa.CheckConstraint(
            "weight_progression_type IS NULL OR "
            "weight_progression_type IN ('linear', 'percentage', 'rpe_based', 'none')",
            name='valid_progression'
        ),
        sa.ForeignKeyConstraint(['workout_day_id'], ['workout_days.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exercise_library_id'], ['exercise_library.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workout_day_id', 'exercise_order', name='unique_day_exercise_order')
    )
    op.create_index('idx_workout_exercises_day', 'workout_exercises', ['workout_day_id', 'exercise_order'])
    op.create_index('idx_workout_exercises_library', 'workout_exercises', ['exercise_library_id'])

    # Create chat_sessions table (depends on users)
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session_type', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "session_type IN ('general', 'workout', 'meal', 'supplement', 'tracking')",
            name='valid_session_type'
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name='valid_status'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_sessions_user', 'chat_sessions', ['user_id', sa.text('started_at DESC')])
    op.create_index(
        'idx_chat_sessions_active',
        'chat_sessions',
        ['user_id', 'status'],
        postgresql_where=sa.text("status = 'active'")
    )

    # Create chat_messages table (depends on chat_sessions)
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name='valid_role'
        ),
        sa.CheckConstraint(
            "agent_type IS NULL OR "
            "agent_type IN ('workout_planning', 'diet_planning', 'supplement_guidance', "
            "'tracking_adjustment', 'scheduling_reminder', 'conversational')",
            name='valid_agent_type'
        ),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_messages_session', 'chat_messages', ['session_id', 'created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order of creation (respecting foreign key dependencies)
    op.drop_index('idx_chat_messages_session', table_name='chat_messages')
    op.drop_table('chat_messages')

    op.drop_index('idx_chat_sessions_active', table_name='chat_sessions', postgresql_where=sa.text("status = 'active'"))
    op.drop_index('idx_chat_sessions_user', table_name='chat_sessions')
    op.drop_table('chat_sessions')

    op.drop_index('idx_workout_exercises_library', table_name='workout_exercises')
    op.drop_index('idx_workout_exercises_day', table_name='workout_exercises')
    op.drop_table('workout_exercises')

    op.drop_index('idx_workout_days_plan', table_name='workout_days')
    op.drop_table('workout_days')

    op.drop_index('idx_workout_plans_updated', table_name='workout_plans')
    op.drop_index('idx_workout_plans_user_id', table_name='workout_plans')
    op.drop_table('workout_plans')

    op.drop_index('idx_exercise_library_equipment', table_name='exercise_library', postgresql_using='gin')
    op.drop_index('idx_exercise_library_difficulty', table_name='exercise_library')
    op.drop_index('idx_exercise_library_muscle', table_name='exercise_library')
    op.drop_index('idx_exercise_library_type', table_name='exercise_library')
    op.drop_table('exercise_library')
