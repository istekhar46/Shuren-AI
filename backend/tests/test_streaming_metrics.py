"""
Tests for streaming metrics tracking.

This module tests the metrics tracking functionality for streaming chat sessions.
"""

import pytest
from app.core.metrics import MetricsTracker, StreamingMetrics


class TestStreamingMetrics:
    """Test StreamingMetrics dataclass."""
    
    def test_metrics_initialization(self):
        """Test that metrics are initialized correctly."""
        metrics = StreamingMetrics(user_id="user123", message_id="msg456")
        
        assert metrics.user_id == "user123"
        assert metrics.message_id == "msg456"
        assert metrics.agent_type is None
        assert metrics.end_time is None
        assert metrics.duration_ms is None
        assert metrics.chunk_count == 0
        assert metrics.response_length == 0
        assert metrics.error_type is None
        assert metrics.database_save_success is True
    
    def test_metrics_complete(self):
        """Test completing a metrics session."""
        metrics = StreamingMetrics(user_id="user123", message_id="msg456")
        
        # Complete the session
        metrics.complete(chunk_count=10, response_length=500, error_type=None)
        
        assert metrics.chunk_count == 10
        assert metrics.response_length == 500
        assert metrics.error_type is None
        assert metrics.end_time is not None
        assert metrics.duration_ms is not None
        assert metrics.duration_ms >= 0  # Can be 0 for very fast operations
    
    def test_metrics_complete_with_error(self):
        """Test completing a metrics session with an error."""
        metrics = StreamingMetrics(user_id="user123", message_id="msg456")
        
        # Complete the session with error
        metrics.complete(chunk_count=5, response_length=200, error_type="timeout")
        
        assert metrics.chunk_count == 5
        assert metrics.response_length == 200
        assert metrics.error_type == "timeout"
    
    def test_mark_database_save_failed(self):
        """Test marking database save as failed."""
        metrics = StreamingMetrics(user_id="user123", message_id="msg456")
        
        assert metrics.database_save_success is True
        
        metrics.mark_database_save_failed()
        
        assert metrics.database_save_success is False


class TestMetricsTracker:
    """Test MetricsTracker class."""
    
    def test_tracker_initialization(self):
        """Test that tracker is initialized correctly."""
        tracker = MetricsTracker()
        
        stats = tracker.get_current_stats()
        assert stats["total_sessions"] == 0
        assert stats["active_sessions"] == 0
        assert stats["avg_duration_ms"] == 0
        assert stats["error_rate_percent"] == 0
        assert stats["database_save_success_rate_percent"] == 100
    
    def test_start_session(self):
        """Test starting a new session."""
        tracker = MetricsTracker()
        
        metrics = tracker.start_session(user_id="user123", message_id="msg456")
        
        assert metrics.user_id == "user123"
        assert metrics.message_id == "msg456"
        
        stats = tracker.get_current_stats()
        assert stats["active_sessions"] == 1
    
    def test_complete_session(self):
        """Test completing a session."""
        tracker = MetricsTracker()
        
        # Start session
        tracker.start_session(user_id="user123", message_id="msg456")
        
        # Complete session
        tracker.complete_session(
            message_id="msg456",
            agent_type="general",
            chunk_count=10,
            response_length=500,
            error_type=None
        )
        
        stats = tracker.get_current_stats()
        assert stats["total_sessions"] == 1
        assert stats["active_sessions"] == 0
        assert stats["avg_duration_ms"] >= 0  # Can be 0 for very fast operations
        assert stats["error_rate_percent"] == 0
    
    def test_complete_session_with_error(self):
        """Test completing a session with an error."""
        tracker = MetricsTracker()
        
        # Start session
        tracker.start_session(user_id="user123", message_id="msg456")
        
        # Complete session with error
        tracker.complete_session(
            message_id="msg456",
            agent_type="general",
            chunk_count=5,
            response_length=200,
            error_type="timeout"
        )
        
        stats = tracker.get_current_stats()
        assert stats["total_sessions"] == 1
        assert stats["error_rate_percent"] == 100
        assert "timeout" in stats["error_counts_by_type"]
        assert stats["error_counts_by_type"]["timeout"] == 1
    
    def test_mark_database_save_failed(self):
        """Test marking database save as failed."""
        tracker = MetricsTracker()
        
        # Start session
        tracker.start_session(user_id="user123", message_id="msg456")
        
        # Mark database save as failed
        tracker.mark_database_save_failed("msg456")
        
        # Complete session
        tracker.complete_session(
            message_id="msg456",
            agent_type="general",
            chunk_count=10,
            response_length=500,
            error_type=None
        )
        
        stats = tracker.get_current_stats()
        assert stats["database_save_success_rate_percent"] == 0
    
    def test_multiple_sessions(self):
        """Test tracking multiple sessions."""
        tracker = MetricsTracker()
        
        # Start and complete multiple sessions
        for i in range(5):
            tracker.start_session(user_id=f"user{i}", message_id=f"msg{i}")
            tracker.complete_session(
                message_id=f"msg{i}",
                agent_type="general",
                chunk_count=10 + i,
                response_length=500 + i * 100,
                error_type=None
            )
        
        stats = tracker.get_current_stats()
        assert stats["total_sessions"] == 5
        assert stats["active_sessions"] == 0
        assert stats["error_rate_percent"] == 0
    
    def test_mixed_success_and_error_sessions(self):
        """Test tracking sessions with mixed success and errors."""
        tracker = MetricsTracker()
        
        # Successful session
        tracker.start_session(user_id="user1", message_id="msg1")
        tracker.complete_session(
            message_id="msg1",
            agent_type="general",
            chunk_count=10,
            response_length=500,
            error_type=None
        )
        
        # Error session
        tracker.start_session(user_id="user2", message_id="msg2")
        tracker.complete_session(
            message_id="msg2",
            agent_type="general",
            chunk_count=5,
            response_length=200,
            error_type="timeout"
        )
        
        # Another successful session
        tracker.start_session(user_id="user3", message_id="msg3")
        tracker.complete_session(
            message_id="msg3",
            agent_type="diet",
            chunk_count=15,
            response_length=800,
            error_type=None
        )
        
        stats = tracker.get_current_stats()
        assert stats["total_sessions"] == 3
        assert stats["error_rate_percent"] == pytest.approx(33.33, rel=0.1)
        assert stats["error_counts_by_type"]["timeout"] == 1
    
    def test_complete_unknown_session(self):
        """Test completing a session that was never started."""
        tracker = MetricsTracker()
        
        # Try to complete a session that doesn't exist
        tracker.complete_session(
            message_id="unknown",
            agent_type="general",
            chunk_count=10,
            response_length=500,
            error_type=None
        )
        
        # Should not crash, just log a warning
        stats = tracker.get_current_stats()
        assert stats["total_sessions"] == 0
