"""Test script for onboarding migration from 11 steps to 9 states.

This script:
1. Creates test users with 11-step onboarding data
2. Runs the migration
3. Verifies the migration results
"""

import asyncio
import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


async def create_test_data(db: AsyncSession):
    """Create test users with 11-step onboarding data using raw SQL."""
    print("\n=== Creating Test Data ===")
    
    test_users = []
    
    # Test Case 1: User at step 2 (fitness_level) with some data
    user1_id = uuid4()
    user1_email = f"test_migration_1_{uuid4().hex[:8]}@example.com"
    await db.execute(
        text("""
            INSERT INTO users (id, email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES (:id, :email, :password, :name, :active, NOW(), NOW())
        """),
        {
            "id": user1_id,
            "email": user1_email,
            "password": "dummy_hash",
            "name": "Test User 1",
            "active": True
        }
    )
    
    await db.execute(
        text("""
            INSERT INTO onboarding_states (id, user_id, current_step, is_complete, step_data, created_at, updated_at)
            VALUES (:id, :user_id, :step, :complete, :data, NOW(), NOW())
        """),
        {
            "id": uuid4(),
            "user_id": user1_id,
            "step": 2,
            "complete": False,
            "data": json.dumps({
                "step_1": {"age": 25, "gender": "male", "height_cm": 175, "weight_kg": 70},
                "step_2": {"fitness_level": "beginner"}
            })
        }
    )
    test_users.append(("User 1 (Step 2)", user1_id))
    
    # Test Case 2: User at step 5 (physical_constraints) with steps 1-5 complete
    user2_id = uuid4()
    user2_email = f"test_migration_2_{uuid4().hex[:8]}@example.com"
    await db.execute(
        text("""
            INSERT INTO users (id, email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES (:id, :email, :password, :name, :active, NOW(), NOW())
        """),
        {
            "id": user2_id,
            "email": user2_email,
            "password": "dummy_hash",
            "name": "Test User 2",
            "active": True
        }
    )
    
    await db.execute(
        text("""
            INSERT INTO onboarding_states (id, user_id, current_step, is_complete, step_data, created_at, updated_at)
            VALUES (:id, :user_id, :step, :complete, :data, NOW(), NOW())
        """),
        {
            "id": uuid4(),
            "user_id": user2_id,
            "step": 5,
            "complete": False,
            "data": json.dumps({
                "step_1": {"age": 30, "gender": "female", "height_cm": 165, "weight_kg": 60},
                "step_2": {"fitness_level": "intermediate"},
                "step_3": {"goals": [{"goal_type": "fat_loss", "priority": 1}]},
                "step_4": {"target_weight_kg": 55, "target_body_fat_percentage": 20},
                "step_5": {"equipment": ["dumbbells", "resistance_bands"], "injuries": [], "limitations": ["lower_back_pain"]}
            })
        }
    )
    test_users.append(("User 2 (Step 5)", user2_id))
    
    # Test Case 3: User completed all 11 steps
    user3_id = uuid4()
    user3_email = f"test_migration_3_{uuid4().hex[:8]}@example.com"
    await db.execute(
        text("""
            INSERT INTO users (id, email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES (:id, :email, :password, :name, :active, NOW(), NOW())
        """),
        {
            "id": user3_id,
            "email": user3_email,
            "password": "dummy_hash",
            "name": "Test User 3",
            "active": True
        }
    )
    
    await db.execute(
        text("""
            INSERT INTO onboarding_states (id, user_id, current_step, is_complete, step_data, created_at, updated_at)
            VALUES (:id, :user_id, :step, :complete, :data, NOW(), NOW())
        """),
        {
            "id": uuid4(),
            "user_id": user3_id,
            "step": 11,
            "complete": True,
            "data": json.dumps({
                "step_1": {"age": 28, "gender": "male", "height_cm": 180, "weight_kg": 80},
                "step_2": {"fitness_level": "advanced"},
                "step_3": {"goals": [{"goal_type": "muscle_gain", "priority": 1}]},
                "step_4": {"target_weight_kg": 85, "target_body_fat_percentage": 12},
                "step_5": {"equipment": ["barbell", "dumbbells"], "injuries": [], "limitations": []},
                "step_6": {"diet_type": "omnivore", "allergies": [], "intolerances": [], "dislikes": []},
                "step_7": {"daily_calorie_target": 2500, "protein_percentage": 30, "carbs_percentage": 40, "fats_percentage": 30},
                "step_8": {"meals": [{"meal_name": "Breakfast", "scheduled_time": "08:00"}]},
                "step_9": {"workouts": [{"day_of_week": 1, "scheduled_time": "18:00"}]},
                "step_10": {"daily_water_target_ml": 3000, "reminder_frequency_minutes": 60},
                "step_11": {"interested_in_supplements": True, "current_supplements": ["protein"]}
            })
        }
    )
    test_users.append(("User 3 (Completed)", user3_id))
    
    # Test Case 4: User at step 0 (not started)
    user4_id = uuid4()
    user4_email = f"test_migration_4_{uuid4().hex[:8]}@example.com"
    await db.execute(
        text("""
            INSERT INTO users (id, email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES (:id, :email, :password, :name, :active, NOW(), NOW())
        """),
        {
            "id": user4_id,
            "email": user4_email,
            "password": "dummy_hash",
            "name": "Test User 4",
            "active": True
        }
    )
    
    await db.execute(
        text("""
            INSERT INTO onboarding_states (id, user_id, current_step, is_complete, step_data, created_at, updated_at)
            VALUES (:id, :user_id, :step, :complete, :data, NOW(), NOW())
        """),
        {
            "id": uuid4(),
            "user_id": user4_id,
            "step": 0,
            "complete": False,
            "data": json.dumps({})
        }
    )
    test_users.append(("User 4 (Not Started)", user4_id))
    
    await db.commit()
    
    print(f"✓ Created {len(test_users)} test users with 11-step onboarding data")
    for name, user_id in test_users:
        print(f"  - {name}: {user_id}")
    
    return test_users


async def verify_pre_migration_state(db: AsyncSession, test_users: list):
    """Verify the database state before migration."""
    print("\n=== Pre-Migration Verification ===")
    
    # Check if agent_history column exists (should not exist yet)
    result = await db.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'onboarding_states' 
        AND column_name = 'agent_history'
    """))
    agent_history_exists = result.fetchone() is not None
    print(f"✓ agent_history column exists: {agent_history_exists}")
    
    # Check current constraint
    result = await db.execute(text("""
        SELECT constraint_name, check_clause
        FROM information_schema.check_constraints
        WHERE constraint_name = 'valid_current_step'
    """))
    constraint = result.fetchone()
    if constraint:
        print(f"✓ Current constraint: {constraint[1]}")
    else:
        print("✓ No valid_current_step constraint found (expected before migration)")
    
    # Verify test data
    for name, user_id in test_users:
        result = await db.execute(
            text("SELECT current_step, step_data FROM onboarding_states WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        row = result.fetchone()
        if row:
            print(f"✓ {name}: current_step={row[0]}, has {len(row[1])} step entries")


async def verify_post_migration_state(db: AsyncSession, test_users: list):
    """Verify the database state after migration."""
    print("\n=== Post-Migration Verification ===")
    
    # Check if agent_history column exists
    result = await db.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'onboarding_states' 
        AND column_name = 'agent_history'
    """))
    agent_history_exists = result.fetchone() is not None
    print(f"✓ agent_history column exists: {agent_history_exists}")
    assert agent_history_exists, "agent_history column should exist after migration"
    
    # Check updated constraint
    result = await db.execute(text("""
        SELECT constraint_name, check_clause
        FROM information_schema.check_constraints
        WHERE constraint_name = 'valid_current_step'
    """))
    constraint = result.fetchone()
    if constraint:
        print(f"✓ Updated constraint: {constraint[1]}")
        # Verify it's the 0-9 constraint
        assert "current_step <= 9" in constraint[1] or "9 >= current_step" in constraint[1], \
            "Constraint should limit current_step to 9"
    else:
        print("✗ valid_current_step constraint not found!")
        raise AssertionError("Constraint should exist after migration")
    
    # Verify migrated data
    print("\n=== Data Migration Verification ===")
    
    expected_mappings = {
        "User 1 (Step 2)": {
            "old_step": 2,
            "new_step": 1,  # Step 2 (fitness_level) → State 1
            "expected_keys": ["step_1"]  # Should have state 1 data
        },
        "User 2 (Step 5)": {
            "old_step": 5,
            "new_step": 3,  # Step 5 (constraints) → State 3 (merged with step 4)
            "expected_keys": ["step_1", "step_2", "step_3"]  # Should have states 1-3
        },
        "User 3 (Completed)": {
            "old_step": 11,
            "new_step": 9,  # Step 11 → State 9
            "expected_keys": [f"step_{i}" for i in range(1, 10)]  # All 9 states
        },
        "User 4 (Not Started)": {
            "old_step": 0,
            "new_step": 0,
            "expected_keys": []  # No data
        }
    }
    
    for name, user_id in test_users:
        result = await db.execute(
            text("SELECT current_step, step_data, agent_history FROM onboarding_states WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        row = result.fetchone()
        
        if row:
            current_step = row[0]
            step_data = row[1]
            agent_history = row[2]
            
            expected = expected_mappings[name]
            
            print(f"\n{name}:")
            print(f"  Old step: {expected['old_step']} → New step: {current_step}")
            print(f"  Expected new step: {expected['new_step']}")
            
            # Verify current_step mapping
            assert current_step == expected['new_step'], \
                f"Expected current_step={expected['new_step']}, got {current_step}"
            print(f"  ✓ Current step correctly mapped")
            
            # Verify step data keys (excluding metadata)
            actual_keys = [k for k in step_data.keys() if k != '_migration_metadata']
            print(f"  Step data keys: {actual_keys}")
            
            # Verify migration metadata exists
            assert '_migration_metadata' in step_data, "Migration metadata should exist"
            metadata = step_data['_migration_metadata']
            print(f"  ✓ Migration metadata present")
            print(f"    - Original step: {metadata.get('original_current_step')}")
            print(f"    - Migration version: {metadata.get('migration_version')}")
            
            # Verify original data preserved
            assert 'original_step_data' in metadata, "Original data should be preserved"
            print(f"  ✓ Original data preserved in metadata")
            
            # Verify agent_history is initialized
            assert isinstance(agent_history, list), "agent_history should be a list"
            print(f"  ✓ agent_history initialized: {agent_history}")
            
            # Special verification for merged state 3 (User 2)
            if name == "User 2 (Step 5)":
                assert 'step_3' in step_data, "State 3 should exist"
                state_3_data = step_data['step_3']
                print(f"  State 3 (merged) data: {list(state_3_data.keys())}")
                # Should have data from both step 4 (target metrics) and step 5 (constraints)
                assert 'equipment' in state_3_data, "Should have equipment from step 5"
                assert 'target_weight_kg' in state_3_data, "Should have target_weight_kg from step 4"
                print(f"  ✓ State 3 correctly merged data from steps 4 and 5")
    
    print("\n=== All Verifications Passed ===")


async def main():
    """Main test function."""
    print("=" * 60)
    print("Testing Onboarding Migration: 11 Steps → 9 States")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Step 1: Create test data
        test_users = await create_test_data(db)
        
        # Step 2: Verify pre-migration state
        await verify_pre_migration_state(db, test_users)
        
        print("\n" + "=" * 60)
        print("Now run: poetry run alembic upgrade head")
        print("Then run this script again with --verify flag")
        print("=" * 60)


async def verify_only():
    """Verify migration results only."""
    print("=" * 60)
    print("Verifying Migration Results")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Get all test users (those with migration metadata)
        result = await db.execute(text("""
            SELECT u.email, u.id
            FROM users u
            JOIN onboarding_states os ON u.id = os.user_id
            WHERE u.email LIKE 'test_migration_%'
            AND os.deleted_at IS NULL
            ORDER BY u.email
        """))
        
        test_users = []
        for row in result.fetchall():
            email = row[0]
            user_id = row[1]
            # Extract user name from email
            if "test_migration_1" in email:
                name = "User 1 (Step 2)"
            elif "test_migration_2" in email:
                name = "User 2 (Step 5)"
            elif "test_migration_3" in email:
                name = "User 3 (Completed)"
            elif "test_migration_4" in email:
                name = "User 4 (Not Started)"
            else:
                name = email
            test_users.append((name, user_id))
        
        if not test_users:
            print("No test users found. Run without --verify flag first to create test data.")
            return
        
        print(f"\nFound {len(test_users)} test users")
        
        # Verify post-migration state
        await verify_post_migration_state(db, test_users)


if __name__ == "__main__":
    import sys
    
    if "--verify" in sys.argv:
        asyncio.run(verify_only())
    else:
        asyncio.run(main())
