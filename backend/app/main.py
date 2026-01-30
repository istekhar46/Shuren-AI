"""
FastAPI application entry point for Shuren Backend.

This module initializes the FastAPI application with:
- API routers for authentication, onboarding, and profiles
- CORS middleware for cross-origin requests
- Exception handlers for common HTTP errors
- Logging configuration
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.endpoints import auth, chat, meals, onboarding, profiles, workouts
from app.core.config import settings
from app.core.exceptions import ProfileLockedException
from app.schemas.error import ErrorResponse


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"CORS origins: {settings.cors_origins_list}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered personal fitness application backend",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    onboarding.router,
    prefix="/api/v1/onboarding",
    tags=["Onboarding"]
)

app.include_router(
    profiles.router,
    prefix="/api/v1/profiles",
    tags=["Profiles"]
)

app.include_router(
    workouts.router,
    prefix="/api/v1/workouts",
    tags=["Workouts"]
)

app.include_router(
    meals.router,
    prefix="/api/v1/meals",
    tags=["Meals"]
)

app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["Chat"]
)


# Exception Handlers

@app.exception_handler(ProfileLockedException)
async def profile_locked_exception_handler(
    request: Request,
    exc: ProfileLockedException
) -> JSONResponse:
    """
    Handle ProfileLockedException errors.
    
    Returns HTTP 403 with explanation that profile must be unlocked
    before modifications can be made.
    """
    logger.warning(
        f"Profile locked error: {request.url}",
        extra={
            "path": str(request.url.path),
            "method": request.method
        }
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": str(exc.detail),
            "error_code": "PROFILE_LOCKED"
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle 404 Not Found errors.
    
    Returns a consistent JSON response for resource not found errors.
    """
    logger.warning(f"404 Not Found: {request.url}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "Resource not found",
            "error_code": "NOT_FOUND",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle 401 Unauthorized errors.
    
    Returns a consistent JSON response for authentication failures.
    """
    logger.warning(f"401 Unauthorized: {request.url}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": "Authentication required or invalid credentials",
            "error_code": "UNAUTHORIZED"
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle 403 Forbidden errors.
    
    Returns a consistent JSON response for authorization failures.
    Preserves detail message from HTTPException if available.
    """
    logger.warning(f"403 Forbidden: {request.url}")
    
    # If it's an HTTPException, preserve the detail message
    if isinstance(exc, HTTPException):
        detail = exc.detail
        error_code = getattr(exc, 'error_code', 'FORBIDDEN')
    else:
        detail = "Access forbidden - insufficient permissions"
        error_code = "FORBIDDEN"
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": detail,
            "error_code": error_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle 422 Unprocessable Entity errors (validation failures).
    
    Returns detailed validation error information including field-level errors
    in a consistent format using the ErrorResponse schema.
    """
    logger.warning(f"422 Validation Error: {request.url} - {exc.errors()}")
    
    # Format validation errors into field_errors dictionary
    field_errors: dict[str, list[str]] = {}
    for error in exc.errors():
        # Build field path from location tuple
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        
        # Add error message to field's error list
        if field_path not in field_errors:
            field_errors[field_path] = []
        field_errors[field_path].append(error["msg"])
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "field_errors": field_errors
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors.
    
    Logs the full error details with stack trace and returns a generic 
    error message to the client for security.
    """
    logger.error(
        f"Database error: {request.url} - {str(exc)}",
        exc_info=True,
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "error_type": type(exc).__name__
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error - database operation failed",
            "error_code": "DATABASE_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions.
    
    This is the catch-all handler for unexpected errors. Logs the full 
    error details with stack trace and returns a generic error message 
    to the client for security.
    """
    logger.error(
        f"Unhandled exception: {request.url} - {str(exc)}",
        exc_info=True,
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "error_type": type(exc).__name__
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the application status and version.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns basic API information and links to documentation.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }
