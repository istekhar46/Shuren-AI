"""Create test onboarding data for rollback testing.

This script creates sample onboarding states with migration metadata
so we can test the rollback from 9 states to 11 steps.
"""

import asyncio
import sys
import json
from uuid import uuid4
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def create_test_data():
    """Create test onboarding states with migration metadata."""
    print("=" * 70)
    print("Creating Test Data for Rollback Testing")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        try:
            # First, create test users with minimal required fields
            user1_id = uuid4()
            user2_id = uuid4()
            user3_id = uuid4()
            user4_id = uuid4()
            
            # Create users in the users table
            await session.execute(text("""
                INSERT INTO users (id, email, hashed_password, is_active, created_at, updated_at)
                VALUES 
                    (:user1_id, 'test1@example.com', 'hashed_password_1', true, NOW(), NOW()),
                    (:user2_id, 'test2@example.com', 'hashed_password_2', true, NOW(), NOW()),
                    (:user3_id, 'test3@example.com', 'hashed_password_3', true, NOW(), NOW()),
                    (:user4_id, 'test4@example.com', 'hashed_password_4', true, NOW(), NOW())
            """), {
                "user1_id": user1_id,
                "user2_id": user2_id,
                "user3_id": user3_id,
                "user4_id": user4_id
            })
            print("\n✓ Created 4 test users")
            
            # Test Case 1: User at state 1 (was step 2)
            step_data_1 = {
                "step_1": {"fitness_level": "beginner"},
                "_migration_metadata": {
                    "original_current_step": 2,
                    "original_step_data": {
                        "step_1": {"age": 25, "gender": "male", "height_cm": 175, "weight_kg": 70},
                        "step_2": {"fitness_level": "beginner"}
                    },
                    "migration_date": "2026-02-11",
                    "migration_version": "b2c3d4e5f6g7"
                }
            }
            
            await session.execute(text("""
                INSERT INTO onboarding_states 
                (id, user_id, current_step, is_complete, step_data, agent_history, created_at, updated_at)
                VALUES (:id, :user_id, :current_step, :is_complete, :step_data, :agent_history, NOW(), NOW())
            """), {
                "id": uuid4(),
                "user_id": user1_id,
                "current_step": 1,
                "is_complete": False,
                "step_data": json.dumps(step_data_1),
                "agent_history": json.dumps([])
            })
            print(f"\n✓ Created test user 1: State 1 (was step 2)")
            
            # Test Case 2: User at state 3 (merged from steps 4 & 5)
            step_data_2 = {
                "step_1": {"fitness_level": "intermediate"},
                "step_2": {"goals": [{"goal_type": "muscle_gain", "priority": 1}]},
                "step_3": {
                    "equipment": ["dumbbells", "resistance_bands"],
                    "injuries": [],
                    "limitations": ["lower_back_pain"],
                    "target_weight_kg": 75.0
                },
                "_migration_metadata": {
                    "original_current_step": 5,
                    "original_step_data": {
                        "step_1": {"age": 30, "gender": "female", "height_cm": 165, "weight_kg": 60},
                        "step_2": {"fitness_level": "intermediate"},
                        "step_3": {"goals": [{"goal_type": "muscle_gain", "priority": 1}]},
                        "step_4": {"target_weight_kg": 75.0},
                        "step_5": {
                            "equipment": ["dumbbells", "resistance_bands"],
                            "injuries": [],
                            "limitations": ["lower_back_pain"]
                        }
                    },
                    "migration_date": "2026-02-11",
                    "migration_version": "b2c3d4e5f6g7"
                }
            }
            
            await session.execute(text("""
                INSERT INTO onboarding_states 
                (id, user_id, current_step, is_complete, step_data, agent_history, created_at, updated_at)
                VALUES (:id, :user_id, :current_step, :is_complete, :step_data, :agent_history, NOW(), NOW())
            """), {
                "id": uuid4(),
                "user_id": user2_id,
                "current_step": 3,
                "is_complete": False,
                "step_data": json.dumps(step_data_2),
                "agent_history": json.dumps([
                    {"state": 1, "agent": "workout_planning", "timestamp": "2026-02-11T10:00:00"},
                    {"state": 2, "agent": "workout_planning", "timestamp": "2026-02-11T10:05:00"}
                ])
            })
            print(f"✓ Created test user 2: State 3 (merged from steps 4 & 5)")
            
            # Test Case 3: User completed all 9 states (was 11 steps)
            step_data_3 = {
                "step_1": {"fitness_level": "advanced"},
                "step_2": {"goals": [{"goal_type": "fat_loss", "priority": 1}]},
                "step_3": {
                    "equipment": ["full_gym"],
                    "injuries": [],
                    "limitations": [],
                    "target_weight_kg": 80.0,
                    "target_body_fat_percentage": 12.0
                },
                "step_4": {
                    "diet_type": "omnivore",
                    "allergies": [],
                    "intolerances": ["lactose"],
                    "dislikes": ["mushrooms"]
                },
                "step_5": {
                    "daily_calorie_target": 2500,
                    "protein_percentage": 30.0,
                    "carbs_percentage": 40.0,
                    "fats_percentage": 30.0
                },
                "step_6": {
                    "meals": [
                        {"meal_name": "Breakfast", "scheduled_time": "07:00", "enable_notifications": True},
                        {"meal_name": "Lunch", "scheduled_time": "12:00", "enable_notifications": True},
                        {"meal_name": "Dinner", "scheduled_time": "19:00", "enable_notifications": True}
                    ]
                },
                "step_7": {
                    "workouts": [
                        {"day_of_week": 1, "scheduled_time": "06:00", "enable_notifications": True},
                        {"day_of_week": 3, "scheduled_time": "06:00", "enable_notifications": True},
                        {"day_of_week": 5, "scheduled_time": "06:00", "enable_notifications": True}
                    ]
                },
                "step_8": {
                    "daily_water_target_ml": 3000,
                    "reminder_frequency_minutes": 60
                },
                "step_9": {
                    "interested_in_supplements": True,
                    "current_supplements": ["protein_powder", "creatine"]
                },
                "_migration_metadata": {
                    "original_current_step": 11,
                    "original_step_data": {
                        "step_1": {"age": 28, "gender": "male", "height_cm": 180, "weight_kg": 85},
                        "step_2": {"fitness_level": "advanced"},
                        "step_3": {"goals": [{"goal_type": "fat_loss", "priority": 1}]},
                        "step_4": {"target_weight_kg": 80.0, "target_body_fat_percentage": 12.0},
                        "step_5": {
                            "equipment": ["full_gym"],
                            "injuries": [],
                            "limitations": []
                        },
                        "step_6": {
                            "diet_type": "omnivore",
                            "allergies": [],
                            "intolerances": ["lactose"],
                            "dislikes": ["mushrooms"]
                        },
                        "step_7": {
                            "daily_calorie_target": 2500,
                            "protein_percentage": 30.0,
                            "carbs_percentage": 40.0,
                            "fats_percentage": 30.0
                        },
                        "step_8": {
                            "meals": [
                                {"meal_name": "Breakfast", "scheduled_time": "07:00", "enable_notifications": True},
                                {"meal_name": "Lunch", "scheduled_time": "12:00", "enable_notifications": True},
                                {"meal_name": "Dinner", "scheduled_time": "19:00", "enable_notifications": True}
                            ]
                        },
                        "step_9": {
                            "workouts": [
                                {"day_of_week": 1, "scheduled_time": "06:00", "enable_notifications": True},
                                {"day_of_week": 3, "scheduled_time": "06:00", "enable_notifications": True},
                                {"day_of_week": 5, "scheduled_time": "06:00", "enable_notifications": True}
                            ]
                        },
                        "step_10": {
                            "daily_water_target_ml": 3000,
                            "reminder_frequency_minutes": 60
                        },
                        "step_11": {
                            "interested_in_supplements": True,
                            "current_supplements": ["protein_powder", "creatine"]
                        }
                    },
                    "migration_date": "2026-02-11",
                    "migration_version": "b2c3d4e5f6g7"
                }
            }
            
            await session.execute(text("""
                INSERT INTO onboarding_states 
                (id, user_id, current_step, is_complete, step_data, agent_history, created_at, updated_at)
                VALUES (:id, :user_id, :current_step, :is_complete, :step_data, :agent_history, NOW(), NOW())
            """), {
                "id": uuid4(),
                "user_id": user3_id,
                "current_step": 9,
                "is_complete": True,
                "step_data": json.dumps(step_data_3),
                "agent_history": json.dumps([
                    {"state": i, "agent": "workout_planning" if i <= 3 else "diet_planning" if i <= 5 else "scheduler" if i <= 8 else "supplement", "timestamp": f"2026-02-11T10:{i:02d}:00"}
                    for i in range(1, 10)
                ])
            })
            print(f"✓ Created test user 3: State 9 (completed, was 11 steps)")
            
            # Test Case 4: User not started
            step_data_4 = {
                "_migration_metadata": {
                    "original_current_step": 0,
                    "original_step_data": {},
                    "migration_date": "2026-02-11",
                    "migration_version": "b2c3d4e5f6g7"
                }
            }
            
            await session.execute(text("""
                INSERT INTO onboarding_states 
                (id, user_id, current_step, is_complete, step_data, agent_history, created_at, updated_at)
                VALUES (:id, :user_id, :current_step, :is_complete, :step_data, :agent_history, NOW(), NOW())
            """), {
                "id": uuid4(),
                "user_id": user4_id,
                "current_step": 0,
                "is_complete": False,
                "step_data": json.dumps(step_data_4),
                "agent_history": json.dumps([])
            })
            print(f"✓ Created test user 4: State 0 (not started)")
            
            await session.commit()
            
            print("\n" + "=" * 70)
            print("✓ Test Data Creation Complete")
            print("=" * 70)
            print(f"\nCreated 4 test onboarding states:")
            print(f"  - User 1: State 1 (was step 2)")
            print(f"  - User 2: State 3 (merged from steps 4 & 5)")
            print(f"  - User 3: State 9 (completed, was 11 steps)")
            print(f"  - User 4: State 0 (not started)")
            print(f"\nAll records include migration metadata for rollback testing.")
            print("\nNow you can test the rollback:")
            print("  1. poetry run python scripts/test_migration_rollback.py")
            print("  2. poetry run alembic downgrade -1")
            print("  3. poetry run python scripts/test_migration_rollback.py --verify")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error creating test data: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False


if __name__ == "__main__":
    result = asyncio.run(create_test_data())
    sys.exit(0 if result else 1)
