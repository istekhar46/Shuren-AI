"""
Workout Plan Generator Service

Generates personalized workout plans based on user fitness level, goals, and preferences.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExerciseType(str, Enum):
    """Types of exercises."""
    COMPOUND = "compound"
    ISOLATION = "isolation"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"


class Exercise(BaseModel):
    """Individual exercise in a workout."""
    name: str
    type: ExerciseType
    sets: int
    reps: str  # e.g., "8-12", "15-20", "AMRAP"
    rest_seconds: int
    notes: str = ""


class WorkoutDay(BaseModel):
    """Single day's workout."""
    day_name: str  # e.g., "Day 1: Upper Body Push"
    exercises: List[Exercise]
    total_duration_minutes: int


class WorkoutPlan(BaseModel):
    """Complete workout plan."""
    frequency: int = Field(ge=2, le=7, description="Days per week")
    duration_minutes: int = Field(ge=20, le=180, description="Minutes per session")
    location: str  # "home" or "gym"
    equipment: List[str]
    training_split: str  # e.g., "Upper/Lower", "Push/Pull/Legs", "Full Body"
    workout_days: List[WorkoutDay]
    progression_strategy: str
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: str) -> str:
        if v.lower() not in ["home", "gym"]:
            raise ValueError("location must be 'home' or 'gym'")
        return v.lower()



class WorkoutPlanGenerator:
    """
    Service for generating personalized workout plans.
    
    Creates workout plans based on:
    - Fitness level (beginner/intermediate/advanced)
    - Primary goal (fat_loss/muscle_gain/general_fitness)
    - Preferences (frequency, location, equipment, duration)
    - Limitations (from fitness assessment)
    """
    
    async def generate_plan(
        self,
        fitness_level: str,
        primary_goal: str,
        frequency: int,
        location: str,
        duration_minutes: int,
        equipment: List[str],
        limitations: Optional[List[str]] = None
    ) -> WorkoutPlan:
        """
        Generate a workout plan based on user profile and preferences.
        
        Args:
            fitness_level: beginner/intermediate/advanced
            primary_goal: fat_loss/muscle_gain/general_fitness
            frequency: Workout days per week (2-7)
            location: home or gym
            duration_minutes: Session duration (20-180)
            equipment: Available equipment list
            limitations: Physical limitations to consider
            
        Returns:
            WorkoutPlan object with complete program
            
        Raises:
            ValueError: If parameters are invalid
        """
        logger.info(f"Generating workout plan for {fitness_level} level, {primary_goal} goal")
        logger.debug(f"Plan parameters: frequency={frequency}, location={location}")
        
        # Validate inputs
        self._validate_inputs(fitness_level, primary_goal, frequency, duration_minutes)
        
        # Determine training split based on frequency and level
        training_split = self._determine_training_split(frequency, fitness_level)
        
        # Generate workout days
        workout_days = self._generate_workout_days(
            training_split=training_split,
            fitness_level=fitness_level,
            primary_goal=primary_goal,
            location=location,
            equipment=equipment,
            duration_minutes=duration_minutes,
            limitations=limitations or []
        )
        
        # Determine progression strategy
        progression_strategy = self._determine_progression_strategy(fitness_level, primary_goal)
        
        return WorkoutPlan(
            frequency=frequency,
            duration_minutes=duration_minutes,
            location=location,
            equipment=equipment,
            training_split=training_split,
            workout_days=workout_days,
            progression_strategy=progression_strategy
        )

    
    async def modify_plan(
        self,
        current_plan: dict,
        modifications: dict
    ) -> WorkoutPlan:
        """
        Modify an existing workout plan based on user feedback.
        
        Args:
            current_plan: Current WorkoutPlan as dict
            modifications: Dict with requested changes
                Examples:
                - {"frequency": 3}  # Change to 3 days/week
                - {"duration_minutes": 45}  # Shorter sessions
                - {"training_split": "Full Body"}  # Change split
                
        Returns:
            Modified WorkoutPlan object
            
        Raises:
            ValueError: If modifications are invalid
        """
        logger.info(f"Modifying workout plan with changes: {modifications}")
        
        # Parse current plan (handle both dict and WorkoutPlan objects)
        if isinstance(current_plan, WorkoutPlan):
            plan = current_plan
        else:
            plan = WorkoutPlan(**current_plan)
        
        # Apply modifications
        if "frequency" in modifications:
            new_frequency = modifications["frequency"]
            if not (2 <= new_frequency <= 7):
                raise ValueError("frequency must be between 2 and 7 days per week")
            plan.frequency = new_frequency
            # Regenerate split and days for new frequency
            plan.training_split = self._determine_training_split(
                plan.frequency,
                self._infer_fitness_level(plan)
            )
            # Regenerate workout days
            plan.workout_days = self._generate_workout_days(
                training_split=plan.training_split,
                fitness_level=self._infer_fitness_level(plan),
                primary_goal=self._infer_primary_goal(plan),
                location=plan.location,
                equipment=plan.equipment,
                duration_minutes=plan.duration_minutes,
                limitations=[]
            )
        
        if "duration_minutes" in modifications:
            new_duration = modifications["duration_minutes"]
            if not (20 <= new_duration <= 180):
                raise ValueError("duration_minutes must be between 20 and 180")
            plan.duration_minutes = new_duration
            # Regenerate workout days with new duration
            plan.workout_days = self._generate_workout_days(
                training_split=plan.training_split,
                fitness_level=self._infer_fitness_level(plan),
                primary_goal=self._infer_primary_goal(plan),
                location=plan.location,
                equipment=plan.equipment,
                duration_minutes=plan.duration_minutes,
                limitations=[]
            )
        
        if "training_split" in modifications:
            plan.training_split = modifications["training_split"]
            # Regenerate workout days with new split
            plan.workout_days = self._generate_workout_days(
                training_split=plan.training_split,
                fitness_level=self._infer_fitness_level(plan),
                primary_goal=self._infer_primary_goal(plan),
                location=plan.location,
                equipment=plan.equipment,
                duration_minutes=plan.duration_minutes,
                limitations=[]
            )
        
        return plan

    
    def _validate_inputs(
        self,
        fitness_level: str,
        primary_goal: str,
        frequency: int,
        duration_minutes: int
    ) -> None:
        """Validate input parameters."""
        valid_levels = ["beginner", "intermediate", "advanced"]
        if fitness_level not in valid_levels:
            raise ValueError(f"fitness_level must be one of {valid_levels}")
        
        valid_goals = ["fat_loss", "muscle_gain", "general_fitness"]
        if primary_goal not in valid_goals:
            raise ValueError(f"primary_goal must be one of {valid_goals}")
        
        if not (2 <= frequency <= 7):
            raise ValueError("frequency must be between 2 and 7 days per week")
        
        if not (20 <= duration_minutes <= 180):
            raise ValueError("duration_minutes must be between 20 and 180")
    
    def _determine_training_split(self, frequency: int, fitness_level: str) -> str:
        """Determine appropriate training split based on frequency and level."""
        if fitness_level == "beginner":
            if frequency <= 3:
                return "Full Body"
            else:
                return "Upper/Lower"
        
        elif fitness_level == "intermediate":
            if frequency <= 3:
                return "Full Body"
            elif frequency == 4:
                return "Upper/Lower"
            else:
                return "Push/Pull/Legs"
        
        else:  # advanced
            if frequency <= 3:
                return "Full Body"
            elif frequency == 4:
                return "Upper/Lower"
            elif frequency == 5:
                return "Push/Pull/Legs"
            else:
                return "Body Part Split"
    
    def _determine_progression_strategy(self, fitness_level: str, primary_goal: str) -> str:
        """Determine progression strategy based on level and goal."""
        if fitness_level == "beginner":
            return "Linear progression: Add weight or reps each week. Focus on form mastery."
        elif fitness_level == "intermediate":
            if primary_goal == "muscle_gain":
                return "Progressive overload: Increase volume weekly. Deload every 4-6 weeks."
            else:
                return "Progressive overload with periodization. Track performance metrics."
        else:  # advanced
            return "Periodized training with mesocycles. Auto-regulation based on performance."

    
    def _generate_workout_days(
        self,
        training_split: str,
        fitness_level: str,
        primary_goal: str,
        location: str,
        equipment: List[str],
        duration_minutes: int,
        limitations: List[str]
    ) -> List[WorkoutDay]:
        """Generate workout days based on split and parameters."""
        logger.debug(f"Generating workout days for {training_split} split")
        
        if training_split == "Full Body":
            return self._generate_full_body_days(
                fitness_level, primary_goal, location, equipment, duration_minutes
            )
        elif training_split == "Upper/Lower":
            return self._generate_upper_lower_days(
                fitness_level, primary_goal, location, equipment, duration_minutes
            )
        elif training_split == "Push/Pull/Legs":
            return self._generate_ppl_days(
                fitness_level, primary_goal, location, equipment, duration_minutes
            )
        else:  # Body Part Split
            return self._generate_body_part_split_days(
                fitness_level, primary_goal, location, equipment, duration_minutes
            )
    
    def _generate_full_body_days(
        self,
        fitness_level: str,
        primary_goal: str,
        location: str,
        equipment: List[str],
        duration_minutes: int
    ) -> List[WorkoutDay]:
        """Generate full body workout days."""
        has_equipment = location == "gym" or len(equipment) >= 3
        
        # Determine sets and reps based on goal
        if primary_goal == "muscle_gain":
            sets, reps = 3, "8-12"
        elif primary_goal == "fat_loss":
            sets, reps = 3, "12-15"
        else:  # general_fitness
            sets, reps = 3, "10-12"
        
        # Build exercise list
        exercises = []
        
        if has_equipment:
            # Gym-based full body
            exercises = [
                Exercise(name="Barbell Squat", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Focus on depth"),
                Exercise(name="Bench Press", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Control the descent"),
                Exercise(name="Bent Over Row", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Keep back straight"),
                Exercise(name="Overhead Press", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Engage core"),
                Exercise(name="Romanian Deadlift", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Feel hamstring stretch"),
            ]
        else:
            # Home/bodyweight full body
            exercises = [
                Exercise(name="Bodyweight Squat", type=ExerciseType.COMPOUND, sets=sets, reps="15-20", rest_seconds=60, notes="Full range of motion"),
                Exercise(name="Push-ups", type=ExerciseType.COMPOUND, sets=sets, reps="AMRAP", rest_seconds=60, notes="Modify as needed"),
                Exercise(name="Inverted Rows", type=ExerciseType.COMPOUND, sets=sets, reps="10-15", rest_seconds=60, notes="Use table or bar"),
                Exercise(name="Pike Push-ups", type=ExerciseType.COMPOUND, sets=sets, reps="8-12", rest_seconds=60, notes="Shoulder focus"),
                Exercise(name="Glute Bridges", type=ExerciseType.COMPOUND, sets=sets, reps="15-20", rest_seconds=60, notes="Squeeze at top"),
            ]
        
        # Add cardio for fat loss
        if primary_goal == "fat_loss":
            exercises.append(
                Exercise(name="HIIT Cardio", type=ExerciseType.CARDIO, sets=1, reps="15 min", rest_seconds=0, notes="30s work, 30s rest intervals")
            )
        
        # Calculate total duration
        total_duration = self._calculate_workout_duration(exercises)
        
        # Create 3 full body days
        return [
            WorkoutDay(day_name=f"Day {i+1}: Full Body", exercises=exercises, total_duration_minutes=total_duration)
            for i in range(3)
        ]

    
    def _generate_upper_lower_days(
        self,
        fitness_level: str,
        primary_goal: str,
        location: str,
        equipment: List[str],
        duration_minutes: int
    ) -> List[WorkoutDay]:
        """Generate upper/lower split workout days."""
        has_equipment = location == "gym" or len(equipment) >= 3
        
        if primary_goal == "muscle_gain":
            sets, reps = 4, "8-12"
        elif primary_goal == "fat_loss":
            sets, reps = 3, "12-15"
        else:
            sets, reps = 3, "10-12"
        
        # Upper body exercises
        if has_equipment:
            upper_exercises = [
                Exercise(name="Bench Press", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Primary chest movement"),
                Exercise(name="Bent Over Row", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Primary back movement"),
                Exercise(name="Overhead Press", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Shoulder focus"),
                Exercise(name="Pull-ups/Lat Pulldown", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Vertical pull"),
                Exercise(name="Dumbbell Curls", type=ExerciseType.ISOLATION, sets=3, reps="10-12", rest_seconds=60, notes="Bicep isolation"),
                Exercise(name="Tricep Dips", type=ExerciseType.ISOLATION, sets=3, reps="10-12", rest_seconds=60, notes="Tricep isolation"),
            ]
        else:
            upper_exercises = [
                Exercise(name="Push-ups", type=ExerciseType.COMPOUND, sets=sets, reps="AMRAP", rest_seconds=60, notes="Chest and triceps"),
                Exercise(name="Inverted Rows", type=ExerciseType.COMPOUND, sets=sets, reps="10-15", rest_seconds=60, notes="Back focus"),
                Exercise(name="Pike Push-ups", type=ExerciseType.COMPOUND, sets=sets, reps="8-12", rest_seconds=60, notes="Shoulders"),
                Exercise(name="Diamond Push-ups", type=ExerciseType.ISOLATION, sets=3, reps="8-12", rest_seconds=60, notes="Triceps"),
            ]
        
        # Lower body exercises
        if has_equipment:
            lower_exercises = [
                Exercise(name="Barbell Squat", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=120, notes="Primary leg movement"),
                Exercise(name="Romanian Deadlift", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=120, notes="Hamstring focus"),
                Exercise(name="Leg Press", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Quad emphasis"),
                Exercise(name="Leg Curl", type=ExerciseType.ISOLATION, sets=3, reps="10-12", rest_seconds=60, notes="Hamstring isolation"),
                Exercise(name="Calf Raises", type=ExerciseType.ISOLATION, sets=3, reps="15-20", rest_seconds=60, notes="Calf development"),
            ]
        else:
            lower_exercises = [
                Exercise(name="Bodyweight Squat", type=ExerciseType.COMPOUND, sets=sets, reps="15-20", rest_seconds=60, notes="Leg strength"),
                Exercise(name="Bulgarian Split Squat", type=ExerciseType.COMPOUND, sets=sets, reps="10-12", rest_seconds=60, notes="Single leg work"),
                Exercise(name="Glute Bridges", type=ExerciseType.COMPOUND, sets=sets, reps="15-20", rest_seconds=60, notes="Glute activation"),
                Exercise(name="Walking Lunges", type=ExerciseType.COMPOUND, sets=sets, reps="12-15", rest_seconds=60, notes="Functional strength"),
            ]
        
        upper_duration = self._calculate_workout_duration(upper_exercises)
        lower_duration = self._calculate_workout_duration(lower_exercises)
        
        return [
            WorkoutDay(day_name="Day 1: Upper Body", exercises=upper_exercises, total_duration_minutes=upper_duration),
            WorkoutDay(day_name="Day 2: Lower Body", exercises=lower_exercises, total_duration_minutes=lower_duration),
        ]

    
    def _generate_ppl_days(
        self,
        fitness_level: str,
        primary_goal: str,
        location: str,
        equipment: List[str],
        duration_minutes: int
    ) -> List[WorkoutDay]:
        """Generate push/pull/legs workout days."""
        has_equipment = location == "gym" or len(equipment) >= 3
        
        if primary_goal == "muscle_gain":
            sets, reps = 4, "8-12"
        elif primary_goal == "fat_loss":
            sets, reps = 3, "12-15"
        else:
            sets, reps = 3, "10-12"
        
        # Push day (chest, shoulders, triceps)
        if has_equipment:
            push_exercises = [
                Exercise(name="Bench Press", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Chest focus"),
                Exercise(name="Overhead Press", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Shoulder focus"),
                Exercise(name="Incline Dumbbell Press", type=ExerciseType.COMPOUND, sets=3, reps=reps, rest_seconds=90, notes="Upper chest"),
                Exercise(name="Lateral Raises", type=ExerciseType.ISOLATION, sets=3, reps="12-15", rest_seconds=60, notes="Side delts"),
                Exercise(name="Tricep Pushdown", type=ExerciseType.ISOLATION, sets=3, reps="10-12", rest_seconds=60, notes="Tricep isolation"),
            ]
        else:
            push_exercises = [
                Exercise(name="Push-ups", type=ExerciseType.COMPOUND, sets=sets, reps="AMRAP", rest_seconds=60, notes="Chest and triceps"),
                Exercise(name="Pike Push-ups", type=ExerciseType.COMPOUND, sets=sets, reps="8-12", rest_seconds=60, notes="Shoulders"),
                Exercise(name="Diamond Push-ups", type=ExerciseType.ISOLATION, sets=3, reps="8-12", rest_seconds=60, notes="Triceps"),
            ]
        
        # Pull day (back, biceps)
        if has_equipment:
            pull_exercises = [
                Exercise(name="Deadlift", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=120, notes="Full back development"),
                Exercise(name="Pull-ups", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Vertical pull"),
                Exercise(name="Bent Over Row", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=90, notes="Horizontal pull"),
                Exercise(name="Face Pulls", type=ExerciseType.ISOLATION, sets=3, reps="15-20", rest_seconds=60, notes="Rear delts"),
                Exercise(name="Barbell Curls", type=ExerciseType.ISOLATION, sets=3, reps="10-12", rest_seconds=60, notes="Bicep focus"),
            ]
        else:
            pull_exercises = [
                Exercise(name="Inverted Rows", type=ExerciseType.COMPOUND, sets=sets, reps="10-15", rest_seconds=60, notes="Back focus"),
                Exercise(name="Chin-ups", type=ExerciseType.COMPOUND, sets=sets, reps="AMRAP", rest_seconds=90, notes="Back and biceps"),
            ]
        
        # Legs day
        if has_equipment:
            leg_exercises = [
                Exercise(name="Barbell Squat", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=120, notes="Quad focus"),
                Exercise(name="Romanian Deadlift", type=ExerciseType.COMPOUND, sets=sets, reps=reps, rest_seconds=120, notes="Hamstrings"),
                Exercise(name="Leg Press", type=ExerciseType.COMPOUND, sets=3, reps=reps, rest_seconds=90, notes="Quad emphasis"),
                Exercise(name="Leg Curl", type=ExerciseType.ISOLATION, sets=3, reps="10-12", rest_seconds=60, notes="Hamstring isolation"),
                Exercise(name="Calf Raises", type=ExerciseType.ISOLATION, sets=4, reps="15-20", rest_seconds=60, notes="Calf development"),
            ]
        else:
            leg_exercises = [
                Exercise(name="Bodyweight Squat", type=ExerciseType.COMPOUND, sets=sets, reps="15-20", rest_seconds=60, notes="Leg strength"),
                Exercise(name="Bulgarian Split Squat", type=ExerciseType.COMPOUND, sets=sets, reps="10-12", rest_seconds=60, notes="Single leg"),
                Exercise(name="Glute Bridges", type=ExerciseType.COMPOUND, sets=sets, reps="15-20", rest_seconds=60, notes="Glutes"),
            ]
        
        push_duration = self._calculate_workout_duration(push_exercises)
        pull_duration = self._calculate_workout_duration(pull_exercises)
        leg_duration = self._calculate_workout_duration(leg_exercises)
        
        return [
            WorkoutDay(day_name="Day 1: Push", exercises=push_exercises, total_duration_minutes=push_duration),
            WorkoutDay(day_name="Day 2: Pull", exercises=pull_exercises, total_duration_minutes=pull_duration),
            WorkoutDay(day_name="Day 3: Legs", exercises=leg_exercises, total_duration_minutes=leg_duration),
        ]

    
    def _generate_body_part_split_days(
        self,
        fitness_level: str,
        primary_goal: str,
        location: str,
        equipment: List[str],
        duration_minutes: int
    ) -> List[WorkoutDay]:
        """Generate body part split workout days (advanced)."""
        has_equipment = location == "gym" or len(equipment) >= 3
        
        sets, reps = 4, "8-12"
        
        if not has_equipment:
            # Fall back to PPL for home workouts
            return self._generate_ppl_days(fitness_level, primary_goal, location, equipment, duration_minutes)
        
        # Chest day
        chest_exercises = [
            Exercise(name="Barbell Bench Press", type=ExerciseType.COMPOUND, sets=4, reps=reps, rest_seconds=90, notes="Flat bench"),
            Exercise(name="Incline Dumbbell Press", type=ExerciseType.COMPOUND, sets=4, reps=reps, rest_seconds=90, notes="Upper chest"),
            Exercise(name="Cable Flyes", type=ExerciseType.ISOLATION, sets=3, reps="12-15", rest_seconds=60, notes="Chest stretch"),
            Exercise(name="Dips", type=ExerciseType.COMPOUND, sets=3, reps="AMRAP", rest_seconds=90, notes="Lower chest"),
        ]
        
        # Back day
        back_exercises = [
            Exercise(name="Deadlift", type=ExerciseType.COMPOUND, sets=4, reps="6-8", rest_seconds=120, notes="Heavy compound"),
            Exercise(name="Pull-ups", type=ExerciseType.COMPOUND, sets=4, reps=reps, rest_seconds=90, notes="Vertical pull"),
            Exercise(name="Barbell Row", type=ExerciseType.COMPOUND, sets=4, reps=reps, rest_seconds=90, notes="Horizontal pull"),
            Exercise(name="Face Pulls", type=ExerciseType.ISOLATION, sets=3, reps="15-20", rest_seconds=60, notes="Rear delts"),
        ]
        
        # Shoulder day
        shoulder_exercises = [
            Exercise(name="Overhead Press", type=ExerciseType.COMPOUND, sets=4, reps=reps, rest_seconds=90, notes="Primary shoulder"),
            Exercise(name="Lateral Raises", type=ExerciseType.ISOLATION, sets=4, reps="12-15", rest_seconds=60, notes="Side delts"),
            Exercise(name="Front Raises", type=ExerciseType.ISOLATION, sets=3, reps="12-15", rest_seconds=60, notes="Front delts"),
            Exercise(name="Rear Delt Flyes", type=ExerciseType.ISOLATION, sets=3, reps="12-15", rest_seconds=60, notes="Rear delts"),
        ]
        
        # Leg day
        leg_exercises = [
            Exercise(name="Barbell Squat", type=ExerciseType.COMPOUND, sets=4, reps=reps, rest_seconds=120, notes="Quad focus"),
            Exercise(name="Romanian Deadlift", type=ExerciseType.COMPOUND, sets=4, reps=reps, rest_seconds=120, notes="Hamstrings"),
            Exercise(name="Leg Press", type=ExerciseType.COMPOUND, sets=3, reps=reps, rest_seconds=90, notes="Quad emphasis"),
            Exercise(name="Leg Curl", type=ExerciseType.ISOLATION, sets=3, reps="10-12", rest_seconds=60, notes="Hamstring isolation"),
            Exercise(name="Calf Raises", type=ExerciseType.ISOLATION, sets=4, reps="15-20", rest_seconds=60, notes="Calves"),
        ]
        
        # Arms day
        arm_exercises = [
            Exercise(name="Barbell Curls", type=ExerciseType.ISOLATION, sets=4, reps="10-12", rest_seconds=60, notes="Bicep mass"),
            Exercise(name="Hammer Curls", type=ExerciseType.ISOLATION, sets=3, reps="10-12", rest_seconds=60, notes="Brachialis"),
            Exercise(name="Close-Grip Bench Press", type=ExerciseType.COMPOUND, sets=4, reps="8-10", rest_seconds=90, notes="Tricep mass"),
            Exercise(name="Tricep Pushdown", type=ExerciseType.ISOLATION, sets=3, reps="12-15", rest_seconds=60, notes="Tricep isolation"),
        ]
        
        chest_duration = self._calculate_workout_duration(chest_exercises)
        back_duration = self._calculate_workout_duration(back_exercises)
        shoulder_duration = self._calculate_workout_duration(shoulder_exercises)
        leg_duration = self._calculate_workout_duration(leg_exercises)
        arm_duration = self._calculate_workout_duration(arm_exercises)
        
        return [
            WorkoutDay(day_name="Day 1: Chest", exercises=chest_exercises, total_duration_minutes=chest_duration),
            WorkoutDay(day_name="Day 2: Back", exercises=back_exercises, total_duration_minutes=back_duration),
            WorkoutDay(day_name="Day 3: Shoulders", exercises=shoulder_exercises, total_duration_minutes=shoulder_duration),
            WorkoutDay(day_name="Day 4: Legs", exercises=leg_exercises, total_duration_minutes=leg_duration),
            WorkoutDay(day_name="Day 5: Arms", exercises=arm_exercises, total_duration_minutes=arm_duration),
        ]

    
    def _calculate_workout_duration(self, exercises: List[Exercise]) -> int:
        """Calculate estimated workout duration in minutes."""
        total_seconds = 0
        
        for exercise in exercises:
            # Estimate time per set (assume 30 seconds per set on average)
            set_time = 30
            # Add rest time
            total_seconds += (set_time + exercise.rest_seconds) * exercise.sets
        
        # Add 5 minutes for warmup and 5 minutes for cooldown
        total_minutes = (total_seconds // 60) + 10
        
        return total_minutes
    
    def _infer_fitness_level(self, plan: WorkoutPlan) -> str:
        """Infer fitness level from existing plan characteristics."""
        # Simple heuristic based on training split
        if plan.training_split == "Body Part Split":
            return "advanced"
        elif plan.training_split == "Push/Pull/Legs":
            return "intermediate"
        elif plan.frequency >= 5:
            return "advanced"
        elif plan.frequency >= 4:
            return "intermediate"
        else:
            return "beginner"
    
    def _infer_primary_goal(self, plan: WorkoutPlan) -> str:
        """Infer primary goal from existing plan characteristics."""
        # Check if plan has cardio exercises
        has_cardio = any(
            exercise.type == ExerciseType.CARDIO
            for day in plan.workout_days
            for exercise in day.exercises
        )
        
        if has_cardio:
            return "fat_loss"
        
        # Check average reps
        total_exercises = 0
        hypertrophy_exercises = 0
        
        for day in plan.workout_days:
            for exercise in day.exercises:
                if exercise.type in [ExerciseType.COMPOUND, ExerciseType.ISOLATION]:
                    total_exercises += 1
                    # Check if reps are in hypertrophy range (8-12)
                    if "8-12" in exercise.reps or "10-12" in exercise.reps:
                        hypertrophy_exercises += 1
        
        if total_exercises > 0 and hypertrophy_exercises / total_exercises > 0.6:
            return "muscle_gain"
        
        return "general_fitness"
