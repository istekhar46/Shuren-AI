"""Custom exceptions for the Shuren backend application"""

from fastapi import HTTPException, status


class ResourceNotFoundException(HTTPException):
    """
    Exception raised when a requested resource is not found.
    
    Returns HTTP 404 Not Found with a specific error message.
    
    Example:
        >>> workout_plan = await get_workout_plan(user_id)
        >>> if not workout_plan:
        ...     raise ResourceNotFoundException("Workout plan not found for user")
        
        Response:
        {
            "detail": "Workout plan not found for user",
            "error_code": "RESOURCE_NOT_FOUND"
        }
    """
    
    def __init__(
        self,
        detail: str = "Resource not found",
        error_code: str = "RESOURCE_NOT_FOUND",
        headers: dict[str, str] | None = None
    ):
        """
        Initialize ResourceNotFoundException.
        
        Args:
            detail: Error message describing what resource was not found
            error_code: Machine-readable error code (optional)
            headers: Additional HTTP headers (optional)
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers
        )
        self.error_code = error_code


class UnauthorizedAccessException(HTTPException):
    """
    Exception raised when a user attempts to access another user's data.
    
    Returns HTTP 403 Forbidden to prevent unauthorized cross-user access.
    
    Example:
        >>> if resource.user_id != current_user.id:
        ...     raise UnauthorizedAccessException()
        
        Response:
        {
            "detail": "Not authorized to access this resource",
            "error_code": "UNAUTHORIZED_ACCESS"
        }
    """
    
    def __init__(
        self,
        detail: str = "Not authorized to access this resource",
        headers: dict[str, str] | None = None
    ):
        """
        Initialize UnauthorizedAccessException.
        
        Args:
            detail: Custom error message (optional)
            headers: Additional HTTP headers (optional)
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers
        )
        self.error_code = "UNAUTHORIZED_ACCESS"
