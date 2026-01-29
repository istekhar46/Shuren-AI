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

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.endpoints import auth, onboarding, profiles
from app.core.config import settings


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


# Exception Handlers

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
            "path": str(request.url.path)
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle 403 Forbidden errors.
    
    Returns a consistent JSON response for authorization failures.
    """
    logger.warning(f"403 Forbidden: {request.url}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "detail": "Access forbidden - insufficient permissions",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle 422 Unprocessable Entity errors (validation failures).
    
    Returns detailed validation error information including field-level errors.
    """
    logger.warning(f"422 Validation Error: {request.url} - {exc.errors()}")
    
    # Format validation errors for better readability
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors.
    
    Logs the full error details and returns a generic error message to the client.
    """
    logger.error(f"Database error: {request.url} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error - database operation failed",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions.
    
    Logs the full error details and returns a generic error message to the client.
    This is the catch-all handler for unexpected errors.
    """
    logger.error(f"Unhandled exception: {request.url} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path)
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
