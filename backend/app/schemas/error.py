"""Error response Pydantic schemas for consistent error handling"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Standard error response schema for all API errors.
    
    Provides consistent error format across all endpoints with:
    - Human-readable error message
    - Machine-readable error code for client handling
    - Optional field-level validation errors
    
    Examples:
        404 Not Found:
        {
            "detail": "Workout plan not found for user",
            "error_code": "WORKOUT_PLAN_NOT_FOUND"
        }
        
        403 Profile Locked:
        {
            "detail": "Profile is locked. Unlock profile before making modifications.",
            "error_code": "PROFILE_LOCKED"
        }
        
        422 Validation Error:
        {
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "field_errors": {
                "duration_weeks": ["Value must be between 1 and 52"],
                "sets": ["Value must be between 1 and 20"]
            }
        }
    """
    detail: str = Field(
        ...,
        description="Human-readable error message describing what went wrong"
    )
    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code for client-side error handling"
    )
    field_errors: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Field-level validation errors (for 422 responses)"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "detail": "Workout plan not found for user",
                    "error_code": "WORKOUT_PLAN_NOT_FOUND"
                },
                {
                    "detail": "Profile is locked. Unlock profile before making modifications.",
                    "error_code": "PROFILE_LOCKED"
                },
                {
                    "detail": "Validation error",
                    "error_code": "VALIDATION_ERROR",
                    "field_errors": {
                        "duration_weeks": ["Value must be between 1 and 52"],
                        "sets": ["Value must be between 1 and 20"]
                    }
                }
            ]
        }


class ValidationErrorDetail(BaseModel):
    """
    Detailed validation error information for a single field.
    
    Used internally to format Pydantic validation errors into
    the standard ErrorResponse format.
    """
    field: str = Field(
        ...,
        description="Field path that failed validation (e.g., 'workout_days.0.exercises.2.sets')"
    )
    message: str = Field(
        ...,
        description="Validation error message"
    )
    type: str = Field(
        ...,
        description="Pydantic error type (e.g., 'value_error.number.not_ge')"
    )
