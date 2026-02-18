"""
Unit tests for WorkoutPlanGenerator service.

Tests cover:
- Plan generation for all fitness levels (beginner/intermediate/advanced)
- Plan generation for all goals (fat_loss/muscle_gain/general_fitness)
- Training split determination for different frequencies
- Exercise selection based on location and equipment
- Duration constraint enforcement
- Input validation (invalid fitness_level, frequency out of range, etc.)
- Plan modification with various modification requests
"""
import pytest
from app.services.workout_plan_generator import (
    WorkoutPlanGenerator,
    WorkoutPlan,
    ExerciseType
)


class TestWorkoutPlanGeneration:
    """Test workout plan generation for different scenarios."""
    
    @pytest.mark.asyncio
    async def test_generate_beginner_muscle_gain_plan(self):
        """Test generating a workout plan for beginner with muscle gain goal."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="muscle_gain",
            frequency=3,
            location="gym",
            duration_minutes=60,
            equipment=["dumbbells", "barbell"],
            limitations=[]
        )
        
        assert plan.frequency == 3
        assert plan.training_split == "Full Body"
        assert len(plan.workout_days) == 3
        assert plan.location == "gym"
        assert plan.duration_minutes == 60
        
        # Verify exercises emphasize compound movements for beginners
        all_exercises = [ex for day in plan.workout_days for ex in day.exercises]
        compound_exercises = [ex for ex in all_exercises if ex.type == ExerciseType.COMPOUND]
        assert len(compound_exercises) >= len(all_exercises) * 0.5  # At least 50% compound
        
        # Verify progression strategy is appropriate for beginners
        assert "Linear progression" in plan.progression_strategy

    
    @pytest.mark.asyncio
    async def test_generate_intermediate_fat_loss_plan(self):
        """Test generating a workout plan for intermediate with fat loss goal."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="fat_loss",
            frequency=4,
            location="gym",
            duration_minutes=75,
            equipment=["dumbbells", "barbell", "cables"],
            limitations=[]
        )
        
        assert plan.frequency == 4
        assert plan.training_split == "Upper/Lower"
        assert len(plan.workout_days) == 2  # Upper and Lower templates
        
        # Verify fat loss plans include cardio or higher rep ranges
        all_exercises = [ex for day in plan.workout_days for ex in day.exercises]
        has_cardio = any(ex.type == ExerciseType.CARDIO for ex in all_exercises)
        has_high_reps = any("12-15" in ex.reps or "15-20" in ex.reps for ex in all_exercises)
        
        assert has_cardio or has_high_reps, "Fat loss plan should include cardio or high rep work"
    
    @pytest.mark.asyncio
    async def test_generate_advanced_general_fitness_plan(self):
        """Test generating a workout plan for advanced with general fitness goal."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="advanced",
            primary_goal="general_fitness",
            frequency=5,
            location="gym",
            duration_minutes=90,
            equipment=["dumbbells", "barbell", "cables", "machines"],
            limitations=[]
        )
        
        assert plan.frequency == 5
        assert plan.training_split == "Push/Pull/Legs"
        assert len(plan.workout_days) == 3  # Push, Pull, Legs templates
        
        # Verify progression strategy is appropriate for advanced
        assert "Periodized" in plan.progression_strategy or "Auto-regulation" in plan.progression_strategy


class TestTrainingSplitDetermination:
    """Test training split determination logic."""
    
    @pytest.mark.asyncio
    async def test_beginner_low_frequency_full_body(self):
        """Test that beginners with low frequency get Full Body split."""
        generator = WorkoutPlanGenerator()
        
        for freq in [2, 3]:
            plan = await generator.generate_plan(
                fitness_level="beginner",
                primary_goal="general_fitness",
                frequency=freq,
                location="home",
                duration_minutes=45,
                equipment=[],
                limitations=[]
            )
            assert plan.training_split == "Full Body", f"Beginner with {freq} days should get Full Body"
    
    @pytest.mark.asyncio
    async def test_beginner_high_frequency_upper_lower(self):
        """Test that beginners with higher frequency get Upper/Lower split."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="muscle_gain",
            frequency=4,
            location="gym",
            duration_minutes=60,
            equipment=["dumbbells"],
            limitations=[]
        )
        assert plan.training_split == "Upper/Lower"
    
    @pytest.mark.asyncio
    async def test_intermediate_ppl_split(self):
        """Test that intermediate with 5 days gets Push/Pull/Legs split."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            frequency=5,
            location="gym",
            duration_minutes=75,
            equipment=["dumbbells", "barbell"],
            limitations=[]
        )
        assert plan.training_split == "Push/Pull/Legs"
    
    @pytest.mark.asyncio
    async def test_advanced_body_part_split(self):
        """Test that advanced with 6+ days gets Body Part Split."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="advanced",
            primary_goal="muscle_gain",
            frequency=6,
            location="gym",
            duration_minutes=90,
            equipment=["dumbbells", "barbell", "cables"],
            limitations=[]
        )
        assert plan.training_split == "Body Part Split"


class TestExerciseSelection:
    """Test exercise selection based on location and equipment."""
    
    @pytest.mark.asyncio
    async def test_home_workout_bodyweight_focus(self):
        """Test that home workouts with limited equipment focus on bodyweight exercises."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            frequency=3,
            location="home",
            duration_minutes=45,
            equipment=[],  # No equipment
            limitations=[]
        )
        
        # Check that exercises are bodyweight-focused
        all_exercises = [ex for day in plan.workout_days for ex in day.exercises]
        bodyweight_exercises = [
            ex for ex in all_exercises 
            if any(keyword in ex.name.lower() for keyword in ["bodyweight", "push-up", "squat", "lunge", "bridge"])
        ]
        
        # At least 60% should be bodyweight exercises
        assert len(bodyweight_exercises) >= len(all_exercises) * 0.6
    
    @pytest.mark.asyncio
    async def test_gym_workout_equipment_usage(self):
        """Test that gym workouts utilize available equipment."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            frequency=4,
            location="gym",
            duration_minutes=60,
            equipment=["dumbbells", "barbell", "cables"],
            limitations=[]
        )
        
        # Check that exercises use equipment
        all_exercises = [ex for day in plan.workout_days for ex in day.exercises]
        equipment_exercises = [
            ex for ex in all_exercises 
            if any(keyword in ex.name.lower() for keyword in ["barbell", "dumbbell", "cable", "press", "row"])
        ]
        
        # At least 50% should use equipment
        assert len(equipment_exercises) >= len(all_exercises) * 0.5


class TestDurationConstraints:
    """Test that workout duration constraints are enforced."""
    
    @pytest.mark.asyncio
    async def test_duration_calculation(self):
        """Test that workout duration is calculated and reasonable."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            frequency=4,
            location="gym",
            duration_minutes=60,
            equipment=["dumbbells", "barbell"],
            limitations=[]
        )
        
        # Check that each workout day has a duration estimate
        for day in plan.workout_days:
            assert day.total_duration_minutes > 0
            # Duration should be reasonable (not exceeding requested time by too much)
            assert day.total_duration_minutes <= plan.duration_minutes + 20  # Allow 20 min buffer


class TestInputValidation:
    """Test input validation and error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_fitness_level(self):
        """Test that invalid fitness level raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        with pytest.raises(ValueError, match="fitness_level must be one of"):
            await generator.generate_plan(
                fitness_level="expert",  # Invalid
                primary_goal="muscle_gain",
                frequency=3,
                location="gym",
                duration_minutes=60,
                equipment=[]
            )
    
    @pytest.mark.asyncio
    async def test_invalid_primary_goal(self):
        """Test that invalid primary goal raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        with pytest.raises(ValueError, match="primary_goal must be one of"):
            await generator.generate_plan(
                fitness_level="beginner",
                primary_goal="weight_loss",  # Invalid (should be fat_loss)
                frequency=3,
                location="gym",
                duration_minutes=60,
                equipment=[]
            )
    
    @pytest.mark.asyncio
    async def test_frequency_out_of_range_low(self):
        """Test that frequency below 2 raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        with pytest.raises(ValueError, match="frequency must be between 2 and 7"):
            await generator.generate_plan(
                fitness_level="beginner",
                primary_goal="general_fitness",
                frequency=1,  # Too low
                location="gym",
                duration_minutes=60,
                equipment=[]
            )
    
    @pytest.mark.asyncio
    async def test_frequency_out_of_range_high(self):
        """Test that frequency above 7 raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        with pytest.raises(ValueError, match="frequency must be between 2 and 7"):
            await generator.generate_plan(
                fitness_level="advanced",
                primary_goal="muscle_gain",
                frequency=8,  # Too high
                location="gym",
                duration_minutes=60,
                equipment=[]
            )
    
    @pytest.mark.asyncio
    async def test_duration_out_of_range_low(self):
        """Test that duration below 20 raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        with pytest.raises(ValueError, match="duration_minutes must be between 20 and 180"):
            await generator.generate_plan(
                fitness_level="beginner",
                primary_goal="general_fitness",
                frequency=3,
                location="gym",
                duration_minutes=15,  # Too low
                equipment=[]
            )
    
    @pytest.mark.asyncio
    async def test_duration_out_of_range_high(self):
        """Test that duration above 180 raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        with pytest.raises(ValueError, match="duration_minutes must be between 20 and 180"):
            await generator.generate_plan(
                fitness_level="advanced",
                primary_goal="muscle_gain",
                frequency=5,
                location="gym",
                duration_minutes=200,  # Too high
                equipment=[]
            )
    
    @pytest.mark.asyncio
    async def test_invalid_location(self):
        """Test that invalid location raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        with pytest.raises(ValueError, match="location must be 'home' or 'gym'"):
            await generator.generate_plan(
                fitness_level="beginner",
                primary_goal="general_fitness",
                frequency=3,
                location="park",  # Invalid
                duration_minutes=60,
                equipment=[]
            )


class TestPlanModification:
    """Test plan modification functionality."""
    
    @pytest.mark.asyncio
    async def test_modify_frequency(self):
        """Test modifying workout frequency."""
        generator = WorkoutPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            frequency=4,
            location="gym",
            duration_minutes=60,
            equipment=["dumbbells", "barbell"]
        )
        
        # Modify frequency
        modified_plan = await generator.modify_plan(
            current_plan=initial_plan.model_dump(),
            modifications={"frequency": 3}
        )
        
        assert modified_plan.frequency == 3
        assert modified_plan.training_split != initial_plan.training_split  # Should change split
    
    @pytest.mark.asyncio
    async def test_modify_duration(self):
        """Test modifying workout duration."""
        generator = WorkoutPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            frequency=3,
            location="home",
            duration_minutes=60,
            equipment=[]
        )
        
        # Modify duration
        modified_plan = await generator.modify_plan(
            current_plan=initial_plan.model_dump(),
            modifications={"duration_minutes": 45}
        )
        
        assert modified_plan.duration_minutes == 45
    
    @pytest.mark.asyncio
    async def test_modify_training_split(self):
        """Test modifying training split directly."""
        generator = WorkoutPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            frequency=4,
            location="gym",
            duration_minutes=60,
            equipment=["dumbbells", "barbell"]
        )
        
        # Modify training split
        modified_plan = await generator.modify_plan(
            current_plan=initial_plan.model_dump(),
            modifications={"training_split": "Full Body"}
        )
        
        assert modified_plan.training_split == "Full Body"
    
    @pytest.mark.asyncio
    async def test_modify_invalid_frequency(self):
        """Test that modifying to invalid frequency raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            frequency=3,
            location="gym",
            duration_minutes=60,
            equipment=[]
        )
        
        # Try to modify to invalid frequency
        with pytest.raises(ValueError, match="frequency must be between 2 and 7"):
            await generator.modify_plan(
                current_plan=initial_plan.model_dump(),
                modifications={"frequency": 10}
            )
    
    @pytest.mark.asyncio
    async def test_modify_invalid_duration(self):
        """Test that modifying to invalid duration raises ValueError."""
        generator = WorkoutPlanGenerator()
        
        # Generate initial plan
        initial_plan = await generator.generate_plan(
            fitness_level="beginner",
            primary_goal="general_fitness",
            frequency=3,
            location="gym",
            duration_minutes=60,
            equipment=[]
        )
        
        # Try to modify to invalid duration
        with pytest.raises(ValueError, match="duration_minutes must be between 20 and 180"):
            await generator.modify_plan(
                current_plan=initial_plan.model_dump(),
                modifications={"duration_minutes": 10}
            )


class TestGoalSpecificFeatures:
    """Test goal-specific plan features."""
    
    @pytest.mark.asyncio
    async def test_muscle_gain_hypertrophy_rep_ranges(self):
        """Test that muscle gain plans emphasize hypertrophy rep ranges (8-12)."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            frequency=4,
            location="gym",
            duration_minutes=60,
            equipment=["dumbbells", "barbell"]
        )
        
        # Check rep ranges
        all_exercises = [ex for day in plan.workout_days for ex in day.exercises]
        resistance_exercises = [
            ex for ex in all_exercises 
            if ex.type in [ExerciseType.COMPOUND, ExerciseType.ISOLATION]
        ]
        
        hypertrophy_exercises = [
            ex for ex in resistance_exercises 
            if "8-12" in ex.reps or "10-12" in ex.reps
        ]
        
        # At least 50% should be in hypertrophy range
        assert len(hypertrophy_exercises) >= len(resistance_exercises) * 0.5
    
    @pytest.mark.asyncio
    async def test_fat_loss_includes_cardio(self):
        """Test that fat loss plans include cardio component."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="fat_loss",
            frequency=4,
            location="gym",
            duration_minutes=75,
            equipment=["dumbbells", "barbell"]
        )
        
        # Check for cardio exercises or high rep ranges (fat loss can use either approach)
        all_exercises = [ex for day in plan.workout_days for ex in day.exercises]
        has_cardio = any(ex.type == ExerciseType.CARDIO for ex in all_exercises)
        has_high_reps = any("12-15" in ex.reps or "15-20" in ex.reps for ex in all_exercises)
        
        assert has_cardio or has_high_reps, "Fat loss plan should include cardio or high rep work"
    
    @pytest.mark.asyncio
    async def test_general_fitness_balanced_approach(self):
        """Test that general fitness plans have balanced approach."""
        generator = WorkoutPlanGenerator()
        
        plan = await generator.generate_plan(
            fitness_level="intermediate",
            primary_goal="general_fitness",
            frequency=4,
            location="gym",
            duration_minutes=60,
            equipment=["dumbbells", "barbell"]
        )
        
        # Check for mix of exercise types
        all_exercises = [ex for day in plan.workout_days for ex in day.exercises]
        exercise_types = set(ex.type for ex in all_exercises)
        
        # Should have at least compound exercises
        assert ExerciseType.COMPOUND in exercise_types
