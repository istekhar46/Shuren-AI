# Onboarding Agent Foundation - Deployment Guide

## Overview

This document provides deployment preparation guidance for the Onboarding Agent Foundation feature, including migration procedures, rollback plans, monitoring setup, and error handling documentation.

## Database Migration

### Migration Details

**Migration File**: `alembic/versions/add_agent_fields_to_onboarding.py`

**Changes**:
- Adds `current_agent` column (String, nullable)
- Adds `agent_context` column (JSONB, default={})
- Adds `conversation_history` column (JSONB, default=[])

### Applying Migration

```bash
# Backup database first
pg_dump -h localhost -U postgres -d shuren > backup_before_agent_migration.sql

# Apply migration
cd backend
poetry run alembic upgrade head

# Verify migration
poetry run alembic current
```

### Rollback Plan

If issues occur after deployment, follow this rollback procedure:

```bash
# 1. Stop the application
docker-compose stop api

# 2. Rollback database migration
cd backend
poetry run alembic downgrade -1

# 3. Restore previous application version
git checkout <previous-commit>
docker-compose up -d --build api

# 4. Verify rollback
poetry run alembic current
```

**Rollback Considerations**:
- The new columns are nullable, so rollback is safe
- Existing data is preserved during rollback
- No data loss occurs as old code ignores new columns
- Conversation history and agent context will be lost if rollback occurs

### Migration Testing

Test the migration in staging environment:

```bash
# 1. Clone production database to staging
pg_dump -h prod-host -U postgres -d shuren | psql -h staging-host -U postgres -d shuren_staging

# 2. Apply migration in staging
cd backend
poetry run alembic upgrade head

# 3. Run integration tests
poetry run pytest tests/test_integration_*.py -v

# 4. Verify backward compatibility
poetry run pytest tests/test_onboarding_endpoints.py -v
```

## Environment Configuration

### Required Environment Variables

Add these to your `.env` file:

```bash
# Anthropic API for LLM
ANTHROPIC_API_KEY=sk-ant-...

# LLM Configuration (optional, defaults shown)
LLM_MODEL=claude-sonnet-4-5-20250929
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

### Configuration Validation

Verify configuration before deployment:

```bash
cd backend
poetry run python -c "from app.core.config import settings; print(f'Anthropic API Key: {settings.ANTHROPIC_API_KEY[:10]}...')"
```

## API Documentation

### New Endpoints

#### POST /api/v1/onboarding/chat

Chat with the current onboarding agent based on user's step.

**Authentication**: Required (JWT Bearer token)

**Request Body**:
```json
{
  "message": "I can do 10 pushups",
  "step": 1
}
```

**Response** (200 OK):
```json
{
  "message": "Great! 10 pushups shows good upper body strength...",
  "agent_type": "FITNESS_ASSESSMENT",
  "current_step": 1,
  "step_complete": false,
  "next_action": "continue"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Onboarding state not found for user
- `422 Unprocessable Entity`: Invalid request body (empty message, etc.)
- `500 Internal Server Error`: Server error processing message

#### GET /api/v1/onboarding/current-agent

Get information about the current onboarding agent.

**Authentication**: Required (JWT Bearer token)

**Response** (200 OK):
```json
{
  "agent_type": "FITNESS_ASSESSMENT",
  "current_step": 1,
  "agent_description": "I'll help assess your current fitness level",
  "context_summary": {
    "fitness_assessment": {
      "pushups": 10,
      "experience": "beginner"
    }
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Onboarding state not found for user
- `500 Internal Server Error`: Server error retrieving agent info

## Monitoring and Logging

### Log Levels

The application uses Python's standard logging with these levels:

- **ERROR**: Agent initialization failures, database errors, LLM API failures
- **WARNING**: Invalid step transitions, missing context data
- **INFO**: Agent routing decisions, step completions
- **DEBUG**: Detailed LLM interactions, context updates

### Key Log Messages

Monitor these log patterns in production:

```python
# Agent routing
logger.info(f"Routing user {user_id} to agent {agent_type} for step {step}")

# LLM errors
logger.error(f"LLM API error: {error}", exc_info=True)

# Database errors
logger.error(f"Error in chat_onboarding: {e}", exc_info=True)

# Context updates
logger.debug(f"Updated agent context for user {user_id}: {context}")
```

### Monitoring Metrics

Track these metrics in your monitoring system:

1. **Agent Response Time**
   - Metric: `onboarding_agent_response_time_seconds`
   - Target: < 2 seconds (p95)
   - Alert: > 5 seconds

2. **Agent Error Rate**
   - Metric: `onboarding_agent_errors_total`
   - Target: < 1% of requests
   - Alert: > 5% error rate

3. **LLM API Latency**
   - Metric: `anthropic_api_latency_seconds`
   - Target: < 1.5 seconds (p95)
   - Alert: > 3 seconds

4. **Database Query Time**
   - Metric: `onboarding_db_query_time_seconds`
   - Target: < 100ms (p95)
   - Alert: > 500ms

### Health Checks

Add these health check endpoints to verify agent system:

```python
# Check Anthropic API connectivity
GET /api/v1/health/anthropic

# Check agent orchestrator
GET /api/v1/health/agents
```

## Error Handling

### Error Codes and Responses

| HTTP Code | Error Type | Description | User Action |
|-----------|------------|-------------|-------------|
| 401 | Unauthorized | Missing/invalid JWT token | Re-authenticate |
| 404 | Not Found | Onboarding state not found | Start onboarding |
| 422 | Validation Error | Invalid request body | Fix request format |
| 500 | Internal Error | Server error | Retry or contact support |

### Common Error Scenarios

#### 1. Anthropic API Key Missing

**Error**: `ValueError: ANTHROPIC_API_KEY is not configured`

**Solution**:
```bash
# Add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." >> backend/.env

# Restart application
docker-compose restart api
```

#### 2. Invalid Onboarding Step

**Error**: `ValueError: Invalid onboarding step: 10`

**Solution**: This indicates data corruption. Check database:
```sql
SELECT user_id, current_step FROM onboarding_states WHERE current_step > 9;
```

#### 3. LLM API Rate Limit

**Error**: `anthropic.RateLimitError: Rate limit exceeded`

**Solution**: Implement exponential backoff or upgrade API tier

#### 4. Database Connection Lost

**Error**: `sqlalchemy.exc.OperationalError: connection lost`

**Solution**: Check database connectivity and connection pool settings

## Deployment Checklist

### Pre-Deployment

- [ ] Run all tests: `poetry run pytest --cov=app`
- [ ] Verify test coverage > 80%
- [ ] Test migration on staging database
- [ ] Verify backward compatibility tests pass
- [ ] Update `.env.example` with new variables
- [ ] Review and merge PR
- [ ] Tag release: `git tag v1.1.0-onboarding-agents`

### Deployment Steps

1. **Backup Production Database**
   ```bash
   pg_dump -h prod-host -U postgres -d shuren > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Deploy Application**
   ```bash
   git pull origin main
   docker-compose down
   docker-compose up -d --build
   ```

3. **Run Migration**
   ```bash
   docker-compose exec api poetry run alembic upgrade head
   ```

4. **Verify Deployment**
   ```bash
   # Check health
   curl https://api.shuren.app/health
   
   # Check new endpoints
   curl -H "Authorization: Bearer $TOKEN" https://api.shuren.app/api/v1/onboarding/current-agent
   ```

5. **Monitor Logs**
   ```bash
   docker-compose logs -f api
   ```

### Post-Deployment

- [ ] Verify health checks pass
- [ ] Test new endpoints with real user
- [ ] Monitor error rates for 1 hour
- [ ] Check LLM API usage and costs
- [ ] Verify conversation history is being saved
- [ ] Update documentation site
- [ ] Notify team of successful deployment

## Performance Considerations

### Expected Load

- **Concurrent Users**: 100-500 during onboarding
- **Messages per User**: 20-50 during complete onboarding
- **Average Response Time**: 1-2 seconds
- **LLM API Calls**: 1 per message

### Optimization Tips

1. **Database Connection Pool**: Ensure adequate pool size
   ```python
   # In config.py
   pool_size=20
   max_overflow=10
   ```

2. **LLM Response Caching**: Consider caching common responses
   - Cache key: `hash(agent_type + message)`
   - TTL: 1 hour
   - Hit rate target: 20-30%

3. **Context Size Management**: Limit conversation history
   ```python
   # Keep last 20 messages only
   conversation_history = conversation_history[-20:]
   ```

## Security Considerations

### Authentication

- All endpoints require JWT authentication
- Tokens expire after 24 hours
- Refresh tokens required for extended sessions

### Data Privacy

- Conversation history contains PII
- Agent context may contain health information
- Ensure GDPR compliance for data retention
- Implement data deletion on user request

### API Key Security

- Never commit API keys to version control
- Use environment variables or secrets manager
- Rotate keys quarterly
- Monitor API usage for anomalies

## Support and Troubleshooting

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# In .env
LOG_LEVEL=DEBUG

# Restart application
docker-compose restart api
```

### Common Issues

1. **Agent not responding**: Check Anthropic API status
2. **Context not persisting**: Verify database commits
3. **Wrong agent for step**: Check step-to-agent mapping
4. **Slow responses**: Monitor LLM API latency

### Contact

For deployment issues, contact:
- DevOps Team: devops@shuren.app
- Backend Team: backend@shuren.app
- On-call: +1-XXX-XXX-XXXX