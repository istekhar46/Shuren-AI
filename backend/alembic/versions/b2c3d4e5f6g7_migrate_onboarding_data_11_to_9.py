"""migrate onboarding data from 11 steps to 9 states

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-11 10:30:00.000000

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate onboarding data from 11 steps to 9 states.
    
    Mapping:
    - Old Step 1 (basic_info) → Removed (moved to User model during registration)
    - Old Step 2 (fitness_level) → New State 1
    - Old Step 3 (fitness_goals) → New State 2
    - Old Steps 4 & 5 (target_metrics + constraints) → New State 3 (merged)
    - Old Step 6 (dietary_preferences) → New State 4
    - Old Step 7 (meal_planning) → New State 5
    - Old Step 8 (meal_schedule) → New State 6
    - Old Step 9 (workout_schedule) → New State 7
    - Old Step 10 (hydration) → New State 8
    - Old Step 11 (lifestyle_baseline) → New State 9
    
    Original data is preserved in _migration_metadata field.
    """
    # Get database connection
    connection = op.get_bind()
    
    # Fetch all onboarding states
    result = connection.execute(
        sa.text("""
            SELECT id, current_step, step_data, is_complete
            FROM onboarding_states
            WHERE deleted_at IS NULL
        """)
    )
    
    rows = result.fetchall()
    
    for row in rows:
        state_id = row[0]
        old_current_step = row[1]
        old_step_data = row[2] if row[2] else {}
        is_complete = row[3]
        
        # Create new step_data with remapped steps
        new_step_data = {}
        
        # Preserve original data in metadata
        migration_metadata = {
            'original_current_step': old_current_step,
            'original_step_data': old_step_data,
            'migration_date': '2026-02-11',
            'migration_version': 'b2c3d4e5f6g7'
        }
        
        # Map old steps to new states
        step_mapping = {
            # Skip step 1 (basic_info) - moved to User model
            2: 1,   # fitness_level
            3: 2,   # fitness_goals
            4: 3,   # target_metrics → workout_constraints (will merge with step 5)
            5: 3,   # physical_constraints → workout_constraints (merged)
            6: 4,   # dietary_preferences
            7: 5,   # meal_planning
            8: 6,   # meal_schedule
            9: 7,   # workout_schedule
            10: 8,  # hydration
            11: 9   # lifestyle_baseline
        }
        
        # Remap step data
        for old_step, new_state in step_mapping.items():
            old_key = f'step_{old_step}'
            new_key = f'step_{new_state}'
            
            if old_key in old_step_data:
                # Special handling for merged state 3 (steps 4 & 5)
                if new_state == 3:
                    if new_key not in new_step_data:
                        new_step_data[new_key] = {}
                    
                    # Merge data from both steps 4 and 5
                    if old_step == 4:
                        # Step 4: target_metrics (target_weight_kg, target_body_fat_percentage)
                        step_4_data = old_step_data[old_key]
                        if isinstance(step_4_data, dict):
                            new_step_data[new_key].update(step_4_data)
                    elif old_step == 5:
                        # Step 5: physical_constraints (equipment, injuries, limitations)
                        step_5_data = old_step_data[old_key]
                        if isinstance(step_5_data, dict):
                            new_step_data[new_key].update(step_5_data)
                else:
                    # Direct mapping for other steps
                    new_step_data[new_key] = old_step_data[old_key]
        
        # Add migration metadata
        new_step_data['_migration_metadata'] = migration_metadata
        
        # Calculate new current_step
        # If user was on step 1, they haven't started yet (step 0)
        # If user was on step 2-11, map to new state
        if old_current_step == 0:
            new_current_step = 0
        elif old_current_step == 1:
            # Step 1 is removed, so user should be at step 0
            new_current_step = 0
        elif old_current_step in step_mapping:
            new_current_step = step_mapping[old_current_step]
        else:
            # If current_step > 11 or invalid, cap at 9
            new_current_step = min(old_current_step, 9)
        
        # Update the record
        connection.execute(
            sa.text("""
                UPDATE onboarding_states
                SET current_step = :new_step,
                    step_data = :new_data
                WHERE id = :state_id
            """),
            {
                'new_step': new_current_step,
                'new_data': json.dumps(new_step_data),
                'state_id': state_id
            }
        )
    
    # After all data is migrated, add the check constraint
    op.create_check_constraint(
        'valid_current_step',
        'onboarding_states',
        'current_step >= 0 AND current_step <= 9'
    )


def downgrade() -> None:
    """Restore original 11-step data from migration metadata.
    
    This rollback restores the original step data and current_step
    from the _migration_metadata field.
    """
    # First, drop the check constraint
    op.drop_constraint('valid_current_step', 'onboarding_states', type_='check')
    
    # Get database connection
    connection = op.get_bind()
    
    # Fetch all onboarding states with migration metadata
    result = connection.execute(
        sa.text("""
            SELECT id, step_data
            FROM onboarding_states
            WHERE deleted_at IS NULL
            AND step_data ? '_migration_metadata'
        """)
    )
    
    rows = result.fetchall()
    
    for row in rows:
        state_id = row[0]
        step_data = row[1] if row[1] else {}
        
        # Extract migration metadata
        migration_metadata = step_data.get('_migration_metadata', {})
        
        if migration_metadata:
            # Restore original data
            original_current_step = migration_metadata.get('original_current_step', 0)
            original_step_data = migration_metadata.get('original_step_data', {})
            
            # Update the record
            connection.execute(
                sa.text("""
                    UPDATE onboarding_states
                    SET current_step = :old_step,
                        step_data = :old_data
                    WHERE id = :state_id
                """),
                {
                    'old_step': original_current_step,
                    'old_data': json.dumps(original_step_data),
                    'state_id': state_id
                }
            )
