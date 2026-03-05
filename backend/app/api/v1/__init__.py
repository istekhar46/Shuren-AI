"""API v1 package"""

from fastapi import APIRouter

from app.api.v1.endpoints import chat, meal_templates, meals, onboarding

# Create v1 API router
api_router = APIRouter()

# Include core meal plan and schedules router
api_router.include_router(
    meals.router,
    prefix="/meals",
    tags=["Meals Core"]
)

# Include meal templates router AFTER core meals router 
# to ensure it mounts /meals/template properly without being masked
api_router.include_router(
    meal_templates.router,
    prefix="/meals",
    tags=["Meal Templates"]
)

# Include chat router
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

# Include onboarding router
api_router.include_router(
    onboarding.router,
    prefix="/onboarding",
    tags=["Onboarding"]
)
