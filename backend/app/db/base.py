"""Base database model with common fields for all entities."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

# Create the declarative base for all models
Base = declarative_base()


class BaseModel(Base):
    """Abstract base model with common fields for all database entities.
    
    Provides:
    - UUID primary key (id)
    - Automatic timestamp management (created_at, updated_at)
    - Soft delete support (deleted_at)
    """
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
