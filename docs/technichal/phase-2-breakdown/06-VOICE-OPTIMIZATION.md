# Sub-Doc 6: Voice Optimization & Production Readiness

## Document Information
**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Ready for Implementation  
**Parent:** [00-PHASE-2-OVERVIEW.md](./00-PHASE-2-OVERVIEW.md)  
**Dependencies:** Sub-Doc 5 (Voice Agent)

---

## Objective

Optimize voice interactions for production:
- Achieve <2s latency (95th percentile)
- Implement context caching
- Add monitoring and metrics
- Error handling and graceful degradation
- Load testing and performance tuning

---

## Prerequisites Verification

```bash
# Verify voice agent works
poetry run pytest backend/tests/test_voice_agent_integration.py -v

# Verify voice sessions can be created
poetry run pytest backend/tests/test_voice_sessions.py -v
```

---

## Optimization Strategies

### 1. Context Caching with Redis

**File:** `backend/app/services/context_cache.py`

```python
"""Redis-based context caching for voice mode"""
import json
import redis.asyncio as redis
from typing import Optional
import logging

from app.core.config import settings
from app.agents.context import AgentContext

logger = logging.getLogger(__name__)


class ContextCache:
    """Cache agent context in Redis for voice sessions"""
    
    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    def _cache_key(self, user_id: str) -> str:
        """Generate cache key for user context"""
        return f"agent_context:{user_id}"
    
    async def get(self, user_id: str) -> Optional[AgentContext]:
        """Get cached context"""
        try:
            key = self._cache_key(user_id)
            data = await self.redis.get(key)
            
            if data:
                context_dict = json.loads(data)
                return AgentContext(**context_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, user_id: str, context: AgentContext):
        """Cache context with TTL"""
        try:
            key = self._cache_key(user_id)
            data = context.model_dump_json()
            
            await self.redis.setex(
                key,
                settings.VOICE_CONTEXT_CACHE_TTL,
                data
            )
            
            logger.info(f"Cached context for user {user_id}")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def invalidate(self, user_id: str):
        """Invalidate cached context"""
        try:
            key = self._cache_key(user_id)
            await self.redis.delete(key)
            logger.info(f"Invalidated cache for user {user_id}")
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
    
    async def close(self):
        """Close Redis connection"""
        await self.redis.close()


# Global cache instance
_context_cache: Optional[ContextCache] = None


def get_context_cache() -> ContextCache:
    """Get global context cache instance"""
    global _context_cache
    if _context_cache is None:
        _context_cache = ContextCache()
    return _context_cache
```

**Update Context Loader:**

**File:** `backend/app/services/context_loader.py`

```python
async def load_agent_context(
    db: AsyncSession,
    user_id: str,
    include_history: bool = True,
    use_cache: bool = False
) -> AgentContext:
    """Load agent context with optional caching"""
    
    # Try cache first if enabled
    if use_cache:
        from app.services.context_cache import get_context_cache
        cache = get_context_cache()
        cached_context = await cache.get(user_id)
        
        if cached_context:
            logger.info(f"Context cache hit for user {user_id}")
            return cached_context
    
    # Load from database
    context = await _load_from_database(db, user_id, include_history)
    
    # Cache if enabled
    if use_cache:
        from app.services.context_cache import get_context_cache
        cache = get_context_cache()
        await cache.set(user_id, context)
    
    return context
```

**Update Voice Agent:**

```python
async def initialize_orchestrator(self):
    """Pre-load with caching"""
    async with async_session_maker() as db:
        # Use cache for voice mode
        self.user_context = await load_agent_context(
            db,
            self.user_id,
            use_cache=True  # Enable caching
        )
        # ... rest of initialization
```

---

### 2. Metrics and Monitoring

**File:** `backend/app/core/metrics.py`

```python
"""Prometheus metrics for monitoring"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import APIRouter
from fastapi.responses import Response
import time

# Voice path metrics
voice_session_total = Counter(
    'voice_sessions_total',
    'Total voice sessions created',
    ['agent_type']
)

voice_latency = Histogram(
    'voice_response_latency_seconds',
    'Voice response latency',
    ['component'],  # stt, llm, tts, total
    buckets=[0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
)

voice_errors = Counter(
    'voice_errors_total',
    'Voice interaction errors',
    ['error_type']
)

# Text path metrics
text_request_total = Counter(
    'text_requests_total',
    'Total text chat requests',
    ['agent_type']
)

text_latency = Histogram(
    'text_response_latency_seconds',
    'Text response latency',
    ['agent_type'],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
)

# LangChain metrics
langchain_calls = Counter(
    'langchain_llm_calls_total',
    'Total LangChain LLM calls',
    ['provider', 'model', 'agent_type']
)

langchain_tokens = Counter(
    'langchain_tokens_total',
    'Total tokens used',
    ['provider', 'model', 'type']  # type: prompt | completion
)

# LiveKit metrics
livekit_rooms_active = Gauge(
    'livekit_rooms_active',
    'Active LiveKit rooms'
)

# Context cache metrics
context_cache_hits = Counter(
    'context_cache_hits_total',
    'Context cache hits'
)

context_cache_misses = Counter(
    'context_cache_misses_total',
    'Context cache misses'
)


# Metrics endpoint
router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )


# Helper functions
class LatencyTracker:
    """Context manager for tracking latency"""
    
    def __init__(self, histogram: Histogram, label: str):
        self.histogram = histogram
        self.label = label
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.histogram.labels(component=self.label).observe(duration)
```

**Register Metrics Endpoint:**

**File:** `backend/app/main.py`

```python
from app.core.metrics import router as metrics_router

app.include_router(metrics_router)
```

**Update Voice Agent with Metrics:**

```python
from app.core.metrics import (
    voice_session_total,
    voice_latency,
    voice_errors,
    LatencyTracker
)

async def entrypoint(ctx: JobContext):
    """Entrypoint with metrics"""
    
    # Track session creation
    metadata = json.loads(ctx.room.metadata or "{}")
    agent_type = metadata.get("agent_type", "general")
    voice_session_total.labels(agent_type=agent_type).inc()
    
    try:
        # ... existing code ...
        
        # Track latency
        with LatencyTracker(voice_latency, "total"):
            await session.start(room=ctx.room, agent=agent)
            await session.generate_reply(...)
            await session.wait_for_completion()
            
    except Exception as e:
        voice_errors.labels(error_type=type(e).__name__).inc()
        raise
```

---

### 3. Error Handling and Graceful Degradation

**File:** `backend/app/livekit_agents/error_handling.py`

```python
"""Error handling for voice agents"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceAgentError(Exception):
    """Base exception for voice agent errors"""
    pass


class ContextLoadError(VoiceAgentError):
    """Failed to load user context"""
    pass


class LLMError(VoiceAgentError):
    """LLM API error"""
    pass


class STTError(VoiceAgentError):
    """Speech-to-text error"""
    pass


class TTSError(VoiceAgentError):
    """Text-to-speech error"""
    pass


async def handle_voice_error(
    error: Exception,
    session,
    fallback_message: Optional[str] = None
) -> bool:
    """Handle voice agent errors gracefully
    
    Args:
        error: The exception that occurred
        session: LiveKit agent session
        fallback_message: Optional fallback message to speak
        
    Returns:
        True if error was handled, False if should propagate
    """
    
    if isinstance(error, ContextLoadError):
        logger.error(f"Context load error: {error}")
        await session.generate_reply(
            instructions="Apologize and say you're having trouble loading their profile. Ask them to try again."
        )
        return True
    
    elif isinstance(error, LLMError):
        logger.error(f"LLM error: {error}")
        await session.generate_reply(
            instructions="Apologize and say you're having trouble thinking right now. Suggest they try text chat."
        )
        return True
    
    elif isinstance(error, (STTError, TTSError)):
        logger.error(f"Voice processing error: {error}")
        # Can't speak if TTS is broken, just log
        return True
    
    else:
        logger.error(f"Unexpected error: {error}", exc_info=True)
        if fallback_message and session:
            try:
                await session.generate_reply(
                    instructions=fallback_message or "Apologize for technical difficulties"
                )
            except:
                pass
        return False
```

**Update Voice Agent:**

```python
from app.livekit_agents.error_handling import handle_voice_error, ContextLoadError

async def entrypoint(ctx: JobContext):
    """Entrypoint with error handling"""
    
    try:
        # ... existing code ...
        
        # Initialize with error handling
        try:
            await agent.initialize_orchestrator()
        except Exception as e:
            raise ContextLoadError(f"Failed to load context: {e}")
        
        # ... rest of code ...
        
    except Exception as e:
        handled = await handle_voice_error(e, session if 'session' in locals() else None)
        if not handled:
            raise
```

---

### 4. Load Testing

**File:** `backend/tests/load_test_voice.py`

```python
"""Load test for voice sessions"""
import asyncio
import time
from httpx import AsyncClient
import statistics


async def create_voice_session(client: AsyncClient, token: str):
    """Create a voice session and measure latency"""
    start = time.time()
    
    response = await client.post(
        "/api/v1/voice-sessions/start",
        json={"agent_type": "workout"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    latency = time.time() - start
    return response.status_code == 200, latency


async def load_test(num_concurrent: int = 10, num_requests: int = 100):
    """Run load test"""
    
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Get auth token
        auth_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password"}
        )
        token = auth_response.json()["access_token"]
        
        # Run concurrent requests
        latencies = []
        successes = 0
        
        for batch in range(0, num_requests, num_concurrent):
            tasks = [
                create_voice_session(client, token)
                for _ in range(min(num_concurrent, num_requests - batch))
            ]
            
            results = await asyncio.gather(*tasks)
            
            for success, latency in results:
                if success:
                    successes += 1
                    latencies.append(latency)
        
        # Calculate statistics
        print(f"\n=== Load Test Results ===")
        print(f"Total Requests: {num_requests}")
        print(f"Successful: {successes}")
        print(f"Failed: {num_requests - successes}")
        print(f"\nLatency Statistics:")
        print(f"  Mean: {statistics.mean(latencies):.3f}s")
        print(f"  Median: {statistics.median(latencies):.3f}s")
        print(f"  P95: {statistics.quantiles(latencies, n=20)[18]:.3f}s")
        print(f"  P99: {statistics.quantiles(latencies, n=100)[98]:.3f}s")
        print(f"  Min: {min(latencies):.3f}s")
        print(f"  Max: {max(latencies):.3f}s")


if __name__ == "__main__":
    asyncio.run(load_test(num_concurrent=10, num_requests=100))
```

**Run Load Test:**

```bash
poetry run python backend/tests/load_test_voice.py
```

---

### 5. Performance Tuning Checklist

- [ ] **Context Caching**: Redis cache for user context (saves 200-500ms)
- [ ] **Connection Pooling**: Database connection pool sized appropriately
- [ ] **LLM Model Selection**: Use GPT-4o-mini or Haiku for classification
- [ ] **Response Length**: Limit voice responses to 150 tokens
- [ ] **Pre-warming**: Warm up LLM connections on agent start
- [ ] **Async Logging**: Non-blocking database writes
- [ ] **CDN for Assets**: Exercise GIFs served from CDN
- [ ] **Horizontal Scaling**: Multiple agent workers

---

### 6. Monitoring Dashboard

**Grafana Dashboard JSON:**

**File:** `monitoring/grafana-dashboard.json`

```json
{
  "dashboard": {
    "title": "Fitness AI Voice Agents",
    "panels": [
      {
        "title": "Voice Response Latency (P95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, voice_response_latency_seconds_bucket)"
        }],
        "type": "graph"
      },
      {
        "title": "Active Voice Sessions",
        "targets": [{
          "expr": "livekit_rooms_active"
        }],
        "type": "stat"
      },
      {
        "title": "Voice Errors",
        "targets": [{
          "expr": "rate(voice_errors_total[5m])"
        }],
        "type": "graph"
      },
      {
        "title": "Context Cache Hit Rate",
        "targets": [{
          "expr": "rate(context_cache_hits_total[5m]) / (rate(context_cache_hits_total[5m]) + rate(context_cache_misses_total[5m]))"
        }],
        "type": "gauge"
      }
    ]
  }
}
```

---

## Verification Checklist

- [ ] Context caching implemented
- [ ] Metrics collection working
- [ ] Error handling in place
- [ ] Load test passes
- [ ] P95 latency <2 seconds
- [ ] Monitoring dashboard configured
- [ ] Graceful degradation works
- [ ] Horizontal scaling tested

**Performance Test:**

```bash
# Run load test
poetry run python backend/tests/load_test_voice.py

# Check metrics
curl http://localhost:8000/metrics | grep voice_response_latency

# Verify P95 < 2 seconds
```

---

## Production Deployment Checklist

### Infrastructure
- [ ] LiveKit server deployed (cloud or self-hosted)
- [ ] Multiple agent workers running (2+ replicas)
- [ ] Redis cluster for caching
- [ ] PostgreSQL with connection pooling
- [ ] Prometheus + Grafana for monitoring

### Configuration
- [ ] All API keys configured
- [ ] Environment variables set
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Rate limiting enabled

### Monitoring
- [ ] Metrics endpoint accessible
- [ ] Grafana dashboard imported
- [ ] Alerts configured (latency, errors, uptime)
- [ ] Log aggregation setup (ELK, Datadog, etc.)

### Testing
- [ ] Load test passed (100+ concurrent sessions)
- [ ] Latency requirements met (P95 <2s)
- [ ] Error rate <1%
- [ ] Failover tested
- [ ] Recovery tested

---

## Success Criteria

✅ Voice latency <2s (P95)  
✅ Text latency <3s (P95)  
✅ Context caching working  
✅ Metrics collected  
✅ Error handling robust  
✅ Load test passed  
✅ Monitoring dashboard live  
✅ Production ready  

**Estimated Time:** 3-4 days

---

## Phase 2 Complete!

Once this sub-doc is verified, Phase 2 (AI Integration) is complete. The system now has:

✅ LangChain agent framework  
✅ 6 specialized agents  
✅ Text chat API  
✅ LiveKit voice infrastructure  
✅ Voice agent workers  
✅ Production-grade optimization  

**Next Phase:** Phase 3 (Background Jobs & Scheduling) or Phase 4 (Client Integration)
