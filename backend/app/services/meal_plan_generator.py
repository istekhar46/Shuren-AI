"""
Meal Plan Generator Service

Generates personalized meal plans based on user fitness level, goals, workout plan,
and dietary preferences.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MealType(str, Enum):
    """Types of meals."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class SampleMeal(BaseModel):
    """Sample meal idea."""
    meal_type: MealType
    name: str
    ingredients: List[str]
    approximate_calories: int
    approximate_protein_g: int
    approximate_carbs_g: int
    approximate_fats_g: int
    prep_time_minutes: int


class MealPlan(BaseModel):
    """Complete meal plan."""
    diet_type: str  # omnivore/vegetarian/vegan/pescatarian
    allergies: List[str]
    dislikes: List[str]
    meal_frequency: int = Field(ge=2, le=6, description="Meals per day")
    meal_prep_level: str  # low/medium/high
    daily_calories: int = Field(ge=1200, le=5000)
    protein_g: int
    carbs_g: int
    fats_g: int
    sample_meals: List[SampleMeal]
    meal_timing_suggestions: str
    
    @field_validator('diet_type')
    @classmethod
    def validate_diet_type(cls, v: str) -> str:
        valid_types = ["omnivore", "vegetarian", "vegan", "pescatarian"]
        if v.lower() not in valid_types:
            raise ValueError(f"diet_type must be one of {valid_types}")
        return v.lower()
    
    @field_validator('meal_prep_level')
    @classmethod
    def validate_meal_prep_level(cls, v: str) -> str:
        valid_levels = ["low", "medium", "high"]
        if v.lower() not in valid_levels:
            raise ValueError(f"meal_prep_level must be one of {valid_levels}")
        return v.lower()



class MealPlanGenerator:
    """
    Service for generating personalized meal plans.
    
    Creates meal plans based on:
    - Fitness level and primary goal
    - Workout plan (frequency and intensity)
    - Dietary preferences and restrictions
    - Meal frequency and prep willingness
    """
    
    # Standard calorie multipliers for TDEE estimation based on workout frequency
    ACTIVITY_MULTIPLIERS = {
        2: 1.2,   # 2 days/week - lightly active
        3: 1.375, # 3 days/week - moderately active
        4: 1.55,  # 4 days/week - very active
        5: 1.725, # 5+ days/week - extremely active
        6: 1.725,
        7: 1.9
    }
    
    async def generate_plan(
        self,
        fitness_level: str,
        primary_goal: str,
        workout_plan: dict,
        diet_type: str,
        allergies: List[str],
        dislikes: List[str],
        meal_frequency: int,
        meal_prep_level: str
    ) -> MealPlan:
        """
        Generate a meal plan based on user profile and preferences.
        
        Args:
            fitness_level: beginner/intermediate/advanced
            primary_goal: fat_loss/muscle_gain/general_fitness
            workout_plan: Workout plan dict with frequency and intensity
            diet_type: omnivore/vegetarian/vegan/pescatarian
            allergies: List of allergies/intolerances
            dislikes: List of disliked foods
            meal_frequency: Meals per day (2-6)
            meal_prep_level: low/medium/high
            
        Returns:
            MealPlan object with complete nutrition strategy
            
        Raises:
            ValueError: If parameters are invalid
        """
        logger.info(f"Generating meal plan for {primary_goal} goal with {diet_type} diet")
        logger.debug(f"Meal frequency: {meal_frequency}, prep level: {meal_prep_level}")
        
        # Validate inputs
        self._validate_inputs(diet_type, meal_frequency, meal_prep_level)
        
        # Calculate calorie target based on goal and workout plan
        workout_frequency = workout_plan.get("frequency", 3)
        daily_calories = self._calculate_calorie_target(primary_goal, workout_frequency)
        
        # Calculate macro breakdown
        protein_g, carbs_g, fats_g = self._calculate_macros(
            daily_calories=daily_calories,
            primary_goal=primary_goal,
            workout_frequency=workout_frequency
        )
        
        # Generate sample meals
        sample_meals = self._generate_sample_meals(
            diet_type=diet_type,
            allergies=allergies,
            dislikes=dislikes,
            meal_frequency=meal_frequency,
            meal_prep_level=meal_prep_level,
            daily_calories=daily_calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fats_g=fats_g
        )
        
        # Generate meal timing suggestions
        meal_timing = self._generate_meal_timing(meal_frequency, workout_frequency)
        
        return MealPlan(
            diet_type=diet_type,
            allergies=allergies,
            dislikes=dislikes,
            meal_frequency=meal_frequency,
            meal_prep_level=meal_prep_level,
            daily_calories=daily_calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fats_g=fats_g,
            sample_meals=sample_meals,
            meal_timing_suggestions=meal_timing
        )

    
    async def modify_plan(
        self,
        current_plan: dict,
        modifications: dict
    ) -> MealPlan:
        """
        Modify an existing meal plan based on user feedback.
        
        Args:
            current_plan: Current MealPlan as dict
            modifications: Dict with requested changes
                Examples:
                - {"daily_calories": 2200}  # Adjust calories
                - {"protein_g": 180}  # Increase protein
                - {"meal_frequency": 4}  # Change meal count
                
        Returns:
            Modified MealPlan object
            
        Raises:
            ValueError: If modifications are invalid
        """
        logger.info(f"Modifying meal plan with changes: {modifications}")
        
        # Parse current plan (handle both dict and MealPlan objects)
        if isinstance(current_plan, MealPlan):
            plan = current_plan
        else:
            plan = MealPlan(**current_plan)
        
        # Apply modifications
        if "daily_calories" in modifications:
            new_calories = modifications["daily_calories"]
            if not (1200 <= new_calories <= 5000):
                raise ValueError("daily_calories must be between 1200 and 5000")
            
            # Recalculate macros proportionally
            old_calories = (plan.protein_g * 4) + (plan.carbs_g * 4) + (plan.fats_g * 9)
            if old_calories > 0:
                ratio = new_calories / old_calories
                plan.protein_g = int(plan.protein_g * ratio)
                plan.carbs_g = int(plan.carbs_g * ratio)
                plan.fats_g = int(plan.fats_g * ratio)
            
            plan.daily_calories = new_calories
            
            # Regenerate sample meals for new calorie target
            plan.sample_meals = self._generate_sample_meals(
                diet_type=plan.diet_type,
                allergies=plan.allergies,
                dislikes=plan.dislikes,
                meal_frequency=plan.meal_frequency,
                meal_prep_level=plan.meal_prep_level,
                daily_calories=plan.daily_calories,
                protein_g=plan.protein_g,
                carbs_g=plan.carbs_g,
                fats_g=plan.fats_g
            )
        
        if "protein_g" in modifications:
            new_protein = modifications["protein_g"]
            if new_protein < 0:
                raise ValueError("protein_g must be positive")
            
            # Adjust other macros to maintain calorie target
            protein_calories = new_protein * 4
            old_protein_calories = plan.protein_g * 4
            calorie_diff = protein_calories - old_protein_calories
            
            # Distribute the difference between carbs and fats
            carb_adjustment = int((calorie_diff * 0.6) / 4)
            fat_adjustment = int((calorie_diff * 0.4) / 9)
            
            plan.protein_g = new_protein
            plan.carbs_g = max(0, plan.carbs_g - carb_adjustment)
            plan.fats_g = max(0, plan.fats_g - fat_adjustment)
        
        if "meal_frequency" in modifications:
            new_frequency = modifications["meal_frequency"]
            if not (2 <= new_frequency <= 6):
                raise ValueError("meal_frequency must be between 2 and 6")
            
            plan.meal_frequency = new_frequency
            
            # Regenerate meal timing and sample meals
            plan.meal_timing_suggestions = self._generate_meal_timing(
                plan.meal_frequency,
                3  # Default workout frequency
            )
            plan.sample_meals = self._generate_sample_meals(
                diet_type=plan.diet_type,
                allergies=plan.allergies,
                dislikes=plan.dislikes,
                meal_frequency=plan.meal_frequency,
                meal_prep_level=plan.meal_prep_level,
                daily_calories=plan.daily_calories,
                protein_g=plan.protein_g,
                carbs_g=plan.carbs_g,
                fats_g=plan.fats_g
            )
        
        return plan

    
    def _validate_inputs(
        self,
        diet_type: str,
        meal_frequency: int,
        meal_prep_level: str
    ) -> None:
        """Validate input parameters."""
        valid_diet_types = ["omnivore", "vegetarian", "vegan", "pescatarian"]
        if diet_type not in valid_diet_types:
            raise ValueError(f"diet_type must be one of {valid_diet_types}")
        
        if not (2 <= meal_frequency <= 6):
            raise ValueError("meal_frequency must be between 2 and 6")
        
        valid_prep_levels = ["low", "medium", "high"]
        if meal_prep_level not in valid_prep_levels:
            raise ValueError(f"meal_prep_level must be one of {valid_prep_levels}")
    
    def _calculate_calorie_target(self, primary_goal: str, workout_frequency: int) -> int:
        """Calculate daily calorie target based on goal and activity level."""
        # Simplified calculation - using average TDEE of 2000 calories as baseline
        # Real implementation would use user's weight, age, height, gender
        base_tdee = 2000
        activity_multiplier = self.ACTIVITY_MULTIPLIERS.get(workout_frequency, 1.375)
        tdee = int(base_tdee * activity_multiplier)
        
        if primary_goal == "muscle_gain":
            return tdee + 400  # Surplus for muscle gain
        elif primary_goal == "fat_loss":
            return tdee - 400  # Deficit for fat loss
        else:  # general_fitness
            return tdee  # Maintenance
    
    def _calculate_macros(
        self,
        daily_calories: int,
        primary_goal: str,
        workout_frequency: int
    ) -> tuple[int, int, int]:
        """Calculate protein, carbs, and fats in grams."""
        # Protein calculation based on goal
        # Using 75kg as average weight - real implementation would use actual weight
        avg_weight_kg = 75
        
        if primary_goal == "muscle_gain":
            protein_g = int(avg_weight_kg * 2.0)  # 2.0g/kg for muscle gain
        elif primary_goal == "fat_loss":
            protein_g = int(avg_weight_kg * 1.8)  # 1.8g/kg for fat loss
        else:  # general_fitness
            protein_g = int(avg_weight_kg * 1.6)  # 1.6g/kg for maintenance
        
        # Protein calories
        protein_calories = protein_g * 4
        
        # Remaining calories for carbs and fats
        remaining_calories = daily_calories - protein_calories
        
        # Fat calculation (25-30% of total calories)
        fat_percentage = 0.28
        fat_calories = int(remaining_calories * fat_percentage)
        fats_g = int(fat_calories / 9)
        
        # Carbs get the rest
        carb_calories = remaining_calories - fat_calories
        carbs_g = int(carb_calories / 4)
        
        # Validate macro sum equals calories within 10%
        calculated_calories = (protein_g * 4) + (carbs_g * 4) + (fats_g * 9)
        tolerance = daily_calories * 0.1
        
        if abs(calculated_calories - daily_calories) > tolerance:
            logger.warning(f"Macro sum {calculated_calories} differs from target {daily_calories}")
            # Adjust carbs to match target
            carb_adjustment = (daily_calories - calculated_calories) / 4
            carbs_g = int(carbs_g + carb_adjustment)
        
        return protein_g, carbs_g, fats_g

    
    def _generate_sample_meals(
        self,
        diet_type: str,
        allergies: List[str],
        dislikes: List[str],
        meal_frequency: int,
        meal_prep_level: str,
        daily_calories: int,
        protein_g: int,
        carbs_g: int,
        fats_g: int
    ) -> List[SampleMeal]:
        """Generate 3-5 sample meal ideas that fit the plan."""
        sample_meals = []
        calories_per_meal = daily_calories // meal_frequency
        protein_per_meal = protein_g // meal_frequency
        carbs_per_meal = carbs_g // meal_frequency
        fats_per_meal = fats_g // meal_frequency
        
        # Normalize allergies and dislikes to lowercase for comparison
        allergies_lower = [a.lower() for a in allergies]
        dislikes_lower = [d.lower() for d in dislikes]
        
        # Helper function to check if ingredients are allowed
        def is_allowed(ingredients: List[str]) -> bool:
            ingredients_lower = [i.lower() for i in ingredients]
            # Check allergies
            for allergen in allergies_lower:
                if any(allergen in ing for ing in ingredients_lower):
                    return False
            # Check dislikes
            for dislike in dislikes_lower:
                if any(dislike in ing for ing in ingredients_lower):
                    return False
            return True
        
        # Breakfast options
        if diet_type in ["omnivore", "pescatarian"]:
            if "eggs" not in allergies_lower and "egg" not in dislikes_lower:
                ingredients = ["eggs", "whole wheat toast", "avocado"]
                if is_allowed(ingredients):
                    sample_meals.append(SampleMeal(
                        meal_type=MealType.BREAKFAST,
                        name="Scrambled Eggs with Avocado Toast",
                        ingredients=ingredients,
                        approximate_calories=calories_per_meal,
                        approximate_protein_g=protein_per_meal,
                        approximate_carbs_g=carbs_per_meal,
                        approximate_fats_g=fats_per_meal,
                        prep_time_minutes=10
                    ))
        
        if diet_type in ["vegetarian", "vegan", "omnivore", "pescatarian"]:
            ingredients = ["oats", "banana", "almond butter", "berries"]
            if is_allowed(ingredients):
                sample_meals.append(SampleMeal(
                    meal_type=MealType.BREAKFAST,
                    name="Protein Oatmeal Bowl",
                    ingredients=ingredients,
                    approximate_calories=calories_per_meal,
                    approximate_protein_g=protein_per_meal,
                    approximate_carbs_g=carbs_per_meal,
                    approximate_fats_g=fats_per_meal,
                    prep_time_minutes=8
                ))
        
        # Lunch options
        if diet_type == "omnivore":
            ingredients = ["chicken breast", "brown rice", "broccoli", "olive oil"]
            if is_allowed(ingredients):
                sample_meals.append(SampleMeal(
                    meal_type=MealType.LUNCH,
                    name="Grilled Chicken with Rice and Vegetables",
                    ingredients=ingredients,
                    approximate_calories=calories_per_meal,
                    approximate_protein_g=protein_per_meal,
                    approximate_carbs_g=carbs_per_meal,
                    approximate_fats_g=fats_per_meal,
                    prep_time_minutes=25
                ))
        
        if diet_type in ["vegetarian", "vegan"]:
            ingredients = ["chickpeas", "quinoa", "spinach", "tahini"]
            if is_allowed(ingredients):
                sample_meals.append(SampleMeal(
                    meal_type=MealType.LUNCH,
                    name="Chickpea Buddha Bowl",
                    ingredients=ingredients,
                    approximate_calories=calories_per_meal,
                    approximate_protein_g=protein_per_meal,
                    approximate_carbs_g=carbs_per_meal,
                    approximate_fats_g=fats_per_meal,
                    prep_time_minutes=20
                ))
        
        if diet_type == "pescatarian":
            ingredients = ["salmon", "sweet potato", "asparagus", "lemon"]
            if is_allowed(ingredients):
                sample_meals.append(SampleMeal(
                    meal_type=MealType.LUNCH,
                    name="Baked Salmon with Sweet Potato",
                    ingredients=ingredients,
                    approximate_calories=calories_per_meal,
                    approximate_protein_g=protein_per_meal,
                    approximate_carbs_g=carbs_per_meal,
                    approximate_fats_g=fats_per_meal,
                    prep_time_minutes=30
                ))
        
        # Dinner options
        if diet_type == "omnivore":
            ingredients = ["lean beef", "pasta", "tomato sauce", "vegetables"]
            if is_allowed(ingredients):
                sample_meals.append(SampleMeal(
                    meal_type=MealType.DINNER,
                    name="Lean Beef Pasta",
                    ingredients=ingredients,
                    approximate_calories=calories_per_meal,
                    approximate_protein_g=protein_per_meal,
                    approximate_carbs_g=carbs_per_meal,
                    approximate_fats_g=fats_per_meal,
                    prep_time_minutes=30
                ))
        
        if diet_type in ["vegetarian", "omnivore"]:
            if "dairy" not in allergies_lower:
                ingredients = ["paneer", "bell peppers", "onions", "spices"]
                if is_allowed(ingredients):
                    sample_meals.append(SampleMeal(
                        meal_type=MealType.DINNER,
                        name="Paneer Tikka Masala",
                        ingredients=ingredients,
                        approximate_calories=calories_per_meal,
                        approximate_protein_g=protein_per_meal,
                        approximate_carbs_g=carbs_per_meal,
                        approximate_fats_g=fats_per_meal,
                        prep_time_minutes=35
                    ))
        
        # Snack options
        if meal_frequency >= 4:
            if diet_type in ["vegetarian", "vegan", "omnivore", "pescatarian"]:
                ingredients = ["greek yogurt", "mixed nuts", "honey"]
                if "dairy" not in allergies_lower and is_allowed(ingredients):
                    sample_meals.append(SampleMeal(
                        meal_type=MealType.SNACK,
                        name="Greek Yogurt with Nuts",
                        ingredients=ingredients,
                        approximate_calories=calories_per_meal // 2,
                        approximate_protein_g=protein_per_meal // 2,
                        approximate_carbs_g=carbs_per_meal // 2,
                        approximate_fats_g=fats_per_meal // 2,
                        prep_time_minutes=2
                    ))
        
        # Ensure we have at least 3 sample meals
        if len(sample_meals) < 3:
            # Add generic meals that work for all diets
            ingredients = ["mixed vegetables", "rice", "beans", "spices"]
            if is_allowed(ingredients):
                sample_meals.append(SampleMeal(
                    meal_type=MealType.DINNER,
                    name="Vegetable Rice Bowl",
                    ingredients=ingredients,
                    approximate_calories=calories_per_meal,
                    approximate_protein_g=protein_per_meal,
                    approximate_carbs_g=carbs_per_meal,
                    approximate_fats_g=fats_per_meal,
                    prep_time_minutes=20
                ))
        
        return sample_meals[:5]  # Return max 5 sample meals
    
    def _generate_meal_timing(self, meal_frequency: int, workout_frequency: int) -> str:
        """Generate meal timing suggestions."""
        if meal_frequency == 2:
            return "Breakfast (8-9am), Dinner (6-7pm). Have a carb-rich meal 2-3 hours before workouts."
        elif meal_frequency == 3:
            return "Breakfast (7-8am), Lunch (12-1pm), Dinner (6-7pm). Have a carb-rich meal 2-3 hours before workouts."
        elif meal_frequency == 4:
            return "Breakfast (7-8am), Lunch (12-1pm), Snack (3-4pm), Dinner (7-8pm). Time snack around workouts for energy."
        elif meal_frequency == 5:
            return "Breakfast (7am), Snack (10am), Lunch (1pm), Snack (4pm), Dinner (7pm). Pre-workout snack 1-2 hours before training."
        else:  # 6 meals
            return "Breakfast (7am), Snack (9:30am), Lunch (12pm), Snack (3pm), Dinner (6pm), Evening Snack (8:30pm). Distribute protein evenly."
