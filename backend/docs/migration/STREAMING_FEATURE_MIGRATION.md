# Chat Text Streaming Feature Migration Guide

**Feature:** Real-time text streaming for chat responses  
**Version:** 1.0.0  
**Migration Date:** TBD  
**Status:** Ready for rollout

---

## Table of Contents

1. [Overview](#overview)
2. [Feature Flag Configuration](#feature-flag-configuration)
3. [Rollout Plan](#rollout-plan)
4. [Monitoring Metrics](#monitoring-metrics)
5. [Rollback Procedure](#rollback-procedure)
6. [Testing Checklist](#testing-checklist)
7. [Known Issues](#known-issues)
8. [Support](#support)

---

## Overview

This migration introduces real-time text streaming for chat responses using Server-Sent Events (SSE). The feature replaces the current loading indicator with incremental text display as AI responses are generated.

### What's Changing

**Before:**
- User sends message → Loading indicator → Complete response appears

**After:**
- User sends message → Response streams word-by-word in real-time

### Benefits

- Improved perceived performance (first chunk arrives in ~500ms)
- Better user experience with real-time feedback
- Reduced perceived wait time for long responses
- Maintains backward compatibility with non-streaming endpoints

### Technical Changes

**Backend:**
- New endpoints: `GET /api/v1/chat/stream` and `GET /api/v1/chat/onboarding-stream`
- SSE event streaming using FastAPI StreamingResponse
- LangChain `astream()` integration for chunk generation
- Database persistence after streaming completes

**Frontend:**
- EventSource API for consuming SSE streams
- Real-time message state updates
- Typing indicators during streaming
- Error handling and retry logic

**Infrastructure:**
- Nginx configuration for SSE (buffering disabled)
- Extended timeout settings for long-lived connections

---

## Feature Flag Configuration

### Environment Variable

Add to `.env` file:

```bash
# Enable/disable streaming feature
ENABLE_STREAMING=true

# Streaming timeout (seconds)
STREAMING_TIMEOUT=60

# Maximum concurrent streams per user
MAX_CONCURRENT_STREAMS=1
```

### Application Configuration

Update `backend/app/config.py`:

```python
class Settings(BaseSettings):
    # Streaming feature flags
    enable_streaming: bool = Field(default=False, env="ENABLE_STREAMING")
    streaming_timeout: int = Field(default=60, env="STREAMING_TIMEOUT")
    max_concurrent_streams: int = Field(default=1, env="MAX_CONCURRENT_STREAMS")
```

### Frontend Configuration

Update `frontend/src/config.ts`:

```typescript
export const config = {
  enableStreaming: process.env.REACT_APP_ENABLE_STREAMING === 'true',
  streamingFallback: true, // Fall back to non-streaming if EventSource unavailable
};
```

### Feature Flag Behavior

| Flag Value | Behavior |
|------------|----------|
| `ENABLE_STREAMING=true` | Streaming endpoints active, frontend uses SSE |
| `ENABLE_STREAMING=false` | Streaming endpoints return 404, frontend uses non-streaming |
| Not set | Defaults to `false` (safe default) |

---

## Rollout Plan

### Phase 1: Internal Testing (Week 1)

**Goal:** Validate streaming functionality in staging environment

**Steps:**
1. Deploy to staging with `ENABLE_STREAMING=true`
2. Run automated test suite (unit + integration + property tests)
3. Manual testing by development team
4. Load testing with 100 concurrent users
5. Monitor metrics for 48 hours

**Success Criteria:**
- All tests pass
- No errors in logs
- Response time p95 < 2 seconds
- Stream completion rate > 99%

**Rollback Trigger:**
- Error rate > 1%
- Stream timeout rate > 5%
- Database save failure rate > 0.1%

---

### Phase 2: Beta Users (Week 2)

**Goal:** Test with real users in production

**Steps:**
1. Deploy to production with `ENABLE_STREAMING=false`
2. Enable feature flag for 5% of users (beta group)
3. Monitor metrics for 72 hours
4. Collect user feedback
5. Fix any issues discovered

**Beta User Selection:**
- Internal team members
- Early adopters who opted in
- Users with completed onboarding

**Success Criteria:**
- User satisfaction score > 4/5
- Error rate < 0.5%
- No critical bugs reported
- Performance metrics within targets

**Rollback Trigger:**
- Critical bug affecting user experience
- Error rate > 2%
- Negative user feedback > 20%

---

### Phase 3: Gradual Rollout (Week 3-4)

**Goal:** Incrementally enable for all users

**Schedule:**

| Day | Percentage | User Count (est.) | Monitoring Period |
|-----|------------|-------------------|-------------------|
| Day 1 | 10% | ~1,000 | 24 hours |
| Day 3 | 25% | ~2,500 | 24 hours |
| Day 5 | 50% | ~5,000 | 48 hours |
| Day 8 | 75% | ~7,500 | 48 hours |
| Day 11 | 100% | ~10,000 | 72 hours |

**Steps for Each Increment:**
1. Update feature flag percentage
2. Deploy configuration change (no code deploy)
3. Monitor metrics for specified period
4. Verify no degradation in performance
5. Proceed to next increment or rollback

**Success Criteria:**
- Error rate remains < 0.5%
- Response time p95 < 2 seconds
- Stream completion rate > 99%
- No increase in support tickets

**Rollback Trigger:**
- Error rate > 1%
- Response time p95 > 5 seconds
- Stream completion rate < 95%
- Critical bug discovered

---

### Phase 4: Full Deployment (Week 5)

**Goal:** Enable streaming for all users permanently

**Steps:**
1. Set `ENABLE_STREAMING=true` for 100% of users
2. Monitor for 1 week
3. Remove feature flag code (cleanup)
4. Update documentation to reflect streaming as default

**Success Criteria:**
- Stable metrics for 7 days
- No critical issues
- User feedback positive
- Performance targets met

---

## Monitoring Metrics

### Critical Metrics (Monitor Continuously)

#### 1. Stream Completion Rate
**Definition:** Percentage of streams that complete successfully

**Target:** > 99%

**Query:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*) as completion_rate
FROM streaming_sessions
WHERE created_at > NOW() - INTERVAL '1 hour';
```

**Alert Threshold:** < 95%

---

#### 2. Stream Error Rate
**Definition:** Percentage of streams that encounter errors

**Target:** < 0.5%

**Query:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE status = 'error') * 100.0 / COUNT(*) as error_rate
FROM streaming_sessions
WHERE created_at > NOW() - INTERVAL '1 hour';
```

**Alert Threshold:** > 1%

---

#### 3. Response Time (First Chunk)
**Definition:** Time from request to first chunk received

**Target:** p95 < 1 second

**Query:**
```sql
SELECT 
  percentile_cont(0.95) WITHIN GROUP (ORDER BY first_chunk_latency_ms) as p95_latency
FROM streaming_sessions
WHERE created_at > NOW() - INTERVAL '1 hour';
```

**Alert Threshold:** p95 > 2 seconds

---

#### 4. Stream Duration
**Definition:** Total time from start to completion

**Target:** p95 < 30 seconds

**Query:**
```sql
SELECT 
  percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration
FROM streaming_sessions
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND status = 'completed';
```

**Alert Threshold:** p95 > 60 seconds

---

#### 5. Database Save Success Rate
**Definition:** Percentage of streams where conversation is saved to database

**Target:** > 99.9%

**Query:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE db_saved = true) * 100.0 / COUNT(*) as save_rate
FROM streaming_sessions
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND status = 'completed';
```

**Alert Threshold:** < 99%

---

### Secondary Metrics (Monitor Daily)

#### 6. Chunks Per Session
**Definition:** Average number of chunks per streaming session

**Target:** 20-50 chunks (varies by response length)

**Query:**
```sql
SELECT AVG(chunk_count) as avg_chunks
FROM streaming_sessions
WHERE created_at > NOW() - INTERVAL '24 hours'
  AND status = 'completed';
```

---

#### 7. Concurrent Streams
**Definition:** Number of active streams at any given time

**Target:** < 100 (adjust based on capacity)

**Query:**
```sql
SELECT COUNT(*) as active_streams
FROM streaming_sessions
WHERE status = 'active';
```

**Alert Threshold:** > 500

---

#### 8. Timeout Rate
**Definition:** Percentage of streams that timeout

**Target:** < 1%

**Query:**
```sql
SELECT 
  COUNT(*) FILTER (WHERE status = 'timeout') * 100.0 / COUNT(*) as timeout_rate
FROM streaming_sessions
WHERE created_at > NOW() - INTERVAL '24 hours';
```

**Alert Threshold:** > 5%

---

### Monitoring Dashboard

Create a real-time dashboard with:
- Stream completion rate (last hour)
- Error rate trend (last 24 hours)
- Response time percentiles (p50, p95, p99)
- Active concurrent streams
- Database save success rate
- Alert status

**Recommended Tools:**
- Grafana for visualization
- Prometheus for metrics collection
- CloudWatch/Datadog for cloud deployments

---

## Rollback Procedure

### When to Rollback

Rollback immediately if:
- Error rate > 2%
- Stream completion rate < 90%
- Critical bug affecting user experience
- Database save failure rate > 1%
- Response time p95 > 10 seconds

### Rollback Steps

#### Option 1: Feature Flag Rollback (Fastest - 30 seconds)

```bash
# 1. Disable streaming via feature flag
export ENABLE_STREAMING=false

# 2. Restart application (zero-downtime)
docker-compose restart api

# 3. Verify rollback
curl https://api.yourdomain.com/api/v1/chat/stream
# Should return 404 or redirect to non-streaming endpoint
```

**Impact:** Users immediately fall back to non-streaming chat

---

#### Option 2: Percentage Rollback (Gradual - 5 minutes)

```bash
# Reduce percentage of users with streaming enabled
# Update feature flag service to reduce from 100% to 50%, 25%, 10%, 0%

# Monitor metrics after each reduction
# Stop when metrics return to acceptable levels
```

**Impact:** Gradual reduction in streaming usage

---

#### Option 3: Code Rollback (Full - 10 minutes)

```bash
# 1. Revert to previous deployment
git revert <streaming-feature-commit>

# 2. Build and deploy
docker-compose build api
docker-compose up -d api

# 3. Verify rollback
curl https://api.yourdomain.com/api/v1/chat
# Should work with non-streaming endpoint
```

**Impact:** Complete removal of streaming feature

---

### Post-Rollback Actions

1. **Notify stakeholders** - Inform team and users of rollback
2. **Investigate root cause** - Analyze logs and metrics
3. **Document issues** - Create tickets for bugs discovered
4. **Plan fix** - Develop and test fixes in staging
5. **Schedule re-deployment** - Plan new rollout after fixes

---

## Testing Checklist

### Pre-Deployment Testing

- [ ] All unit tests pass (`poetry run pytest tests/`)
- [ ] All integration tests pass
- [ ] All property-based tests pass (100+ iterations)
- [ ] Manual testing in staging environment
- [ ] Load testing with 100 concurrent users
- [ ] Nginx configuration tested and verified
- [ ] Database migrations applied successfully
- [ ] Feature flags configured correctly
- [ ] Monitoring dashboards created
- [ ] Alert thresholds configured

### Post-Deployment Testing

- [ ] Smoke test: Send test message and verify streaming works
- [ ] Verify non-streaming endpoints still work (backward compatibility)
- [ ] Check error logs for unexpected errors
- [ ] Verify metrics are being collected
- [ ] Test rollback procedure in staging
- [ ] Verify database persistence after streaming
- [ ] Test timeout behavior (30+ second responses)
- [ ] Test error handling (invalid tokens, network errors)
- [ ] Verify CORS headers for cross-origin requests
- [ ] Test on multiple browsers (Chrome, Firefox, Safari, Edge)

### User Acceptance Testing

- [ ] Internal team testing (5+ users)
- [ ] Beta user testing (50+ users)
- [ ] Collect user feedback
- [ ] Verify accessibility with screen readers
- [ ] Test on mobile devices (iOS, Android)
- [ ] Test on slow network connections
- [ ] Verify typing indicator appears correctly
- [ ] Test retry functionality on errors

---

## Known Issues

### Issue 1: EventSource Browser Compatibility

**Description:** EventSource API not supported in Internet Explorer

**Impact:** Users on IE cannot use streaming

**Workaround:** Frontend automatically falls back to non-streaming

**Status:** Won't fix (IE is deprecated)

---

### Issue 2: Nginx Buffering on Some Configurations

**Description:** Some nginx configurations may buffer SSE events despite `proxy_buffering off`

**Impact:** Events arrive in batches instead of real-time

**Workaround:** 
- Verify `X-Accel-Buffering: no` header is set
- Disable gzip compression for SSE endpoints
- Check for intermediate proxies that may buffer

**Status:** Documented in deployment guide

---

### Issue 3: Mobile Network Timeouts

**Description:** Mobile networks may close long-lived connections after 60 seconds

**Impact:** Streams may be interrupted on mobile devices

**Workaround:** 
- Keep responses under 60 seconds
- Implement automatic reconnection on client
- Send periodic keepalive events

**Status:** Monitoring in beta phase

---

## Support

### During Rollout

**On-Call Engineer:** Available 24/7 during rollout phases

**Escalation Path:**
1. Check monitoring dashboard
2. Review error logs
3. Contact on-call engineer
4. Escalate to backend team lead if needed

### Post-Rollout

**Support Channels:**
- Slack: #backend-support
- Email: backend-team@yourdomain.com
- Incident Management: PagerDuty

**Response Times:**
- Critical (P0): 15 minutes
- High (P1): 1 hour
- Medium (P2): 4 hours
- Low (P3): 24 hours

---

## Appendix

### Useful Commands

```bash
# Check streaming endpoint health
curl -N "https://api.yourdomain.com/api/v1/chat/stream?message=test&token=TOKEN"

# Monitor active streams
docker-compose exec postgres psql -U shuren -c "SELECT COUNT(*) FROM streaming_sessions WHERE status='active';"

# View streaming errors
docker-compose logs api | grep "streaming_error"

# Check nginx configuration
sudo nginx -t

# Reload nginx
sudo nginx -s reload
```

### Related Documentation

- [API Documentation](../API_DOCUMENTATION.md)
- [Deployment Guide](../DEPLOYMENT_GUIDE.md)
- [Design Document](../../../.kiro/specs/chat-text-streaming/design.md)
- [Requirements Document](../../../.kiro/specs/chat-text-streaming/requirements.md)

---

## Changelog

### Version 1.0.0 (2026-02-17)
- Initial migration guide
- Defined rollout plan (4 phases)
- Documented monitoring metrics
- Created rollback procedures
- Added testing checklist

