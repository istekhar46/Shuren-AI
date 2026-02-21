# Streaming Response Database Connection Fix

## Issue Description

When using FastAPI's `StreamingResponse` with Server-Sent Events (SSE) for chat streaming, a `CancelledError` was occurring during database connection cleanup after the response completed successfully.

### Error Log
```
sqlalchemy.pool.impl.AsyncAdaptedQueuePool - ERROR - Exception terminating connection
asyncio.exceptions.CancelledError: Cancelled via cancel scope
```

## Root Cause

The error occurred due to the interaction between FastAPI's request lifecycle and SQLAlchemy's async connection pool:

1. **StreamingResponse completes** - The generator finishes yielding all chunks and the response is sent to the client
2. **FastAPI cancels the request task** - As part of normal cleanup, FastAPI/Uvicorn cancels the request task
3. **SQLAlchemy attempts graceful connection cleanup** - SQLAlchemy tries to terminate the database connection gracefully using `asyncio.shield()`
4. **Cancellation interrupts cleanup** - The task cancellation propagates through, causing a `CancelledError` during the connection termination process

**Important**: This error is **harmless** - the streaming works correctly, the response is delivered successfully, and the error only occurs during cleanup after the response is already sent. However, it creates noisy error logs.

## Solution Implemented

### 1. Manual Database Session Management (Already Implemented)

The streaming endpoints already follow the official FastAPI pattern for long-running `StreamingResponse` operations:

```python
async def generate():
    """Async generator function for SSE streaming with managed database session"""
    # Create a new database session that will live for the entire streaming operation
    # This is the official pattern for StreamingResponse with database dependencies
    async with AsyncSessionLocal() as db:
        # All streaming logic here
        # Database session stays alive during entire streaming operation
```

**Why this pattern is necessary:**
- FastAPI's dependency injection with `yield` closes database sessions immediately after the endpoint function returns
- `StreamingResponse` generators continue running after the endpoint returns
- Agents call function tools during streaming that need database access
- Manual session management keeps the session alive for the entire streaming duration

### 2. Connection Pool Configuration

Added `pool_reset_on_return="rollback"` to ensure clean connection state when connections are returned to the pool:

```python
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,
    pool_reset_on_return="rollback"  # Ensure clean connection state
)
```

### 3. Logging Filter to Suppress Harmless Errors

Added a custom logging filter to suppress the specific `CancelledError` logs during connection termination:

```python
class SuppressCancelledErrorFilter(logging.Filter):
    """
    Filter to suppress CancelledError logs during database connection termination.
    
    When StreamingResponse completes, FastAPI cancels the request task as part of
    normal cleanup. SQLAlchemy tries to gracefully close connections, but the
    cancellation can interrupt this process, causing harmless CancelledError logs.
    
    This filter suppresses these specific errors to reduce log noise while keeping
    other important error logs intact.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        # Suppress "Exception terminating connection" errors with CancelledError
        if record.levelno == logging.ERROR:
            message = record.getMessage()
            if "Exception terminating connection" in message and "CancelledError" in message:
                return False
        return True

# Add filter to SQLAlchemy pool logger
sqlalchemy_pool_logger = logging.getLogger("sqlalchemy.pool.impl.AsyncAdaptedQueuePool")
sqlalchemy_pool_logger.addFilter(SuppressCancelledErrorFilter())
```

## Files Modified

1. **backend/app/db/session.py**
   - Added `pool_reset_on_return="rollback"` to engine configuration

2. **backend/app/main.py**
   - Added `SuppressCancelledErrorFilter` class
   - Applied filter to SQLAlchemy pool logger

3. **backend/app/api/v1/endpoints/chat.py**
   - Fixed indentation in `chat_onboarding_stream` function
   - Ensured proper try-except-finally structure within the database session context manager

## Testing

To verify the fix:

1. Start the backend server:
   ```bash
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Send a chat message during onboarding via the frontend

3. Verify:
   - Streaming works correctly (response chunks delivered in real-time)
   - No `CancelledError` logs appear in the console
   - Response completes successfully with final "done" event

## References

- [FastAPI Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
- [SQLAlchemy Async Engine Configuration](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SQLAlchemy Issue #6592 - asyncpg connections and CancelledError](https://github.com/sqlalchemy/sqlalchemy/issues/6592)

## Key Takeaways

1. **Manual session management is required** for `StreamingResponse` with database operations
2. **The CancelledError is harmless** - it's a cleanup artifact, not a functional issue
3. **Logging filters are appropriate** for suppressing known harmless errors
4. **Connection pool configuration** helps ensure clean connection state

Content was rephrased for compliance with licensing restrictions.
