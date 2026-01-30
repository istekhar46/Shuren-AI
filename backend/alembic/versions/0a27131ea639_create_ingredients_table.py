"""create ingredients table

Revision ID: 0a27131ea639
Revises: 7f960ed91e7c
Create Date: 2026-01-30 22:27:05.045990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a27131ea639'
down_revision: Union[str, Sequence[str], None] = '7f960ed91e7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create ingredients table."""
    op.create_table(
        'ingredients',
        # Basic information
        sa.Column('name', sa.String(length=200), nullable=False, unique=True),
        sa.Column('name_hindi', sa.String(length=200), nullable=True),
        
        # Classification
        sa.Column('category', sa.String(length=50), nullable=False),
        
        # Nutritional information (per 100g)
        sa.Column('calories_per_100g', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('protein_per_100g', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('carbs_per_100g', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('fats_per_100g', sa.Numeric(precision=5, scale=2), nullable=True),
        
        # Measurement
        sa.Column('typical_unit', sa.String(length=20), nullable=False),
        
        # Allergen tags
        sa.Column('is_allergen', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('allergen_type', sa.String(length=50), nullable=True),
        
        # Metadata
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        
        # Base model columns
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Unique constraint on name
        sa.UniqueConstraint('name', name='uq_ingredients_name'),
        
        # Check constraint on category
        sa.CheckConstraint(
            "category IN ('vegetable', 'fruit', 'protein', 'grain', 'dairy', 'spice', 'oil', 'other')",
            name='valid_category'
        ),
    )
    
    # Create indexes for performance
    op.create_index(
        'idx_ingredients_category',
        'ingredients',
        ['category'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = true')
    )
    
    op.create_index(
        'idx_ingredients_allergen',
        'ingredients',
        ['is_allergen', 'allergen_type'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL AND is_active = true')
    )


def downgrade() -> None:
    """Downgrade schema: Drop ingredients table."""
    # Drop indexes first
    op.drop_index('idx_ingredients_allergen', table_name='ingredients', postgresql_where=sa.text('deleted_at IS NULL AND is_active = true'))
    op.drop_index('idx_ingredients_category', table_name='ingredients', postgresql_where=sa.text('deleted_at IS NULL AND is_active = true'))
    
    # Drop table
    op.drop_table('ingredients')
