"""Meal template models for weekly meal planning with dish assignments."""

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class MealTemplate(BaseModel):
    """Meal template entity representing a weekly meal plan.
    
    Each user can have up to 4 weekly templates (4-week rotation).
    Templates contain specific dish assignments for each meal slot.
    """
    
    __tablename__ = "meal_templates"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Template identification
    week_number = Column(Integer, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Generation metadata
    generated_by = Column(String(50), default='system', nullable=False)
    generation_reason = Column(Text, nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="meal_templates")
    template_meals = relationship(
        "TemplateMeal",
        back_populates="template",
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('week_number BETWEEN 1 AND 4', name='valid_week_number'),
        UniqueConstraint('profile_id', 'week_number', name='unique_profile_week'),
        Index('idx_meal_templates_profile', 'profile_id', postgresql_where=(
            Column('deleted_at').is_(None)
        )),
        Index('idx_meal_templates_active', 'profile_id', 'is_active', postgresql_where=(
            Column('deleted_at').is_(None) & (Column('is_active') == True)
        )),
    )


class TemplateMeal(BaseModel):
    """Template meal entity linking meal slots to specific dishes.
    
    Represents a specific dish assignment for a meal slot in the template.
    Each meal slot can have a primary dish and multiple alternatives.
    """
    
    __tablename__ = "template_meals"
    
    # Foreign keys
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_templates.id", ondelete="CASCADE"),
        nullable=False
    )
    meal_schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal_schedules.id", ondelete="CASCADE"),
        nullable=False
    )
    dish_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dishes.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    # Meal slot identification
    day_of_week = Column(Integer, nullable=False)
    
    # Dish role
    is_primary = Column(Boolean, default=True, nullable=False)
    alternative_order = Column(Integer, default=1, nullable=False)
    
    # Relationships
    template = relationship("MealTemplate", back_populates="template_meals")
    meal_schedule = relationship("MealSchedule")
    dish = relationship("Dish", back_populates="template_meals")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('day_of_week BETWEEN 0 AND 6', name='valid_day_of_week'),
        CheckConstraint('alternative_order BETWEEN 1 AND 5', name='valid_alternative_order'),
        Index('idx_template_meals_template', 'template_id'),
        Index('idx_template_meals_schedule', 'meal_schedule_id'),
        Index('idx_template_meals_dish', 'dish_id'),
        Index('idx_template_meals_day', 'template_id', 'day_of_week'),
        Index('idx_template_meals_primary', 'template_id', 'is_primary', postgresql_where=(
            Column('is_primary') == True
        )),
    )
