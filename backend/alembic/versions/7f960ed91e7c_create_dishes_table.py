"""create dishes table

Revision ID: 7f960ed91e7c
Revises: 957d7289c7c3
Create Date: 2026-01-30 22:03:32.500826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7f960ed91e7c'
down_revision: Union[str, Sequence[str], None] = '957d7289c7c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create dishes table."""
    op.create_table(
        'dishes',
        # Basic information
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('name_hindi', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Classification
        sa.Column('cuisine_type', sa.String(length=50), nullable=False),
        sa.Column('meal_type', sa.String(length=50), nullable=False),
        sa.Column('dish_category', sa.String(length=50), nullable=True),
        
        # Nutritional information (per serving)
        sa.Column('serving_size_g', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('calories', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('protein_g', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('carbs_g', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('fats_g', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('fiber_g', sa.Numeric(precision=4, scale=2), nullable=True),
        
        # Preparation details
        sa.Column('prep_time_minutes', sa.Integer(), nullable=False),
        sa.Column('cook_time_minutes', sa.Integer(), nullable=False),
        sa.Column('difficulty_level', sa.String(length=20), nullable=False),
        
        # Dietary tags
        sa.Column('is_vegetarian', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_vegan', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_gluten_free', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_dairy_free', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_nut_free', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        # Allergen information
        sa.Column('contains_allergens', postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")),
        
        # Metadata
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('popularity_score', sa.Integer(), nullable=False, server_default=sa.text('0')),
        
        # Base model columns
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Check constraints
        sa.CheckConstraint('calories > 0 AND calories < 2000', name='valid_calories'),
        sa.CheckConstraint('protein_g >= 0 AND carbs_g >= 0 AND fats_g >= 0', name='valid_macros'),
        sa.CheckConstraint('prep_time_minutes >= 0 AND prep_time_minutes <= 180', name='valid_prep_time'),
        sa.CheckConstraint('cook_time_minutes >= 0 AND cook_time_minutes <= 240', name='valid_cook_time'),
        sa.CheckConstraint("difficulty_level IN ('easy', 'medium', 'hard')", name='valid_difficulty'),
        sa.CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout')",
            name='valid_meal_type'
        ),
    )
    
    # Create indexes for performance
    op.create_index(
        'idx_dishes_meal_type',
        'dishes',
        ['meal_type'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = true')
    )
    
    op.create_index(
        'idx_dishes_dietary',
        'dishes',
        ['is_vegetarian', 'is_vegan'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = true')
    )
    
    op.create_index(
        'idx_dishes_cuisine',
        'dishes',
        ['cuisine_type'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = true')
    )
    
    op.create_index(
        'idx_dishes_nutrition',
        'dishes',
        ['calories', 'protein_g'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = true')
    )
    
    # GIN index for allergen array searches
    op.create_index(
        'idx_dishes_allergens',
        'dishes',
        ['contains_allergens'],
        unique=False,
        postgresql_using='gin',
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = true')
    )


def downgrade() -> None:
    """Downgrade schema: Drop dishes table."""
    # Drop indexes first
    op.drop_index('idx_dishes_allergens', table_name='dishes', postgresql_where=sa.text('deleted_at IS NULL AND is_active = true'))
    op.drop_index('idx_dishes_nutrition', table_name='dishes', postgresql_where=sa.text('deleted_at IS NULL AND is_active = true'))
    op.drop_index('idx_dishes_cuisine', table_name='dishes', postgresql_where=sa.text('deleted_at IS NULL AND is_active = true'))
    op.drop_index('idx_dishes_dietary', table_name='dishes', postgresql_where=sa.text('deleted_at IS NULL AND is_active = true'))
    op.drop_index('idx_dishes_meal_type', table_name='dishes', postgresql_where=sa.text('deleted_at IS NULL AND is_active = true'))
    
    # Drop table
    op.drop_table('dishes')
