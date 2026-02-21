"""
Metrics tracking for streaming chat sessions.

This module provides in-memory metrics tracking for streaming sessions.
Metrics are logged and can be exported to monitoring systems like Prometheus,
Datadog, or CloudWatch in the future.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StreamingMetrics:
    """Metrics for a single streaming session."""
    
    user_id: str
    message_id: str
    agent_type: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[int] = None
    chunk_count: int = 0
    response_length: int = 0
    error_type: Optional[str] = None
    database_save_success: bool = True
    
    def complete(self, chunk_count: int, response_length: int, error_type: Optional[str] = None):
        """Mark the streaming session as complete and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = int((self.end_time - self.start_time) * 1000)
        self.chunk_count = chunk_count
        self.response_length = response_length
        self.error_type = error_type
    
    def mark_database_save_failed(self):
        """Mark that database save failed for this session."""
        self.database_save_success = False


class MetricsTracker:
    """
    In-memory metrics tracker for streaming sessions.
    
    Tracks:
    - Streaming session duration (avg, p95, p99)
    - Chunks per session
    - Error rate by error type
    - Database save success rate
    """
    
    def __init__(self):
        self._sessions: Dict[str, StreamingMetrics] = {}
        self._completed_sessions: List[StreamingMetrics] = []
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._database_save_failures: int = 0
        self._total_sessions: int = 0
    
    def start_session(self, user_id: str, message_id: str) -> StreamingMetrics:
        """Start tracking a new streaming session."""
        metrics = StreamingMetrics(user_id=user_id, message_id=message_id)
        self._sessions[message_id] = metrics
        return metrics
    
    def complete_session(
        self,
        message_id: str,
        agent_type: str,
        chunk_count: int,
        response_length: int,
        error_type: Optional[str] = None
    ):
        """Complete a streaming session and record metrics."""
        if message_id not in self._sessions:
            logger.warning(f"Attempted to complete unknown session: {message_id}")
            return
        
        metrics = self._sessions[message_id]
        metrics.agent_type = agent_type
        metrics.complete(chunk_count, response_length, error_type)
        
        # Move to completed sessions
        self._completed_sessions.append(metrics)
        del self._sessions[message_id]
        
        # Update counters
        self._total_sessions += 1
        if error_type:
            self._error_counts[error_type] += 1
        if not metrics.database_save_success:
            self._database_save_failures += 1
        
        # Log metrics
        self._log_session_metrics(metrics)
        
        # Periodically log aggregate metrics (every 100 sessions)
        if self._total_sessions % 100 == 0:
            self._log_aggregate_metrics()
    
    def mark_database_save_failed(self, message_id: str):
        """Mark that database save failed for a session."""
        if message_id in self._sessions:
            self._sessions[message_id].mark_database_save_failed()
    
    def _log_session_metrics(self, metrics: StreamingMetrics):
        """Log metrics for a completed session."""
        logger.info(
            "Streaming session metrics",
            extra={
                "event": "session_metrics",
                "user_id": metrics.user_id,
                "message_id": metrics.message_id,
                "agent_type": metrics.agent_type,
                "duration_ms": metrics.duration_ms,
                "chunk_count": metrics.chunk_count,
                "response_length": metrics.response_length,
                "error_type": metrics.error_type,
                "database_save_success": metrics.database_save_success
            }
        )
    
    def _log_aggregate_metrics(self):
        """Log aggregate metrics across all completed sessions."""
        if not self._completed_sessions:
            return
        
        # Calculate duration statistics
        durations = [s.duration_ms for s in self._completed_sessions if s.duration_ms is not None]
        if durations:
            durations_sorted = sorted(durations)
            avg_duration = sum(durations) / len(durations)
            p95_duration = durations_sorted[int(len(durations_sorted) * 0.95)] if len(durations_sorted) > 0 else 0
            p99_duration = durations_sorted[int(len(durations_sorted) * 0.99)] if len(durations_sorted) > 0 else 0
        else:
            avg_duration = p95_duration = p99_duration = 0
        
        # Calculate chunk statistics
        chunks = [s.chunk_count for s in self._completed_sessions]
        avg_chunks = sum(chunks) / len(chunks) if chunks else 0
        
        # Calculate error rate
        error_count = sum(1 for s in self._completed_sessions if s.error_type is not None)
        error_rate = (error_count / len(self._completed_sessions)) * 100 if self._completed_sessions else 0
        
        # Calculate database save success rate
        db_success_rate = ((self._total_sessions - self._database_save_failures) / self._total_sessions) * 100 if self._total_sessions > 0 else 100
        
        logger.info(
            "Aggregate streaming metrics",
            extra={
                "event": "aggregate_metrics",
                "total_sessions": self._total_sessions,
                "avg_duration_ms": int(avg_duration),
                "p95_duration_ms": p95_duration,
                "p99_duration_ms": p99_duration,
                "avg_chunks_per_session": round(avg_chunks, 2),
                "error_rate_percent": round(error_rate, 2),
                "error_counts_by_type": dict(self._error_counts),
                "database_save_success_rate_percent": round(db_success_rate, 2),
                "database_save_failures": self._database_save_failures
            }
        )
    
    def get_current_stats(self) -> Dict:
        """Get current statistics for monitoring/debugging."""
        if not self._completed_sessions:
            return {
                "total_sessions": 0,
                "active_sessions": len(self._sessions),
                "avg_duration_ms": 0,
                "error_rate_percent": 0,
                "database_save_success_rate_percent": 100
            }
        
        durations = [s.duration_ms for s in self._completed_sessions if s.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        error_count = sum(1 for s in self._completed_sessions if s.error_type is not None)
        error_rate = (error_count / len(self._completed_sessions)) * 100
        
        db_success_rate = ((self._total_sessions - self._database_save_failures) / self._total_sessions) * 100 if self._total_sessions > 0 else 100
        
        return {
            "total_sessions": self._total_sessions,
            "active_sessions": len(self._sessions),
            "avg_duration_ms": int(avg_duration),
            "error_rate_percent": round(error_rate, 2),
            "error_counts_by_type": dict(self._error_counts),
            "database_save_success_rate_percent": round(db_success_rate, 2)
        }


# Global metrics tracker instance
_metrics_tracker = MetricsTracker()


def get_metrics_tracker() -> MetricsTracker:
    """Get the global metrics tracker instance."""
    return _metrics_tracker
