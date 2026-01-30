"""create dish ingredients table

Revision ID: 5e89aa6e6fb3
Revises: 0a27131ea639
Create Date: 2026-01-30 22:53:10.557968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e89aa6e6fb3'
down_revision: Union[str, Sequence[str], None] = '0a27131ea639'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create dish_ingredients junction table."""
    op.create_table(
        'dish_ingredients',
        # Foreign keys
        sa.Column('dish_id', sa.UUID(), nullable=False),
        sa.Column('ingredient_id', sa.UUID(), nullable=False),
        
        # Quantity information
        sa.Column('quantity', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        
        # Optional notes
        sa.Column('preparation_note', sa.String(length=200), nullable=True),
        
        # Metadata
        sa.Column('is_optional', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        # Base model columns
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ['dish_id'],
            ['dishes.id'],
            name='fk_dish_ingredients_dish_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['ingredient_id'],
            ['ingredients.id'],
            name='fk_dish_ingredients_ingredient_id',
            ondelete='RESTRICT'
        ),
        
        # Unique constraint on (dish_id, ingredient_id)
        sa.UniqueConstraint('dish_id', 'ingredient_id', name='unique_dish_ingredient'),
        
        # Check constraint: quantity > 0
        sa.CheckConstraint('quantity > 0', name='valid_quantity'),
    )
    
    # Create indexes for performance
    op.create_index(
        'idx_dish_ingredients_dish',
        'dish_ingredients',
        ['dish_id'],
        unique=False
    )
    
    op.create_index(
        'idx_dish_ingredients_ingredient',
        'dish_ingredients',
        ['ingredient_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema: Drop dish_ingredients table."""
    # Drop indexes first
    op.drop_index('idx_dish_ingredients_ingredient', table_name='dish_ingredients')
    op.drop_index('idx_dish_ingredients_dish', table_name='dish_ingredients')
    
    # Drop table (foreign keys are dropped automatically)
    op.drop_table('dish_ingredients')
