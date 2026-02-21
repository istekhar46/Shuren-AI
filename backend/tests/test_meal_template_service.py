"""Unit tests for MealTemplateService."""

import pytest
import pytest_asyncio
from datetime import date, datetime, time
from uuid import uuid4
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.meal_template_service import MealTemplateService
from app.services.dish_service import DishService
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.preferences import MealPlan, MealSchedule, DietaryPreference
from app.models.profile import UserProfile
from app.models.user import User
from app.models.dish import Dish
from app.core.exceptions import ProfileLockedException
from app.core.security import hash_password


@pytest_asyncio.fixture
async def test_user_with_profile(db_session: AsyncSession):
    """Create a test user with a complete profile setup."""
    # Create user
    user = User(
        id=uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    
    # Create profile
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=False,
        fitness_level="intermediate"
    )
    db_session.add(profile)
    
    # Create meal plan
    meal_plan = MealPlan(
        id=uuid4(),
        profile_id=profile.id,
        daily_calorie_target=2500,
        protein_percentage=Decimal("30"),
        carbs_percentage=Decimal("45"),
        fats_percentage=Decimal("25")
    )
    db_session.add(meal_plan)
    
    # Create meal schedules
    meal_schedules = [
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="Breakfast",
            scheduled_time=time(8, 0),
            enable_notifications=True
        ),
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="Lunch",
            scheduled_time=time(13, 0),
            enable_notifications=True
        ),
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="Dinner",
            scheduled_time=time(19, 0),
            enable_notifications=True
        )
    ]
    for schedule in meal_schedules:
        db_session.add(schedule)
    
    # Create dietary preferences
    dietary_prefs = DietaryPreference(
        id=uuid4(),
        profile_id=profile.id,
        diet_type="omnivore",
        allergies=[],
        intolerances=[],
        dislikes=[]
    )
    db_session.add(dietary_prefs)
    
    await db_session.commit()
    await db_session.refresh(profile)
    
    return user, profile, meal_schedules


@pytest_asyncio.fixture
async def locked_profile(db_session: AsyncSession):
    """Create a locked profile for testing lock validation."""
    user = User(
        id=uuid4(),
        email="locked@example.com",
        hashed_password=hash_password("password123"),
        full_name="Locked User",
        is_active=True
    )
    db_session.add(user)
    
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=True,
        fitness_level="beginner"
    )
    db_session.add(profile)
    
    await db_session.commit()
    await db_session.refresh(profile)
    
    return user, profile


@pytest_asyncio.fixture
async def sample_dishes(db_session: AsyncSession):
    """Create sample dishes for testing."""
    dishes = []
    
    dish_data = [
        {
            "name": "Egg Omelette",
            "meal_type": "breakfast",
            "calories": 350,
            "protein_g": 25,
            "is_vegetarian": True,
        },
        {
            "name": "Chicken Curry",
            "meal_type": "lunch",
            "calories": 600,
            "protein_g": 45,
            "is_vegetarian": False,
        },
        {
            "name": "Grilled Fish",
            "meal_type": "dinner",
            "calories": 500,
            "protein_g": 40,
            "is_vegetarian": False,
        },
        {
            "name": "Paneer Paratha",
            "meal_type": "breakfast",
            "calories": 450,
            "protein_g": 20,
            "is_vegetarian": True,
        },
        {
            "name": "Dal Tadka",
            "meal_type": "lunch",
            "calories": 500,
            "protein_g": 20,
            "is_vegetarian": True,
        },
        {
            "name": "Vegetable Stir Fry",
            "meal_type": "dinner",
            "calories": 400,
            "protein_g": 15,
            "is_vegetarian": True,
        },
    ]
    
    for data in dish_data:
        dish = Dish(
            id=uuid4(),
            name=data["name"],
            cuisine_type="north_indian",
            meal_type=data["meal_type"],
            serving_size_g=300,
            calories=Decimal(str(data["calories"])),
            protein_g=Decimal(str(data["protein_g"])),
            carbs_g=Decimal("40"),
            fats_g=Decimal("15"),
            prep_time_minutes=10,
            cook_time_minutes=20,
            difficulty_level="easy",
            is_vegetarian=data["is_vegetarian"],
            is_vegan=False,
            is_gluten_free=False,
            is_dairy_free=False,
            is_nut_free=True,
            contains_allergens=[],
            is_active=True,
            popularity_score=100
        )
        db_session.add(dish)
        dishes.append(dish)
    
    await db_session.commit()
    return dishes


@pytest_asyncio.fixture
async def meal_template_with_meals(
    db_session: AsyncSession,
    test_user_with_profile,
    sample_dishes
):
    """Create a meal template with template meals for testing."""
    user, profile, meal_schedules = test_user_with_profile
    
    # Create template
    template = MealTemplate(
        id=uuid4(),
        profile_id=profile.id,
        week_number=1,
        is_active=True,
        generated_by="system",
        generation_reason="Test template"
    )
    db_session.add(template)
    await db_session.flush()
    
    # Create template meals for today
    today = date.today()
    day_of_week = today.weekday()
    
    # Assign dishes to meal schedules
    breakfast_dishes = [d for d in sample_dishes if d.meal_type == "breakfast"]
    lunch_dishes = [d for d in sample_dishes if d.meal_type == "lunch"]
    dinner_dishes = [d for d in sample_dishes if d.meal_type == "dinner"]
    
    meal_dish_mapping = {
        "Breakfast": breakfast_dishes,
        "Lunch": lunch_dishes,
        "Dinner": dinner_dishes
    }
    
    for schedule in meal_schedules:
        dishes_for_meal = meal_dish_mapping.get(schedule.meal_name, [])
        for idx, dish in enumerate(dishes_for_meal[:3]):  # Primary + 2 alternatives
            template_meal = TemplateMeal(
                id=uuid4(),
                template_id=template.id,
                meal_schedule_id=schedule.id,
                dish_id=dish.id,
                day_of_week=day_of_week,
                is_primary=(idx == 0),
                alternative_order=idx + 1
            )
            db_session.add(template_meal)
    
    await db_session.commit()
    await db_session.refresh(template)
    
    return template, profile, meal_schedules


class TestGetActiveTemplate:
    """Tests for get_active_template method."""
    
    @pytest.mark.asyncio
    async def test_get_active_template_success(
        self,
        db_session: AsyncSession,
        meal_template_with_meals
    ):
        """Test successfully retrieving active template."""
        template, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        # Get active template
        result = await service.get_active_template(profile.id)
        
        assert result is not None
        assert result.id == template.id
        assert result.profile_id == profile.id
        assert len(result.template_meals) > 0
    
    @pytest.mark.asyncio
    async def test_get_active_template_not_found(
        self,
        db_session: AsyncSession,
        test_user_with_profile
    ):
        """Test when no active template exists."""
        _, profile, _ = test_user_with_profile
        service = MealTemplateService(db_session)
        
        result = await service.get_active_template(profile.id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_active_template_week_rotation(
        self,
        db_session: AsyncSession,
        test_user_with_profile,
        sample_dishes
    ):
        """Test that correct week template is returned based on rotation."""
        _, profile, meal_schedules = test_user_with_profile
        service = MealTemplateService(db_session)
        
        # Calculate expected week number
        week_of_year = date.today().isocalendar()[1]
        expected_week = ((week_of_year - 1) % 4) + 1
        
        # Create template for expected week
        template = MealTemplate(
            id=uuid4(),
            profile_id=profile.id,
            week_number=expected_week,
            is_active=True,
            generated_by="system"
        )
        db_session.add(template)
        await db_session.commit()
        
        result = await service.get_active_template(profile.id)
        
        assert result is not None
        assert result.week_number == expected_week


class TestGetTodayMeals:
    """Tests for get_today_meals method."""
    
    @pytest.mark.asyncio
    async def test_get_today_meals_success(
        self,
        db_session: AsyncSession,
        meal_template_with_meals
    ):
        """Test successfully retrieving today's meals."""
        _, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        result = await service.get_today_meals(profile.id)
        
        assert result is not None
        assert result['date'] == date.today().isoformat()
        assert result['day_of_week'] == date.today().weekday()
        assert result['day_name'] == date.today().strftime('%A')
        assert len(result['meals']) > 0
        assert 'total_calories' in result
        assert 'total_protein_g' in result
        assert 'total_carbs_g' in result
        assert 'total_fats_g' in result
    
    @pytest.mark.asyncio
    async def test_get_today_meals_no_template(
        self,
        db_session: AsyncSession,
        test_user_with_profile
    ):
        """Test error when no active template exists."""
        _, profile, _ = test_user_with_profile
        service = MealTemplateService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.get_today_meals(profile.id)
        
        assert exc_info.value.status_code == 404
        assert "No active meal template found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_today_meals_nutritional_totals(
        self,
        db_session: AsyncSession,
        meal_template_with_meals
    ):
        """Test that nutritional totals are calculated correctly."""
        _, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        result = await service.get_today_meals(profile.id)
        
        # Verify totals are positive numbers
        assert result['total_calories'] > 0
        assert result['total_protein_g'] > 0
        assert result['total_carbs_g'] > 0
        assert result['total_fats_g'] > 0
    
    @pytest.mark.asyncio
    async def test_get_today_meals_sorted_by_time(
        self,
        db_session: AsyncSession,
        meal_template_with_meals
    ):
        """Test that meals are sorted by scheduled time."""
        _, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        result = await service.get_today_meals(profile.id)
        
        # Verify meals are sorted
        meals = result['meals']
        for i in range(len(meals) - 1):
            assert meals[i]['scheduled_time'] <= meals[i + 1]['scheduled_time']


class TestGetNextMeal:
    """Tests for get_next_meal method."""
    
    @pytest.mark.asyncio
    async def test_get_next_meal_found(
        self,
        db_session: AsyncSession,
        meal_template_with_meals
    ):
        """Test finding next meal after current time."""
        _, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        # Mock current time to be early morning
        with patch('app.services.meal_template_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.combine(date.today(), time(6, 0))
            mock_datetime.combine = datetime.combine
            
            result = await service.get_next_meal(profile.id)
        
        if result:  # Only assert if there's a meal after 6 AM
            assert 'meal_name' in result
            assert 'scheduled_time' in result
            assert 'time_until_meal_minutes' in result
            assert 'primary_dish' in result
            assert 'alternative_dishes' in result
    
    @pytest.mark.asyncio
    async def test_get_next_meal_none_remaining(
        self,
        db_session: AsyncSession,
        meal_template_with_meals
    ):
        """Test when no more meals remain today."""
        _, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        # Mock current time to be late night
        with patch('app.services.meal_template_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.combine(date.today(), time(23, 59))
            mock_datetime.combine = datetime.combine
            
            result = await service.get_next_meal(profile.id)
        
        # Should return None when no meals left
        assert result is None


class TestGetTemplateByWeek:
    """Tests for get_template_by_week method."""
    
    @pytest.mark.asyncio
    async def test_get_template_by_week_success(
        self,
        db_session: AsyncSession,
        meal_template_with_meals
    ):
        """Test retrieving template by specific week number."""
        template, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        result = await service.get_template_by_week(profile.id, 1)
        
        assert result is not None
        assert result.id == template.id
        assert result.week_number == 1
    
    @pytest.mark.asyncio
    async def test_get_template_by_week_not_found(
        self,
        db_session: AsyncSession,
        test_user_with_profile
    ):
        """Test when template for specific week doesn't exist."""
        _, profile, _ = test_user_with_profile
        service = MealTemplateService(db_session)
        
        result = await service.get_template_by_week(profile.id, 2)
        
        assert result is None


class TestGenerateTemplate:
    """Tests for generate_template method."""
    
    @pytest.mark.asyncio
    async def test_generate_template_success(
        self,
        db_session: AsyncSession,
        test_user_with_profile,
        sample_dishes
    ):
        """Test successfully generating a new template."""
        _, profile, meal_schedules = test_user_with_profile
        service = MealTemplateService(db_session)
        
        # Mock dish service to return dishes
        with patch.object(service.dish_service, 'get_dishes_for_meal_slot') as mock_get_dishes:
            mock_get_dishes.return_value = sample_dishes[:3]
            
            result = await service.generate_template(
                profile_id=profile.id,
                week_number=1,
                preferences="Test preferences"
            )
        
        # Refresh to load relationships
        await db_session.refresh(result, ['template_meals'])
        
        assert result is not None
        assert result.profile_id == profile.id
        assert result.week_number == 1
        assert result.generated_by == 'ai_agent'
        assert result.generation_reason == "Test preferences"
        assert len(result.template_meals) > 0
    
    @pytest.mark.asyncio
    async def test_generate_template_locked_profile(
        self,
        db_session: AsyncSession,
        locked_profile
    ):
        """Test that generation fails for locked profile."""
        _, profile = locked_profile
        service = MealTemplateService(db_session)
        
        with pytest.raises(ProfileLockedException):
            await service.generate_template(
                profile_id=profile.id,
                week_number=1
            )
    
    @pytest.mark.asyncio
    async def test_generate_template_missing_meal_plan(
        self,
        db_session: AsyncSession
    ):
        """Test error when profile has no meal plan."""
        # Create profile without meal plan
        user = User(
            id=uuid4(),
            email="nomealplan@example.com",
            hashed_password=hash_password("password123"),
            full_name="No Meal Plan User",
            is_active=True
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=False,
            fitness_level="beginner"
        )
        db_session.add(profile)
        await db_session.commit()
        
        service = MealTemplateService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.generate_template(
                profile_id=profile.id,
                week_number=1
            )
        
        assert exc_info.value.status_code == 400
        assert "meal plan and schedules" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_generate_template_creates_all_days(
        self,
        db_session: AsyncSession,
        test_user_with_profile,
        sample_dishes
    ):
        """Test that template is generated for all 7 days."""
        _, profile, meal_schedules = test_user_with_profile
        service = MealTemplateService(db_session)
        
        with patch.object(service.dish_service, 'get_dishes_for_meal_slot') as mock_get_dishes:
            mock_get_dishes.return_value = sample_dishes[:3]
            
            result = await service.generate_template(
                profile_id=profile.id,
                week_number=1
            )
        
        # Refresh to load relationships
        await db_session.refresh(result, ['template_meals'])
        
        # Should have meals for all 7 days
        days_covered = set(tm.day_of_week for tm in result.template_meals)
        assert len(days_covered) == 7
    
    @pytest.mark.asyncio
    async def test_generate_template_primary_and_alternatives(
        self,
        db_session: AsyncSession,
        test_user_with_profile,
        sample_dishes
    ):
        """Test that each meal slot has primary and alternative dishes."""
        _, profile, meal_schedules = test_user_with_profile
        service = MealTemplateService(db_session)
        
        with patch.object(service.dish_service, 'get_dishes_for_meal_slot') as mock_get_dishes:
            mock_get_dishes.return_value = sample_dishes[:3]
            
            result = await service.generate_template(
                profile_id=profile.id,
                week_number=1
            )
        
        # Refresh to load relationships
        await db_session.refresh(result, ['template_meals'])
        
        # Check that each meal slot has primary and alternatives
        for day in range(7):
            for schedule in meal_schedules:
                meals_for_slot = [
                    tm for tm in result.template_meals
                    if tm.day_of_week == day and tm.meal_schedule_id == schedule.id
                ]
                
                # Should have 3 dishes (1 primary + 2 alternatives)
                assert len(meals_for_slot) == 3
                
                # Exactly one should be primary
                primary_count = sum(1 for tm in meals_for_slot if tm.is_primary)
                assert primary_count == 1


class TestSwapDish:
    """Tests for swap_dish method."""
    
    @pytest.mark.asyncio
    async def test_swap_dish_success(
        self,
        db_session: AsyncSession,
        meal_template_with_meals,
        sample_dishes
    ):
        """Test successfully swapping a dish."""
        template, profile, meal_schedules = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        # Get a different dish to swap to
        new_dish = sample_dishes[0]
        today = date.today()
        day_of_week = today.weekday()
        
        result = await service.swap_dish(
            profile_id=profile.id,
            day_of_week=day_of_week,
            meal_name="Breakfast",
            new_dish_id=new_dish.id
        )
        
        assert result is not None
        assert result.id == template.id
    
    @pytest.mark.asyncio
    async def test_swap_dish_locked_profile(
        self,
        db_session: AsyncSession,
        locked_profile,
        sample_dishes
    ):
        """Test that swap fails for locked profile."""
        _, profile = locked_profile
        service = MealTemplateService(db_session)
        
        with pytest.raises(ProfileLockedException):
            await service.swap_dish(
                profile_id=profile.id,
                day_of_week=0,
                meal_name="Breakfast",
                new_dish_id=sample_dishes[0].id
            )
    
    @pytest.mark.asyncio
    async def test_swap_dish_no_template(
        self,
        db_session: AsyncSession,
        test_user_with_profile,
        sample_dishes
    ):
        """Test error when no active template exists."""
        _, profile, _ = test_user_with_profile
        service = MealTemplateService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.swap_dish(
                profile_id=profile.id,
                day_of_week=0,
                meal_name="Breakfast",
                new_dish_id=sample_dishes[0].id
            )
        
        assert exc_info.value.status_code == 404
        assert "No active template found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_swap_dish_invalid_meal_name(
        self,
        db_session: AsyncSession,
        meal_template_with_meals,
        sample_dishes
    ):
        """Test error when meal schedule doesn't exist."""
        _, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.swap_dish(
                profile_id=profile.id,
                day_of_week=0,
                meal_name="NonexistentMeal",
                new_dish_id=sample_dishes[0].id
            )
        
        assert exc_info.value.status_code == 404
        assert "Meal schedule" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_swap_dish_invalid_dish_id(
        self,
        db_session: AsyncSession,
        meal_template_with_meals
    ):
        """Test error when dish doesn't exist."""
        _, profile, _ = meal_template_with_meals
        service = MealTemplateService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.swap_dish(
                profile_id=profile.id,
                day_of_week=0,
                meal_name="Breakfast",
                new_dish_id=uuid4()  # Non-existent dish ID
            )
        
        assert exc_info.value.status_code == 404
        assert "Dish not found" in exc_info.value.detail


class TestHelperMethods:
    """Tests for helper methods."""
    
    def test_determine_meal_type(self, db_session: AsyncSession):
        """Test meal type determination from meal name."""
        service = MealTemplateService(db_session)
        
        assert service._determine_meal_type("Breakfast") == "breakfast"
        assert service._determine_meal_type("Lunch") == "lunch"
        assert service._determine_meal_type("Dinner") == "dinner"
        assert service._determine_meal_type("Pre-workout Snack") == "pre_workout"
        assert service._determine_meal_type("Post-workout Meal") == "post_workout"
        assert service._determine_meal_type("Evening Snack") == "snack"
    
    def test_calculate_meal_targets(self, db_session: AsyncSession):
        """Test meal target calculations."""
        service = MealTemplateService(db_session)
        
        daily_calories = 2500
        daily_protein = 150.0
        meals_per_day = 3
        
        # Test breakfast
        cal_target, protein_target = service._calculate_meal_targets(
            "Breakfast",
            daily_calories,
            daily_protein,
            meals_per_day
        )
        assert cal_target == 750  # 30% of 2500
        assert protein_target == 45  # 30% of 150
        
        # Test lunch
        cal_target, protein_target = service._calculate_meal_targets(
            "Lunch",
            daily_calories,
            daily_protein,
            meals_per_day
        )
        assert cal_target == 875  # 35% of 2500
        assert protein_target == 45  # 30% of 150
        
        # Test pre-workout
        cal_target, protein_target = service._calculate_meal_targets(
            "Pre-workout",
            daily_calories,
            daily_protein,
            meals_per_day
        )
        assert cal_target == 250  # 10% of 2500
        assert protein_target == 15  # 10% of 150
    
    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, db_session: AsyncSession):
        """Test error when profile doesn't exist."""
        service = MealTemplateService(db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            await service._get_profile(uuid4())
        
        assert exc_info.value.status_code == 404
        assert "Profile not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_profile_with_relationships(
        self,
        db_session: AsyncSession,
        test_user_with_profile
    ):
        """Test that profile is loaded with all relationships."""
        _, profile, _ = test_user_with_profile
        service = MealTemplateService(db_session)
        
        result = await service._get_profile(profile.id)
        
        assert result is not None
        assert result.id == profile.id
        # Relationships should be loaded
        assert hasattr(result, 'meal_plan')
        assert hasattr(result, 'meal_schedules')
        assert hasattr(result, 'dietary_preferences')


class TestDietaryPreferenceEnforcement:
    """Tests for dietary preference enforcement."""
    
    @pytest.mark.asyncio
    async def test_vegetarian_dishes_only(
        self,
        db_session: AsyncSession,
        test_user_with_profile,
        sample_dishes
    ):
        """Test that vegetarian users only get vegetarian dishes."""
        _, profile, meal_schedules = test_user_with_profile
        
        # Update dietary preferences to vegetarian
        from sqlalchemy import select
        result = await db_session.execute(
            select(DietaryPreference).where(DietaryPreference.profile_id == profile.id)
        )
        dietary_prefs = result.scalar_one()
        dietary_prefs.diet_type = "vegetarian"
        await db_session.commit()
        
        service = MealTemplateService(db_session)
        
        # Mock dish service to verify vegetarian filter is applied
        with patch.object(service.dish_service, 'get_dishes_for_meal_slot') as mock_get_dishes:
            vegetarian_dishes = [d for d in sample_dishes if d.is_vegetarian]
            mock_get_dishes.return_value = vegetarian_dishes[:3]
            
            result = await service.generate_template(
                profile_id=profile.id,
                week_number=1
            )
        
        # Verify dietary preferences were passed to dish service
        assert mock_get_dishes.called
        call_args = mock_get_dishes.call_args
        assert call_args[1]['dietary_preferences']['diet_type'] == 'vegetarian'
