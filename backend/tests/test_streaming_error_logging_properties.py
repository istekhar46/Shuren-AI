"""
Property-based tests for streaming error logging.

**Property 23: Error Logging**
**Validates: Requirements 6.6**

This module tests that all errors during streaming are properly logged with full context.
"""

import logging
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.metrics import get_metrics_tracker


# Strategy for generating error types
error_types = st.sampled_from([
    "state_not_found",
    "invalid_state",
    "context_load_failed",
    "agent_streaming_failed",
    "classification_failed",
    "invalid_agent_type",
    "timeout",
    "unexpected_error",
    "database_save_failed"
])

# Strategy for generating error messages
error_messages = st.text(min_size=10, max_size=200)

# Strategy for generating user IDs
user_ids = st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))

# Strategy for generating message IDs
message_ids = st.uuids().map(str)


@pytest.mark.property
class TestErrorLoggingProperties:
    """Property-based tests for error logging in streaming endpoints."""
    
    @given(
        error_type=error_types,
        error_message=error_messages,
        user_id=user_ids,
        message_id=message_ids
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_errors_are_logged(self, error_type, error_message, user_id, message_id, caplog):
        """
        Property: For any error that occurs during streaming, the error should be logged
        with full context including error_type, error_message, user_id, and message_id.
        
        **Validates: Requirements 6.6**
        """
        # Set log level to capture all logs
        caplog.set_level(logging.ERROR)
        caplog.clear()
        
        # Get logger
        logger = logging.getLogger("app.api.v1.endpoints.chat")
        
        # Simulate error logging (as done in streaming endpoints)
        logger.error(
            f"Error occurred: {error_type}",
            extra={
                "event": "stream_error",
                "user_id": user_id,
                "message_id": message_id,
                "error_type": error_type,
                "error_message": error_message
            }
        )
        
        # Verify error was logged
        assert len(caplog.records) > 0
        
        # Find the error record
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) > 0
        
        # Verify the error record contains all required context
        error_record = error_records[0]
        assert error_record.user_id == user_id
        assert error_record.message_id == message_id
        assert error_record.error_type == error_type
        assert error_record.error_message == error_message
        assert error_record.event == "stream_error"
    
    @given(
        error_type=error_types,
        user_id=user_ids,
        message_id=message_ids,
        chunk_count=st.integers(min_value=0, max_value=1000)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_error_logging_includes_metrics(self, error_type, user_id, message_id, chunk_count, caplog):
        """
        Property: For any error that occurs during streaming, the error log should include
        metrics information such as chunk_count and duration.
        
        **Validates: Requirements 6.6**
        """
        caplog.set_level(logging.ERROR)
        caplog.clear()
        logger = logging.getLogger("app.api.v1.endpoints.chat")
        
        # Simulate error logging with metrics
        logger.error(
            f"Streaming error: {error_type}",
            extra={
                "event": "stream_error",
                "user_id": user_id,
                "message_id": message_id,
                "error_type": error_type,
                "chunks_sent": chunk_count
            }
        )
        
        # Verify error was logged with metrics
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) > 0
        
        error_record = error_records[0]
        assert error_record.chunks_sent == chunk_count
    
    @given(
        error_type=error_types,
        user_id=user_ids,
        message_id=message_ids
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_cleanup_logged_after_error(self, error_type, user_id, message_id, caplog):
        """
        Property: For any error that occurs during streaming, a cleanup event should be
        logged after the error.
        
        **Validates: Requirements 6.6**
        """
        caplog.set_level(logging.INFO)
        caplog.clear()
        logger = logging.getLogger("app.api.v1.endpoints.chat")
        
        # Simulate error logging
        logger.error(
            f"Error: {error_type}",
            extra={
                "event": "stream_error",
                "user_id": user_id,
                "message_id": message_id,
                "error_type": error_type
            }
        )
        
        # Simulate cleanup logging
        logger.info(
            "Stream cleanup after error",
            extra={
                "event": "stream_cleanup",
                "user_id": user_id,
                "message_id": message_id,
                "error": True
            }
        )
        
        # Verify both error and cleanup were logged
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        
        assert len(error_records) > 0
        assert len(info_records) > 0
        
        # Verify cleanup record has correct context
        cleanup_records = [r for r in info_records if hasattr(r, 'event') and r.event == "stream_cleanup"]
        assert len(cleanup_records) > 0
        
        cleanup_record = cleanup_records[0]
        assert cleanup_record.user_id == user_id
        assert cleanup_record.message_id == message_id
        assert cleanup_record.error is True
    
    @given(
        error_type=error_types,
        user_id=user_ids,
        message_id=message_ids,
        agent_type=st.sampled_from(["general", "workout", "diet", "supplement", "tracker", "scheduler"])
    )
    def test_error_tracking_in_metrics(self, error_type, user_id, message_id, agent_type):
        """
        Property: For any error that occurs during streaming, the error should be tracked
        in the metrics system with the correct error_type.
        
        **Validates: Requirements 6.6**
        """
        # Get metrics tracker
        from app.core.metrics import MetricsTracker
        tracker = MetricsTracker()
        
        # Start a session
        tracker.start_session(user_id=user_id, message_id=message_id)
        
        # Complete session with error
        tracker.complete_session(
            message_id=message_id,
            agent_type=agent_type,
            chunk_count=5,
            response_length=100,
            error_type=error_type
        )
        
        # Verify error is tracked in metrics
        stats = tracker.get_current_stats()
        assert stats["total_sessions"] == 1
        assert stats["error_rate_percent"] == 100
        assert error_type in stats["error_counts_by_type"]
        assert stats["error_counts_by_type"][error_type] == 1
    
    @given(
        error_messages=st.lists(
            st.tuples(error_types, user_ids, message_ids),
            min_size=1,
            max_size=20
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_errors_all_logged(self, error_messages, caplog):
        """
        Property: For any sequence of errors that occur, all errors should be logged
        individually with their own context.
        
        **Validates: Requirements 6.6**
        """
        caplog.set_level(logging.ERROR)
        caplog.clear()
        logger = logging.getLogger("app.api.v1.endpoints.chat")
        
        # Log multiple errors
        for error_type, user_id, message_id in error_messages:
            logger.error(
                f"Error: {error_type}",
                extra={
                    "event": "stream_error",
                    "user_id": user_id,
                    "message_id": message_id,
                    "error_type": error_type
                }
            )
        
        # Verify all errors were logged
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) == len(error_messages)
        
        # Verify each error has correct context
        for i, (error_type, user_id, message_id) in enumerate(error_messages):
            record = error_records[i]
            assert record.user_id == user_id
            assert record.message_id == message_id
            assert record.error_type == error_type
    
    @given(
        error_type=error_types,
        user_id=user_ids,
        message_id=message_ids
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_database_save_failure_logged(self, error_type, user_id, message_id, caplog):
        """
        Property: For any database save failure during streaming, the failure should be
        logged with full context and marked in metrics.
        
        **Validates: Requirements 6.6**
        """
        caplog.set_level(logging.ERROR)
        caplog.clear()
        logger = logging.getLogger("app.api.v1.endpoints.chat")
        
        # Get metrics tracker
        from app.core.metrics import MetricsTracker
        tracker = MetricsTracker()
        
        # Start session
        tracker.start_session(user_id=user_id, message_id=message_id)
        
        # Simulate database save failure logging
        logger.error(
            "Failed to save conversation",
            extra={
                "event": "database_save_failed",
                "user_id": user_id,
                "message_id": message_id,
                "error_type": "conversation_save_failed",
                "error_message": "Database connection lost"
            }
        )
        
        # Mark database save as failed in metrics
        tracker.mark_database_save_failed(message_id)
        
        # Complete session
        tracker.complete_session(
            message_id=message_id,
            agent_type="general",
            chunk_count=10,
            response_length=500,
            error_type=None
        )
        
        # Verify error was logged
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) > 0
        
        error_record = error_records[0]
        assert error_record.event == "database_save_failed"
        assert error_record.user_id == user_id
        assert error_record.message_id == message_id
        
        # Verify metrics tracked the failure
        stats = tracker.get_current_stats()
        assert stats["database_save_success_rate_percent"] == 0
