"""
Property-based tests for onboarding data migration (11 steps → 9 states).

These tests use Hypothesis to verify that the migration logic correctly:
1. Preserves all original data in metadata
2. Correctly remaps state numbers from 11-step to 9-state structure

**Property: Data Migration Preservation**
**Validates: Requirements 3.1**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from uuid import uuid4
from datetime import datetime, timezone
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.onboarding import OnboardingState
from app.models.user import User


# ============================================================================
# Hypothesis Strategies for Onboarding Data
# ============================================================================

def step_data_strategy():
    """Generate realistic step data for old 11-step structure.
    
    Simplified to generate faster while still testing the migration logic.
    """
    return st.fixed_dictionaries({
        f"step_{i}": st.one_of(
            st.none(),
            st.dictionaries(
                keys=st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
                values=st.one_of(
                    st.text(min_size=0, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
                    st.integers(min_value=0, max_value=100),
                    st.booleans(),
                    st.lists(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'), max_size=3)
                ),
                min_size=0,
                max_size=5
            )
        ) for i in range(1, 12)
    })


def current_step_strategy():
    """Generate valid current_step values for old 11-step structure."""
    return st.integers(min_value=0, max_value=11)


# ============================================================================
# Migration Logic (Replicated from Alembic Migration)
# ============================================================================

def migrate_step_data(old_current_step: int, old_step_data: dict) -> tuple[int, dict]:
    """Replicate the migration logic from the Alembic migration.
    
    Args:
        old_current_step: Current step in 11-step structure (0-11)
        old_step_data: Step data in 11-step structure
    
    Returns:
        tuple: (new_current_step, new_step_data) in 9-state structure
    """
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
        
        if old_key in old_step_data and old_step_data[old_key] is not None:
            # Special handling for merged state 3 (steps 4 & 5)
            if new_state == 3:
                if new_key not in new_step_data:
                    new_step_data[new_key] = {}
                
                # Merge data from both steps 4 and 5
                if old_step == 4:
                    # Step 4: target_metrics
                    step_4_data = old_step_data[old_key]
                    if isinstance(step_4_data, dict):
                        new_step_data[new_key].update(step_4_data)
                elif old_step == 5:
                    # Step 5: physical_constraints
                    step_5_data = old_step_data[old_key]
                    if isinstance(step_5_data, dict):
                        new_step_data[new_key].update(step_5_data)
            else:
                # Direct mapping for other steps
                new_step_data[new_key] = old_step_data[old_key]
    
    # Add migration metadata
    new_step_data['_migration_metadata'] = migration_metadata
    
    # Calculate new current_step
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
    
    return new_current_step, new_step_data


# ============================================================================
# Property Tests
# ============================================================================

class TestDataMigrationPreservation:
    """
    Property: Data Migration Preservation
    
    For any onboarding state with 11-step data, the migration should:
    1. Preserve all original data in _migration_metadata
    2. Correctly remap state numbers according to the mapping
    3. Merge steps 4 & 5 into state 3
    4. Not lose any data during migration
    
    **Validates: Requirements 3.1**
    """
    
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    @given(
        current_step=current_step_strategy(),
        step_data=step_data_strategy()
    )
    def test_migration_preserves_original_data(self, current_step: int, step_data: dict):
        """
        Property: All original data is preserved in migration metadata.
        
        Given any valid 11-step onboarding state,
        When the migration is applied,
        Then the original current_step and step_data should be preserved
        in the _migration_metadata field.
        """
        # Apply migration
        new_current_step, new_step_data = migrate_step_data(current_step, step_data)
        
        # Verify metadata exists
        assert '_migration_metadata' in new_step_data
        metadata = new_step_data['_migration_metadata']
        
        # Verify original data is preserved
        assert metadata['original_current_step'] == current_step
        assert metadata['original_step_data'] == step_data
        assert metadata['migration_version'] == 'b2c3d4e5f6g7'
        assert 'migration_date' in metadata
    
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    @given(
        current_step=st.integers(min_value=2, max_value=11),
        step_data=step_data_strategy()
    )
    def test_migration_remaps_state_numbers_correctly(self, current_step: int, step_data: dict):
        """
        Property: State numbers are correctly remapped.
        
        Given any current_step from 2-11,
        When the migration is applied,
        Then the new current_step should match the expected mapping.
        """
        # Expected mapping
        expected_mapping = {
            2: 1,   # fitness_level
            3: 2,   # fitness_goals
            4: 3,   # target_metrics → workout_constraints
            5: 3,   # physical_constraints → workout_constraints (merged)
            6: 4,   # dietary_preferences
            7: 5,   # meal_planning
            8: 6,   # meal_schedule
            9: 7,   # workout_schedule
            10: 8,  # hydration
            11: 9   # lifestyle_baseline
        }
        
        # Apply migration
        new_current_step, new_step_data = migrate_step_data(current_step, step_data)
        
        # Verify mapping
        assert new_current_step == expected_mapping[current_step]
    
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    @given(step_data=step_data_strategy())
    def test_migration_handles_step_0_and_1(self, step_data: dict):
        """
        Property: Steps 0 and 1 are correctly handled.
        
        Given current_step of 0 or 1,
        When the migration is applied,
        Then the new current_step should be 0 (since step 1 is removed).
        """
        # Test step 0
        new_current_step_0, _ = migrate_step_data(0, step_data)
        assert new_current_step_0 == 0
        
        # Test step 1
        new_current_step_1, _ = migrate_step_data(1, step_data)
        assert new_current_step_1 == 0
    
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    @given(step_data=step_data_strategy())
    def test_migration_merges_steps_4_and_5(self, step_data: dict):
        """
        Property: Steps 4 and 5 are correctly merged into state 3.
        
        Given step_data with data in steps 4 and/or 5,
        When the migration is applied,
        Then both should be merged into step_3 in the new structure.
        """
        # Only test if we have data in step 4 or 5
        has_step_4 = step_data.get('step_4') is not None and isinstance(step_data['step_4'], dict)
        has_step_5 = step_data.get('step_5') is not None and isinstance(step_data['step_5'], dict)
        
        assume(has_step_4 or has_step_5)
        
        # Apply migration
        _, new_step_data = migrate_step_data(5, step_data)
        
        # Verify merged data
        if has_step_4 or has_step_5:
            assert 'step_3' in new_step_data
            assert isinstance(new_step_data['step_3'], dict)
            
            # Verify step 4 data is in merged state
            if has_step_4:
                step_4_data = step_data['step_4']
                for key, value in step_4_data.items():
                    assert key in new_step_data['step_3']
                    assert new_step_data['step_3'][key] == value
            
            # Verify step 5 data is in merged state
            if has_step_5:
                step_5_data = step_data['step_5']
                for key, value in step_5_data.items():
                    assert key in new_step_data['step_3']
                    assert new_step_data['step_3'][key] == value
    
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    @given(
        current_step=current_step_strategy(),
        step_data=step_data_strategy()
    )
    def test_migration_does_not_lose_data(self, current_step: int, step_data: dict):
        """
        Property: No data is lost during migration.
        
        Given any 11-step onboarding state,
        When the migration is applied,
        Then all non-null step data should be present either in the new
        step_data or in the migration metadata.
        """
        # Count non-null steps in original data
        original_non_null_steps = sum(
            1 for i in range(1, 12)
            if step_data.get(f'step_{i}') is not None
        )
        
        # Apply migration
        new_current_step, new_step_data = migrate_step_data(current_step, step_data)
        
        # Verify metadata contains original data
        assert new_step_data['_migration_metadata']['original_step_data'] == step_data
        
        # Count steps in new data (excluding metadata and step_1 which is removed)
        new_steps = sum(
            1 for i in range(1, 10)
            if new_step_data.get(f'step_{i}') is not None
        )
        
        # We should have migrated all steps except step_1
        # Steps 4 and 5 merge into one, so we expect:
        # - If both step_4 and step_5 exist: original_count - 1 (for removed step_1) - 1 (for merge)
        # - Otherwise: original_count - 1 (for removed step_1)
        has_step_1 = step_data.get('step_1') is not None
        has_step_4 = step_data.get('step_4') is not None
        has_step_5 = step_data.get('step_5') is not None
        
        expected_new_steps = original_non_null_steps
        if has_step_1:
            expected_new_steps -= 1  # Step 1 is removed
        if has_step_4 and has_step_5:
            expected_new_steps -= 1  # Steps 4 and 5 merge into one
        
        assert new_steps == expected_new_steps
    
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    @given(
        current_step=current_step_strategy(),
        step_data=step_data_strategy()
    )
    def test_migration_new_current_step_in_valid_range(self, current_step: int, step_data: dict):
        """
        Property: New current_step is always in valid range (0-9).
        
        Given any current_step value,
        When the migration is applied,
        Then the new current_step should be between 0 and 9.
        """
        # Apply migration
        new_current_step, _ = migrate_step_data(current_step, step_data)
        
        # Verify range
        assert 0 <= new_current_step <= 9


# ============================================================================
# Integration Tests with Database
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.property
class TestMigrationIntegration:
    """Integration tests for migration with actual database operations."""
    
    @settings(
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
        max_examples=20,
        deadline=None  # Disable deadline for database operations
    )
    @given(
        current_step=st.integers(min_value=0, max_value=11),
        step_data=step_data_strategy()
    )
    async def test_migration_roundtrip_with_database(
        self,
        db_session: AsyncSession,
        current_step: int,
        step_data: dict
    ):
        """
        Property: Migration can be applied and data retrieved from database.
        
        Given any onboarding state,
        When migrated and stored in database,
        Then the data should be retrievable and match expected structure.
        """
        # Create a test user
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="test_hash",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.flush()
        
        # Apply migration logic
        new_current_step, new_step_data = migrate_step_data(current_step, step_data)
        
        # Create onboarding state with migrated data
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=new_current_step,
            is_complete=False,
            step_data=new_step_data,
            agent_history=[],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        await db_session.refresh(onboarding_state)
        
        # Verify data was stored correctly
        assert onboarding_state.current_step == new_current_step
        assert '_migration_metadata' in onboarding_state.step_data
        assert onboarding_state.step_data['_migration_metadata']['original_current_step'] == current_step
        assert onboarding_state.step_data['_migration_metadata']['original_step_data'] == step_data
        
        # Verify current_step is in valid range
        assert 0 <= onboarding_state.current_step <= 9
