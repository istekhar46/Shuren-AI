"""update onboarding state schema

Revision ID: a1b2c3d4e5f6
Revises: 5aca3703586c
Create Date: 2026-02-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5aca3703586c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade onboarding_states table.
    
    Changes:
    1. Add agent_history JSONB column with default empty list
    
    Note: Check constraint for current_step will be added AFTER data migration
    """
    # Add agent_history column
    op.add_column(
        'onboarding_states',
        sa.Column(
            'agent_history',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='[]'
        )
    )


def downgrade() -> None:
    """Downgrade onboarding_states table.
    
    Reverts:
    1. Remove agent_history column
    """
    # Drop agent_history column
    op.drop_column('onboarding_states', 'agent_history')
