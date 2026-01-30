"""create template meals table

Revision ID: 582ee71d9305
Revises: 43aeb196576c
Create Date: 2026-01-30 23:13:09.562062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '582ee71d9305'
down_revision: Union[str, Sequence[str], None] = '43aeb196576c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create template_meals table."""
    op.create_table(
        'template_meals',
        # Foreign keys
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('meal_schedule_id', sa.UUID(), nullable=False),
        sa.Column('dish_id', sa.UUID(), nullable=False),
        
        # Meal slot identification
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        
        # Dish role
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('alternative_order', sa.Integer(), nullable=False, server_default=sa.text('1')),
        
        # Base model columns
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ['template_id'],
            ['meal_templates.id'],
            name='fk_template_meals_template_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['meal_schedule_id'],
            ['meal_schedules.id'],
            name='fk_template_meals_meal_schedule_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['dish_id'],
            ['dishes.id'],
            name='fk_template_meals_dish_id',
            ondelete='RESTRICT'
        ),
        
        # Check constraints
        sa.CheckConstraint('day_of_week BETWEEN 0 AND 6', name='valid_day_of_week'),
        sa.CheckConstraint('alternative_order BETWEEN 1 AND 5', name='valid_alternative_order'),
    )
    
    # Create indexes for performance
    op.create_index(
        'idx_template_meals_template',
        'template_meals',
        ['template_id'],
        unique=False
    )
    
    op.create_index(
        'idx_template_meals_schedule',
        'template_meals',
        ['meal_schedule_id'],
        unique=False
    )
    
    op.create_index(
        'idx_template_meals_dish',
        'template_meals',
        ['dish_id'],
        unique=False
    )
    
    op.create_index(
        'idx_template_meals_day',
        'template_meals',
        ['template_id', 'day_of_week'],
        unique=False
    )
    
    op.create_index(
        'idx_template_meals_primary',
        'template_meals',
        ['template_id', 'is_primary'],
        unique=False,
        postgresql_where=sa.text('is_primary = true')
    )


def downgrade() -> None:
    """Downgrade schema: Drop template_meals table."""
    # Drop indexes first
    op.drop_index('idx_template_meals_primary', table_name='template_meals', postgresql_where=sa.text('is_primary = true'))
    op.drop_index('idx_template_meals_day', table_name='template_meals')
    op.drop_index('idx_template_meals_dish', table_name='template_meals')
    op.drop_index('idx_template_meals_schedule', table_name='template_meals')
    op.drop_index('idx_template_meals_template', table_name='template_meals')
    
    # Drop table (foreign keys are dropped automatically)
    op.drop_table('template_meals')
