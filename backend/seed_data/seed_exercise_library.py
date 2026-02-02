"""
Seed script for exercise_library table.

This script populates the exercise_library table with reference data including:
- Compound movements (squats, deadlifts, bench press, rows)
- Isolation exercises (curls, extensions, raises)
- Cardio exercises (running, cycling, rowing)

Run with: poetry run python seed_exercise_library.py
"""
import asyncio
import sys
import uuid
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


# Exercise data organized by category
EXERCISES = [
    # ========== COMPOUND MOVEMENTS ==========
    {
        "exercise_name": "Barbell Back Squat",
        "exercise_slug": "barbell-back-squat",
        "exercise_type": "strength",
        "primary_muscle_group": "Quadriceps",
        "secondary_muscle_groups": ["Glutes", "Hamstrings", "Core"],
        "equipment_required": ["Barbell", "Squat Rack"],
        "difficulty_level": "intermediate",
        "description": "A fundamental compound exercise that targets the lower body, particularly the quadriceps, glutes, and hamstrings.",
        "instructions": "1. Position the barbell on your upper back/traps\n2. Stand with feet shoulder-width apart\n3. Brace your core and descend by bending knees and hips\n4. Lower until thighs are parallel to ground\n5. Drive through heels to return to starting position",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Squat.gif",
        "is_compound": True,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Conventional Deadlift",
        "exercise_slug": "conventional-deadlift",
        "exercise_type": "strength",
        "primary_muscle_group": "Hamstrings",
        "secondary_muscle_groups": ["Glutes", "Lower Back", "Traps", "Forearms"],
        "equipment_required": ["Barbell"],
        "difficulty_level": "intermediate",
        "description": "The king of compound exercises, working the entire posterior chain and building total body strength.",
        "instructions": "1. Stand with feet hip-width apart, barbell over mid-foot\n2. Bend at hips and knees to grip the bar\n3. Keep back straight, chest up, and core braced\n4. Drive through heels, extending hips and knees simultaneously\n5. Stand tall at the top, then lower with control",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Deadlift.gif",
        "is_compound": True,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Barbell Bench Press",
        "exercise_slug": "barbell-bench-press",
        "exercise_type": "strength",
        "primary_muscle_group": "Chest",
        "secondary_muscle_groups": ["Triceps", "Anterior Deltoids"],
        "equipment_required": ["Barbell", "Bench"],
        "difficulty_level": "intermediate",
        "description": "A classic upper body compound movement that builds chest, shoulder, and tricep strength.",
        "instructions": "1. Lie on bench with feet flat on floor\n2. Grip barbell slightly wider than shoulder-width\n3. Unrack the bar and position over chest\n4. Lower bar to mid-chest with control\n5. Press bar back up to starting position",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bench-Press.gif",
        "is_compound": True,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Barbell Bent-Over Row",
        "exercise_slug": "barbell-bent-over-row",
        "exercise_type": "strength",
        "primary_muscle_group": "Back",
        "secondary_muscle_groups": ["Biceps", "Rear Deltoids", "Traps"],
        "equipment_required": ["Barbell"],
        "difficulty_level": "intermediate",
        "description": "A fundamental back exercise that builds thickness and strength in the lats and mid-back.",
        "instructions": "1. Stand with feet hip-width apart, holding barbell\n2. Hinge at hips to 45-degree angle, back straight\n3. Let arms hang straight down\n4. Pull barbell to lower chest/upper abdomen\n5. Squeeze shoulder blades together at top\n6. Lower with control",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bent-Over-Row.gif",
        "is_compound": True,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Overhead Press",
        "exercise_slug": "overhead-press",
        "exercise_type": "strength",
        "primary_muscle_group": "Shoulders",
        "secondary_muscle_groups": ["Triceps", "Upper Chest", "Core"],
        "equipment_required": ["Barbell"],
        "difficulty_level": "intermediate",
        "description": "A compound shoulder exercise that builds overhead pressing strength and shoulder stability.",
        "instructions": "1. Stand with feet shoulder-width apart\n2. Hold barbell at shoulder height, hands just outside shoulders\n3. Brace core and press bar overhead\n4. Lock out arms at top with bar over mid-foot\n5. Lower with control to starting position",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Standing-Military-Press.gif",
        "is_compound": True,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Pull-Up",
        "exercise_slug": "pull-up",
        "exercise_type": "strength",
        "primary_muscle_group": "Back",
        "secondary_muscle_groups": ["Biceps", "Rear Deltoids", "Core"],
        "equipment_required": ["Pull-up Bar"],
        "difficulty_level": "intermediate",
        "description": "A bodyweight compound exercise that builds back width and pulling strength.",
        "instructions": "1. Hang from bar with overhand grip, hands shoulder-width apart\n2. Engage core and pull shoulder blades down\n3. Pull body up until chin clears bar\n4. Lower with control to full hang\n5. Repeat",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Pull-up.gif",
        "is_compound": True,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Dumbbell Lunges",
        "exercise_slug": "dumbbell-lunges",
        "exercise_type": "strength",
        "primary_muscle_group": "Quadriceps",
        "secondary_muscle_groups": ["Glutes", "Hamstrings", "Core"],
        "equipment_required": ["Dumbbells"],
        "difficulty_level": "beginner",
        "description": "A unilateral compound exercise that builds leg strength and improves balance.",
        "instructions": "1. Stand with dumbbells at sides\n2. Step forward with one leg\n3. Lower back knee toward ground\n4. Front thigh should be parallel to ground\n5. Push through front heel to return to start\n6. Alternate legs",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lunge.gif",
        "is_compound": True,
        "is_unilateral": True,
    },

    # ========== ISOLATION EXERCISES ==========
    {
        "exercise_name": "Barbell Bicep Curl",
        "exercise_slug": "barbell-bicep-curl",
        "exercise_type": "strength",
        "primary_muscle_group": "Biceps",
        "secondary_muscle_groups": ["Forearms"],
        "equipment_required": ["Barbell"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise targeting the biceps for arm development.",
        "instructions": "1. Stand with feet shoulder-width apart\n2. Hold barbell with underhand grip at hip level\n3. Keep elbows close to sides\n4. Curl bar up toward shoulders\n5. Squeeze biceps at top\n6. Lower with control",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Curl.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Dumbbell Bicep Curl",
        "exercise_slug": "dumbbell-bicep-curl",
        "exercise_type": "strength",
        "primary_muscle_group": "Biceps",
        "secondary_muscle_groups": ["Forearms"],
        "equipment_required": ["Dumbbells"],
        "difficulty_level": "beginner",
        "description": "A classic isolation exercise for building bicep size and strength.",
        "instructions": "1. Stand with dumbbells at sides, palms facing forward\n2. Keep elbows close to torso\n3. Curl weights up toward shoulders\n4. Squeeze biceps at top\n5. Lower with control\n6. Can be done alternating or simultaneously",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Curl.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Tricep Rope Pushdown",
        "exercise_slug": "tricep-rope-pushdown",
        "exercise_type": "strength",
        "primary_muscle_group": "Triceps",
        "secondary_muscle_groups": [],
        "equipment_required": ["Cable Machine", "Rope Attachment"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise that targets all three heads of the triceps.",
        "instructions": "1. Attach rope to high pulley\n2. Grip rope with palms facing each other\n3. Keep elbows close to sides\n4. Push rope down until arms are fully extended\n5. Split rope ends apart at bottom\n6. Return to starting position with control",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Rope-Pushdown.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Overhead Tricep Extension",
        "exercise_slug": "overhead-tricep-extension",
        "exercise_type": "strength",
        "primary_muscle_group": "Triceps",
        "secondary_muscle_groups": [],
        "equipment_required": ["Dumbbell"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise that emphasizes the long head of the triceps.",
        "instructions": "1. Hold dumbbell overhead with both hands\n2. Keep elbows close to head\n3. Lower weight behind head by bending elbows\n4. Extend arms back to starting position\n5. Keep upper arms stationary throughout",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Overhead-Triceps-Extension.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Lateral Raise",
        "exercise_slug": "lateral-raise",
        "exercise_type": "strength",
        "primary_muscle_group": "Shoulders",
        "secondary_muscle_groups": ["Traps"],
        "equipment_required": ["Dumbbells"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise targeting the lateral deltoids for shoulder width.",
        "instructions": "1. Stand with dumbbells at sides\n2. Keep slight bend in elbows\n3. Raise arms out to sides until parallel to ground\n4. Lead with elbows, not hands\n5. Lower with control\n6. Avoid swinging or using momentum",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lateral-Raise.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Front Raise",
        "exercise_slug": "front-raise",
        "exercise_type": "strength",
        "primary_muscle_group": "Shoulders",
        "secondary_muscle_groups": ["Upper Chest"],
        "equipment_required": ["Dumbbells"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise targeting the anterior deltoids.",
        "instructions": "1. Stand with dumbbells in front of thighs\n2. Keep slight bend in elbows\n3. Raise arms forward until parallel to ground\n4. Palms facing down or toward each other\n5. Lower with control\n6. Can be done alternating or simultaneously",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Front-Raise.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Rear Delt Fly",
        "exercise_slug": "rear-delt-fly",
        "exercise_type": "strength",
        "primary_muscle_group": "Shoulders",
        "secondary_muscle_groups": ["Upper Back"],
        "equipment_required": ["Dumbbells"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise targeting the posterior deltoids and upper back.",
        "instructions": "1. Bend at hips to 45-degree angle\n2. Hold dumbbells with arms hanging down\n3. Keep slight bend in elbows\n4. Raise arms out to sides, squeezing shoulder blades\n5. Lower with control\n6. Avoid using momentum",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Rear-Delt-Fly.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Leg Extension",
        "exercise_slug": "leg-extension",
        "exercise_type": "strength",
        "primary_muscle_group": "Quadriceps",
        "secondary_muscle_groups": [],
        "equipment_required": ["Leg Extension Machine"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise that targets the quadriceps muscles.",
        "instructions": "1. Sit in leg extension machine\n2. Position ankles under pad\n3. Grip handles for stability\n4. Extend legs until fully straight\n5. Squeeze quads at top\n6. Lower with control",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Leg-Extension.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Leg Curl",
        "exercise_slug": "leg-curl",
        "exercise_type": "strength",
        "primary_muscle_group": "Hamstrings",
        "secondary_muscle_groups": [],
        "equipment_required": ["Leg Curl Machine"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise targeting the hamstrings.",
        "instructions": "1. Lie face down on leg curl machine\n2. Position ankles under pad\n3. Grip handles for stability\n4. Curl legs up toward glutes\n5. Squeeze hamstrings at top\n6. Lower with control",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Lying-Leg-Curl.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Calf Raise",
        "exercise_slug": "calf-raise",
        "exercise_type": "strength",
        "primary_muscle_group": "Calves",
        "secondary_muscle_groups": [],
        "equipment_required": ["Calf Raise Machine"],
        "difficulty_level": "beginner",
        "description": "An isolation exercise for building calf muscle size and strength.",
        "instructions": "1. Stand on calf raise machine with balls of feet on platform\n2. Lower heels below platform level\n3. Push through balls of feet to raise heels as high as possible\n4. Squeeze calves at top\n5. Lower with control\n6. Can be done on machine or with dumbbells",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/02/Calf-Raise.gif",
        "is_compound": False,
        "is_unilateral": False,
    },

    # ========== CARDIO EXERCISES ==========
    {
        "exercise_name": "Treadmill Running",
        "exercise_slug": "treadmill-running",
        "exercise_type": "cardio",
        "primary_muscle_group": "Cardiovascular System",
        "secondary_muscle_groups": ["Quadriceps", "Hamstrings", "Calves"],
        "equipment_required": ["Treadmill"],
        "difficulty_level": "beginner",
        "description": "A cardiovascular exercise that improves endurance and burns calories.",
        "instructions": "1. Start treadmill at comfortable walking pace\n2. Gradually increase speed to desired running pace\n3. Maintain upright posture\n4. Land mid-foot with each stride\n5. Swing arms naturally\n6. Adjust speed and incline as needed",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/09/Treadmill-Running.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Outdoor Running",
        "exercise_slug": "outdoor-running",
        "exercise_type": "cardio",
        "primary_muscle_group": "Cardiovascular System",
        "secondary_muscle_groups": ["Quadriceps", "Hamstrings", "Calves", "Core"],
        "equipment_required": ["Running Shoes"],
        "difficulty_level": "beginner",
        "description": "Running outdoors for cardiovascular fitness and mental health benefits.",
        "instructions": "1. Warm up with 5-10 minutes of walking\n2. Start at comfortable jogging pace\n3. Maintain upright posture with slight forward lean\n4. Land mid-foot, not on heels\n5. Keep arms at 90-degree angle\n6. Breathe rhythmically\n7. Cool down with walking",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/09/Running.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Stationary Bike",
        "exercise_slug": "stationary-bike",
        "exercise_type": "cardio",
        "primary_muscle_group": "Cardiovascular System",
        "secondary_muscle_groups": ["Quadriceps", "Hamstrings", "Calves"],
        "equipment_required": ["Stationary Bike"],
        "difficulty_level": "beginner",
        "description": "Low-impact cardiovascular exercise suitable for all fitness levels.",
        "instructions": "1. Adjust seat height so knee has slight bend at bottom of pedal stroke\n2. Start with low resistance\n3. Maintain steady cadence (60-90 RPM)\n4. Keep core engaged and back straight\n5. Gradually increase resistance or speed\n6. Can do steady-state or interval training",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/09/Stationary-Bike.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Outdoor Cycling",
        "exercise_slug": "outdoor-cycling",
        "exercise_type": "cardio",
        "primary_muscle_group": "Cardiovascular System",
        "secondary_muscle_groups": ["Quadriceps", "Hamstrings", "Calves", "Core"],
        "equipment_required": ["Bicycle", "Helmet"],
        "difficulty_level": "beginner",
        "description": "Outdoor cycling for cardiovascular fitness and leg strength.",
        "instructions": "1. Ensure bike is properly fitted to your height\n2. Always wear helmet for safety\n3. Start with flat terrain\n4. Maintain steady cadence\n5. Use gears appropriately for terrain\n6. Stay hydrated\n7. Follow traffic rules",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/09/Cycling.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Rowing Machine",
        "exercise_slug": "rowing-machine",
        "exercise_type": "cardio",
        "primary_muscle_group": "Cardiovascular System",
        "secondary_muscle_groups": ["Back", "Legs", "Core", "Arms"],
        "equipment_required": ["Rowing Machine"],
        "difficulty_level": "intermediate",
        "description": "Full-body cardiovascular exercise that also builds strength.",
        "instructions": "1. Sit on rower with feet secured in straps\n2. Grip handle with overhand grip\n3. Start with legs bent, arms extended (catch position)\n4. Push with legs first, then lean back, then pull arms\n5. Reverse the motion: extend arms, lean forward, bend legs\n6. Maintain smooth, controlled rhythm",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/09/Rowing-Machine.gif",
        "is_compound": True,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Jump Rope",
        "exercise_slug": "jump-rope",
        "exercise_type": "cardio",
        "primary_muscle_group": "Cardiovascular System",
        "secondary_muscle_groups": ["Calves", "Shoulders", "Core"],
        "equipment_required": ["Jump Rope"],
        "difficulty_level": "beginner",
        "description": "High-intensity cardiovascular exercise that improves coordination and burns calories.",
        "instructions": "1. Hold rope handles at hip level\n2. Rotate rope with wrists, not arms\n3. Jump just high enough to clear rope\n4. Land softly on balls of feet\n5. Keep elbows close to sides\n6. Maintain steady rhythm\n7. Start with 30-second intervals",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/09/Jump-Rope.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Elliptical Trainer",
        "exercise_slug": "elliptical-trainer",
        "exercise_type": "cardio",
        "primary_muscle_group": "Cardiovascular System",
        "secondary_muscle_groups": ["Quadriceps", "Hamstrings", "Glutes"],
        "equipment_required": ["Elliptical Machine"],
        "difficulty_level": "beginner",
        "description": "Low-impact cardiovascular exercise suitable for all fitness levels.",
        "instructions": "1. Step onto elliptical and grip handles\n2. Start with low resistance\n3. Push and pull pedals in smooth elliptical motion\n4. Keep core engaged\n5. Can move forward or backward\n6. Adjust resistance and incline as needed\n7. Maintain steady pace",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/09/Elliptical.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
    {
        "exercise_name": "Stair Climber",
        "exercise_slug": "stair-climber",
        "exercise_type": "cardio",
        "primary_muscle_group": "Cardiovascular System",
        "secondary_muscle_groups": ["Quadriceps", "Glutes", "Hamstrings", "Calves"],
        "equipment_required": ["Stair Climber Machine"],
        "difficulty_level": "intermediate",
        "description": "Cardiovascular exercise that also builds lower body strength.",
        "instructions": "1. Step onto stair climber\n2. Grip handles lightly for balance\n3. Start with moderate speed\n4. Take full steps, don't just tap stairs\n5. Keep core engaged and posture upright\n6. Avoid leaning heavily on handles\n7. Adjust speed as needed",
        "gif_url": "https://fitnessprogramer.com/wp-content/uploads/2021/09/Stair-Climber.gif",
        "is_compound": False,
        "is_unilateral": False,
    },
]


async def seed_exercise_library():
    """Seed the exercise_library table with reference data."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if data already exists
            result = await session.execute(text("SELECT COUNT(*) FROM exercise_library"))
            count = result.scalar()
            
            if count > 0:
                print(f"Exercise library already contains {count} exercises. Skipping seed.")
                return
            
            print("Seeding exercise library...")
            
            # Insert exercises
            for exercise in EXERCISES:
                exercise_id = uuid.uuid4()
                
                query = text("""
                    INSERT INTO exercise_library (
                        id, exercise_name, exercise_slug, exercise_type,
                        primary_muscle_group, secondary_muscle_groups,
                        equipment_required, difficulty_level, description,
                        instructions, gif_url, is_compound, is_unilateral,
                        created_at, updated_at
                    ) VALUES (
                        :id, :exercise_name, :exercise_slug, :exercise_type,
                        :primary_muscle_group, :secondary_muscle_groups,
                        :equipment_required, :difficulty_level, :description,
                        :instructions, :gif_url, :is_compound, :is_unilateral,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """)
                
                await session.execute(query, {
                    "id": exercise_id,
                    "exercise_name": exercise["exercise_name"],
                    "exercise_slug": exercise["exercise_slug"],
                    "exercise_type": exercise["exercise_type"],
                    "primary_muscle_group": exercise["primary_muscle_group"],
                    "secondary_muscle_groups": exercise["secondary_muscle_groups"],
                    "equipment_required": exercise["equipment_required"],
                    "difficulty_level": exercise["difficulty_level"],
                    "description": exercise["description"],
                    "instructions": exercise["instructions"],
                    "gif_url": exercise.get("gif_url"),
                    "is_compound": exercise["is_compound"],
                    "is_unilateral": exercise["is_unilateral"],
                })
                
                print(f"  ✓ Added: {exercise['exercise_name']}")
            
            await session.commit()
            print(f"\n✅ Successfully seeded {len(EXERCISES)} exercises!")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error seeding exercise library: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_exercise_library())
