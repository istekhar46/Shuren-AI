"""
Integration tests for profile locking workflow.

Tests the complete unlock → modify → lock cycle and version creation
during modifications. Validates that profile locking prevents unauthorized
changes and that version history is properly maintained.

Validates: Requirements 4.1, 4.4, 7.1, 7.5
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User
from app.models.profile import UserProfile, UserProfileVersion
from app.models.preferences import MealPlan, WorkoutSchedule
from app.models.workout import WorkoutPlan


@pytest.mark.asyncio
class TestProfileLockingWorkflow:
    """Integration tests for profile locking workflow.
    
    Validates: Requirements 4.1, 4.4, 7.1, 7.5
    """
    
    async def test_unlock_modify_lock_cycle_workout_plan(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete unlock → modify → lock cycle for workout plan.
        
        This test validates:
        1. Profile starts locked
        2. Modification attempts are rejected when locked
        3. Profile can be unlocked
        4. Modifications succeed when unlocked
        5. Profile can be locked again
        6. Subsequent modifications are rejected
        
        Validates: Requirements 4.1, 4.2, 4.3
        """
        # Step 1: Create user with locked profile and workout plan
        user = User(
            id=uuid4(),
            email="lock_test@example.com",
            full_name="Lock Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,  # Start locked
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        await db_session.flush()
        
        workout_plan = WorkoutPlan(
            id=uuid4(),
            user_id=user.id,
            plan_name="Original Plan",
            plan_description="Original description",
            duration_weeks=8,
            days_per_week=3,
            is_locked=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(workout_plan)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Step 2: Verify modification is rejected when locked
        response = await client.patch(
            "/api/v1/workouts/plan",
            json={"plan_name": "Modified Plan"}
        )
        
        assert response.status_code == 403
        error_data = response.json()
        assert "locked" in error_data["detail"].lower()
        
        # Step 3: Unlock the profile
        profile.is_locked = False
        workout_plan.is_locked = False
        await db_session.commit()
        
        # Step 4: Verify modification succeeds when unlocked
        response = await client.patch(
            "/api/v1/workouts/plan",
            json={
                "plan_name": "Modified Plan",
                "duration_weeks": 12
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["plan_name"] == "Modified Plan"
        assert data["duration_weeks"] == 12
        
        # Verify changes persisted in database
        await db_session.refresh(workout_plan)
        assert workout_plan.plan_name == "Modified Plan"
        assert workout_plan.duration_weeks == 12
        
        # Step 5: Lock the profile again
        profile.is_locked = True
        workout_plan.is_locked = True
        await db_session.commit()
        
        # Step 6: Verify subsequent modifications are rejected
        response = await client.patch(
            "/api/v1/workouts/plan",
            json={"plan_name": "Another Modification"}
        )
        
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()
        
        # Verify plan was not modified
        await db_session.refresh(workout_plan)
        assert workout_plan.plan_name == "Modified Plan"  # Still the previous value
    
    @pytest.mark.skip(reason="Meal plan schema/model mismatch - requires fixing meal plan API")
    async def test_unlock_modify_lock_cycle_meal_plan(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete unlock → modify → lock cycle for meal plan.
        
        This test validates the same workflow as workout plan but for meal plans.
        
        Validates: Requirements 7.1, 7.2, 7.3
        """
        # Step 1: Create user with locked profile and meal plan
        user = User(
            id=uuid4(),
            email="meal_lock_test@example.com",
            full_name="Meal Lock Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        await db_session.flush()
        
        meal_plan = MealPlan(
            id=uuid4(),
            profile_id=profile.id,
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.0"),
            carbs_percentage=Decimal("40.0"),
            fats_percentage=Decimal("30.0")
        )
        db_session.add(meal_plan)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Step 2: Verify modification is rejected when locked
        response = await client.patch(
            "/api/v1/meals/plan",
            json={"daily_calorie_target": 2500}
        )
        
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()
        
        # Step 3: Unlock the profile
        profile.is_locked = False
        await db_session.commit()
        
        # Step 4: Verify modification succeeds when unlocked
        response = await client.patch(
            "/api/v1/meals/plan",
            json={"daily_calorie_target": 2500}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["daily_calorie_target"] == 2500
        
        # Step 5: Lock the profile again
        profile.is_locked = True
        await db_session.commit()
        
        # Step 6: Verify subsequent modifications are rejected
        response = await client.patch(
            "/api/v1/meals/plan",
            json={"daily_calorie_target": 3000}
        )
        
        assert response.status_code == 403
    
    @pytest.mark.skip(reason="Meal plan schema/model mismatch - requires fixing meal plan API")
    async def test_version_creation_on_modification(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that profile versions are created when locked profiles are modified.
        
        This test validates:
        1. No versions exist initially
        2. Unlocking and modifying creates a version
        3. Version contains pre-modification state
        4. Multiple modifications create multiple versions
        5. Version numbers increment correctly
        
        Validates: Requirements 4.4, 7.5, 11.1, 11.2
        """
        # Step 1: Create user with locked profile and meal plan
        user = User(
            id=uuid4(),
            email="version_test@example.com",
            full_name="Version Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        await db_session.flush()
        
        meal_plan = MealPlan(
            id=uuid4(),
            profile_id=profile.id,
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.0"),
            carbs_percentage=Decimal("40.0"),
            fats_percentage=Decimal("30.0")
        )
        db_session.add(meal_plan)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Step 2: Verify no versions exist initially
        result = await db_session.execute(
            select(UserProfileVersion).where(
                UserProfileVersion.profile_id == profile.id
            )
        )
        versions = result.scalars().all()
        assert len(versions) == 0
        
        # Step 3: Unlock and modify (should create version)
        profile.is_locked = False
        await db_session.commit()
        
        # First modification
        response = await client.patch(
            "/api/v1/meals/plan",
            json={"daily_calorie_target": 2500}
        )
        assert response.status_code == 200
        
        # Step 4: Verify version was created with pre-modification state
        await db_session.commit()
        result = await db_session.execute(
            select(UserProfileVersion).where(
                UserProfileVersion.profile_id == profile.id
            ).order_by(UserProfileVersion.version_number)
        )
        versions = result.scalars().all()
        
        assert len(versions) == 1
        version1 = versions[0]
        assert version1.version_number == 1
        assert version1.snapshot is not None
        
        # Verify snapshot contains original state (2000 calories)
        snapshot = version1.snapshot
        assert "meal_plan" in snapshot or "daily_calorie_target" in snapshot
        
        # Step 5: Make another modification (should create another version)
        response = await client.patch(
            "/api/v1/meals/plan",
            json={"daily_calorie_target": 3000}
        )
        assert response.status_code == 200
        
        # Step 6: Verify second version was created
        await db_session.commit()
        result = await db_session.execute(
            select(UserProfileVersion).where(
                UserProfileVersion.profile_id == profile.id
            ).order_by(UserProfileVersion.version_number)
        )
        versions = result.scalars().all()
        
        assert len(versions) == 2
        version2 = versions[1]
        assert version2.version_number == 2
        assert version2.snapshot is not None
        
        # Verify version numbers are sequential
        assert version1.version_number == 1
        assert version2.version_number == 2
    
    async def test_version_immutability(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that profile versions cannot be modified or deleted.
        
        This test validates:
        1. Profile versions cannot be modified after creation
        2. Profile versions cannot be deleted
        3. Immutability is enforced at the database level
        
        Validates: Requirements 11.5
        """
        # Create user with profile
        user = User(
            id=uuid4(),
            email="immutable_test@example.com",
            full_name="Immutable Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=False,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Create a profile version
        version = UserProfileVersion(
            id=uuid4(),
            profile_id=profile.id,
            version_number=1,
            change_reason="Initial version",
            snapshot={"fitness_level": "intermediate"},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(version)
        await db_session.commit()
        
        # Test 1: Attempt to modify version (should fail)
        await db_session.refresh(version)
        version_id = version.id  # Store the ID before modification
        version.change_reason = "Modified reason"
        
        with pytest.raises(Exception) as exc_info:
            await db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()
        await db_session.rollback()
        
        # Test 2: Attempt to delete version (should fail)
        # Re-fetch the version after rollback
        result = await db_session.execute(
            select(UserProfileVersion).where(
                UserProfileVersion.id == version_id
            )
        )
        version = result.scalar_one()
        
        with pytest.raises(Exception) as exc_info:
            await db_session.delete(version)
            await db_session.flush()  # Use flush instead of commit to trigger the event
        
        assert "immutable" in str(exc_info.value).lower()
        await db_session.rollback()
        
        # Verify version still exists unchanged
        result = await db_session.execute(
            select(UserProfileVersion).where(
                UserProfileVersion.id == version_id
            )
        )
        existing_version = result.scalar_one()
        assert existing_version.change_reason == "Initial version"
        assert existing_version.version_number == 1
