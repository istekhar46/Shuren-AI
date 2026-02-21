"""Tests for timestamp validation and profile version immutability.

This module tests:
- Timestamp presence and automatic setting (created_at, updated_at)
- Profile version immutability (no deletion, no modification)
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.profile import UserProfile, UserProfileVersion
from app.models.workout import WorkoutPlan
from app.models.chat import ChatSession, ChatMessage


class TestTimestampValidation:
    """Test that timestamps are automatically set and updated correctly."""
    
    @pytest.mark.asyncio
    async def test_created_at_set_on_creation(self, db_session):
        """Test that created_at is automatically set when entity is created."""
        # Create a user
        user = User(
            email="timestamp_test@example.com",
            full_name="Timestamp Test",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Verify created_at is set and recent
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
        # Should be within last 5 seconds
        time_diff = datetime.now(timezone.utc) - user.created_at.replace(tzinfo=timezone.utc)
        assert time_diff.total_seconds() < 5
    
    @pytest.mark.asyncio
    async def test_updated_at_set_on_creation(self, db_session):
        """Test that updated_at is automatically set when entity is created."""
        # Create a user
        user = User(
            email="updated_test@example.com",
            full_name="Updated Test",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Verify updated_at is set and recent
        assert user.updated_at is not None
        assert isinstance(user.updated_at, datetime)
        # Should be within last 5 seconds
        time_diff = datetime.now(timezone.utc) - user.updated_at.replace(tzinfo=timezone.utc)
        assert time_diff.total_seconds() < 5
    
    @pytest.mark.asyncio
    async def test_updated_at_changes_on_modification(self, db_session):
        """Test that updated_at is updated when entity is modified."""
        # Create a user
        user = User(
            email="modify_test@example.com",
            full_name="Modify Test",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        original_updated_at = user.updated_at
        
        # Wait a moment to ensure timestamp difference
        import asyncio
        await asyncio.sleep(0.1)
        
        # Modify the user
        user.full_name = "Modified Name"
        await db_session.commit()
        await db_session.refresh(user)
        
        # Verify updated_at changed
        assert user.updated_at is not None
        assert user.updated_at > original_updated_at
    
    @pytest.mark.asyncio
    async def test_workout_plan_has_timestamps(self, db_session):
        """Test that workout plans have proper timestamps."""
        # Create a user first
        user = User(
            email="workout_timestamp@example.com",
            full_name="Workout Timestamp",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a workout plan
        workout_plan = WorkoutPlan(
            user_id=user.id,
            plan_name="Test Plan",
            duration_weeks=12,
            days_per_week=4,
            is_locked=False
        )
        db_session.add(workout_plan)
        await db_session.commit()
        await db_session.refresh(workout_plan)
        
        # Verify timestamps
        assert workout_plan.created_at is not None
        assert workout_plan.updated_at is not None
        time_diff = datetime.now(timezone.utc) - workout_plan.created_at.replace(tzinfo=timezone.utc)
        assert time_diff.total_seconds() < 5
    
    @pytest.mark.asyncio
    async def test_chat_session_has_timestamps(self, db_session):
        """Test that chat sessions have proper timestamps."""
        # Create a user first
        user = User(
            email="chat_timestamp@example.com",
            full_name="Chat Timestamp",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a chat session
        chat_session = ChatSession(
            user_id=user.id,
            session_type='general',
            status='active'
        )
        db_session.add(chat_session)
        await db_session.commit()
        await db_session.refresh(chat_session)
        
        # Verify timestamps
        assert chat_session.started_at is not None
        assert chat_session.last_activity_at is not None
        time_diff = datetime.now(timezone.utc) - chat_session.started_at.replace(tzinfo=timezone.utc)
        assert time_diff.total_seconds() < 5


class TestProfileVersionImmutability:
    """Test that profile versions cannot be deleted or modified."""
    
    @pytest.mark.asyncio
    async def test_profile_version_cannot_be_deleted(self, db_session):
        """Test that attempting to delete a profile version raises an error."""
        # Create a user and profile
        user = User(
            email="version_delete@example.com",
            full_name="Version Delete Test",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        profile = UserProfile(
            user_id=user.id,
            is_locked=True,
            fitness_level='intermediate'
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        # Create a profile version
        version = UserProfileVersion(
            profile_id=profile.id,
            version_number=1,
            change_reason="Initial version",
            snapshot={"fitness_level": "intermediate"}
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)
        
        # Attempt to delete the version - should raise IntegrityError
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.delete(version)
            await db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()
        assert "cannot be deleted" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_profile_version_snapshot_cannot_be_modified(self, db_session):
        """Test that attempting to modify a profile version snapshot raises an error."""
        # Create a user and profile
        user = User(
            email="version_modify@example.com",
            full_name="Version Modify Test",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        profile = UserProfile(
            user_id=user.id,
            is_locked=True,
            fitness_level='beginner'
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        # Create a profile version
        version = UserProfileVersion(
            profile_id=profile.id,
            version_number=1,
            change_reason="Initial version",
            snapshot={"fitness_level": "beginner"}
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)
        
        # Attempt to modify the snapshot - should raise IntegrityError
        with pytest.raises(IntegrityError) as exc_info:
            version.snapshot = {"fitness_level": "advanced"}
            await db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()
        assert "cannot be modified" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_profile_version_number_cannot_be_modified(self, db_session):
        """Test that attempting to modify a profile version number raises an error."""
        # Create a user and profile
        user = User(
            email="version_number@example.com",
            full_name="Version Number Test",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        profile = UserProfile(
            user_id=user.id,
            is_locked=True,
            fitness_level='intermediate'
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        # Create a profile version
        version = UserProfileVersion(
            profile_id=profile.id,
            version_number=1,
            change_reason="Initial version",
            snapshot={"fitness_level": "intermediate"}
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)
        
        # Attempt to modify the version number - should raise IntegrityError
        with pytest.raises(IntegrityError) as exc_info:
            version.version_number = 2
            await db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()
        assert "cannot be modified" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_profile_version_reason_cannot_be_modified(self, db_session):
        """Test that attempting to modify a profile version reason raises an error."""
        # Create a user and profile
        user = User(
            email="version_reason@example.com",
            full_name="Version Reason Test",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        profile = UserProfile(
            user_id=user.id,
            is_locked=True,
            fitness_level='advanced'
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        # Create a profile version
        version = UserProfileVersion(
            profile_id=profile.id,
            version_number=1,
            change_reason="Initial version",
            snapshot={"fitness_level": "advanced"}
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)
        
        # Attempt to modify the change reason - should raise IntegrityError
        with pytest.raises(IntegrityError) as exc_info:
            version.change_reason = "Modified reason"
            await db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()
        assert "cannot be modified" in str(exc_info.value).lower()
