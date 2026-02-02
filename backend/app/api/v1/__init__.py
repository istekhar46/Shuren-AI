"""API v1 package"""

from fastapi import APIRouter

from app.api.v1.endpoints import chat, dishes, meal_templates, shopping_list

# Create v1 API router
api_router = APIRouter()

# Include meal templates router
api_router.include_router(
    meal_templates.router,
    prefix="/meals",
    tags=["Meal Templates"]
)

# Include shopping list router
api_router.include_router(
    shopping_list.router,
    prefix="/meals/shopping-list",
    tags=["Shopping List"]
)

# Include dishes router
api_router.include_router(
    dishes.router,
    prefix="/dishes",
    tags=["Dishes"]
)

# Include chat router
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)
