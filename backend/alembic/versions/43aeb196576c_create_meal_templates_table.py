"""create meal templates table

Revision ID: 43aeb196576c
Revises: 5e89aa6e6fb3
Create Date: 2026-01-30 23:11:53.258525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43aeb196576c'
down_revision: Union[str, Sequence[str], None] = '5e89aa6e6fb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create meal_templates table."""
    op.create_table(
        'meal_templates',
        # Foreign key to profile
        sa.Column('profile_id', sa.UUID(), nullable=False),
        
        # Template identification
        sa.Column('week_number', sa.Integer(), nullable=False),
        
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        
        # Generation metadata
        sa.Column('generated_by', sa.String(length=50), nullable=False, server_default=sa.text("'system'")),
        sa.Column('generation_reason', sa.Text(), nullable=True),
        
        # Base model columns
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key constraint
        sa.ForeignKeyConstraint(
            ['profile_id'],
            ['user_profiles.id'],
            name='fk_meal_templates_profile_id',
            ondelete='CASCADE'
        ),
        
        # Check constraint: week_number BETWEEN 1 AND 4
        sa.CheckConstraint('week_number BETWEEN 1 AND 4', name='valid_week_number'),
        
        # Unique constraint on (profile_id, week_number)
        sa.UniqueConstraint('profile_id', 'week_number', name='unique_profile_week'),
    )
    
    # Create indexes for performance
    op.create_index(
        'idx_meal_templates_profile',
        'meal_templates',
        ['profile_id'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    op.create_index(
        'idx_meal_templates_active',
        'meal_templates',
        ['profile_id', 'is_active'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = true')
    )


def downgrade() -> None:
    """Downgrade schema: Drop meal_templates table."""
    # Drop indexes first
    op.drop_index('idx_meal_templates_active', table_name='meal_templates', postgresql_where=sa.text('deleted_at IS NULL AND is_active = true'))
    op.drop_index('idx_meal_templates_profile', table_name='meal_templates', postgresql_where=sa.text('deleted_at IS NULL'))
    
    # Drop table (foreign keys are dropped automatically)
    op.drop_table('meal_templates')
