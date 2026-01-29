"""Tests for ProfileService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.profile_service import ProfileService
from app.models.profile import UserProfile, UserProfileVersion


class TestProfileService:
    """Test suite for ProfileService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def profile_service(self, mock_db):
        """Create ProfileService instance."""
        return ProfileService(mock_db)
    
    @pytest.fixture
    def sample_profile(self):
        """Create sample profile for testing."""
        profile = UserProfile(
            id=uuid4(),
            user_id=uuid4(),
            is_locked=False,
            fitness_level="intermediate"
        )
        # Mock relationships
        profile.fitness_goals = []
        profile.physical_constraints = []
        profile.dietary_preferences = None
        profile.meal_plan = None
        profile.meal_schedules = []
        profile.workout_schedules = []
        profile.hydration_preferences = None
        profile.lifestyle_baseline = None
        profile.versions = []
        return profile
    
    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, profile_service, mock_db):
        """Test get_profile raises 404 when profile not found."""
        # Mock database to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        user_id = uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            await profile_service.get_profile(user_id)
        
        assert exc_info.value.status_code == 404
        assert "Profile not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_lock_profile_sets_is_locked(self, profile_service, mock_db, sample_profile):
        """Test lock_profile sets is_locked to True."""
        # Mock get_profile to return sample profile
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_profile
        mock_result.scalar_one.return_value = sample_profile
        mock_db.execute.return_value = mock_result
        
        # Initially unlocked
        assert sample_profile.is_locked is False
        
        # Lock profile
        result = await profile_service.lock_profile(sample_profile.user_id)
        
        # Verify is_locked is True
        assert sample_profile.is_locked is True
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_update_profile_locked_without_unlock_raises_403(
        self, profile_service, mock_db, sample_profile
    ):
        """Test update_profile raises 403 when profile is locked without unlock."""
        # Set profile as locked
        sample_profile.is_locked = True
        
        # Mock get_profile to return locked profile
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_profile
        mock_db.execute.return_value = mock_result
        
        updates = {"fitness_level": "advanced"}
        reason = "Test update"
        
        with pytest.raises(HTTPException) as exc_info:
            await profile_service.update_profile(
                sample_profile.user_id,
                updates,
                reason
            )
        
        assert exc_info.value.status_code == 403
        assert "locked" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_create_profile_snapshot_structure(self, profile_service, sample_profile):
        """Test _create_profile_snapshot creates correct structure."""
        # Mock database execute for reload
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = sample_profile
        profile_service.db.execute = AsyncMock(return_value=mock_result)
        
        snapshot = await profile_service._create_profile_snapshot(sample_profile)
        
        # Verify snapshot has required keys
        assert "fitness_level" in snapshot
        assert "is_locked" in snapshot
        assert "fitness_goals" in snapshot
        assert "physical_constraints" in snapshot
        assert "dietary_preferences" in snapshot
        assert "meal_plan" in snapshot
        assert "meal_schedules" in snapshot
        assert "workout_schedules" in snapshot
        assert "hydration_preferences" in snapshot
        assert "lifestyle_baseline" in snapshot
        
        # Verify values
        assert snapshot["fitness_level"] == "intermediate"
        assert snapshot["is_locked"] is False
        assert isinstance(snapshot["fitness_goals"], list)
