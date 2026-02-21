# Onboarding Agents Monitoring Configuration

## Overview

This document provides monitoring configuration examples for the Onboarding Agent Foundation feature. Use these configurations with your monitoring system (Prometheus, Datadog, New Relic, etc.).

## Metrics to Track

### 1. Agent Response Time

**Metric Name**: `onboarding_agent_response_time_seconds`

**Type**: Histogram

**Labels**:
- `agent_type`: Type of agent (fitness_assessment, goal_setting, etc.)
- `step`: Onboarding step number (0-9)
- `status`: Response status (success, error)

**Target SLO**:
- p50: < 1 second
- p95: < 2 seconds
- p99: < 5 seconds

**Alert Conditions**:
- p95 > 5 seconds for 5 minutes
- p99 > 10 seconds for 5 minutes

**Prometheus Query Example**:
```promql
histogram_quantile(0.95, 
  rate(onboarding_agent_response_time_seconds_bucket[5m])
) > 5
```

---

### 2. Agent Error Rate

**Metric Name**: `onboarding_agent_errors_total`

**Type**: Counter

**Labels**:
- `agent_type`: Type of agent
- `error_type`: Type of error (llm_error, database_error, validation_error)
- `step`: Onboarding step number

**Target SLO**:
- Error rate < 1% of total requests
- No sustained errors for > 5 minutes

**Alert Conditions**:
- Error rate > 5% for 5 minutes
- Any errors > 10 per minute

**Prometheus Query Example**:
```promql
rate(onboarding_agent_errors_total[5m]) / 
rate(onboarding_agent_requests_total[5m]) > 0.05
```

---

### 3. LLM API Latency

**Metric Name**: `anthropic_api_latency_seconds`

**Type**: Histogram

**Labels**:
- `model`: LLM model name (claude-sonnet-4-5-20250929)
- `agent_type`: Agent making the request
- `status`: API response status (success, error, timeout)

**Target SLO**:
- p50: < 800ms
- p95: < 1.5 seconds
- p99: < 3 seconds

**Alert Conditions**:
- p95 > 3 seconds for 5 minutes
- Timeout rate > 1%

**Prometheus Query Example**:
```promql
histogram_quantile(0.95, 
  rate(anthropic_api_latency_seconds_bucket[5m])
) > 3
```

---

### 4. Database Query Time

**Metric Name**: `onboarding_db_query_time_seconds`

**Type**: Histogram

**Labels**:
- `operation`: Type of operation (load_state, save_context, update_history)
- `table`: Database table (onboarding_states)

**Target SLO**:
- p50: < 50ms
- p95: < 100ms
- p99: < 500ms

**Alert Conditions**:
- p95 > 500ms for 5 minutes
- p99 > 1 second

**Prometheus Query Example**:
```promql
histogram_quantile(0.95, 
  rate(onboarding_db_query_time_seconds_bucket[5m])
) > 0.5
```

---

### 5. Agent Requests Total

**Metric Name**: `onboarding_agent_requests_total`

**Type**: Counter

**Labels**:
- `agent_type`: Type of agent
- `step`: Onboarding step number
- `status`: Request status (success, error)

**Usage**: Track request volume and success rate

**Prometheus Query Example**:
```promql
rate(onboarding_agent_requests_total[5m])
```

---

### 6. Conversation History Size

**Metric Name**: `onboarding_conversation_history_size_bytes`

**Type**: Gauge

**Labels**:
- `user_id`: User identifier (hashed for privacy)
- `step`: Current onboarding step

**Target**: < 100KB per user

**Alert Conditions**:
- Average size > 200KB
- Any user > 500KB

---

### 7. Agent Context Size

**Metric Name**: `onboarding_agent_context_size_bytes`

**Type**: Gauge

**Labels**:
- `agent_type`: Type of agent
- `step`: Onboarding step

**Target**: < 50KB per agent

**Alert Conditions**:
- Average size > 100KB
- Any context > 200KB

---

## Log Monitoring

### Critical Log Patterns

Monitor these log patterns for issues:

#### 1. LLM API Errors

**Pattern**: `LLM API error`

**Severity**: ERROR

**Alert**: > 5 occurrences in 5 minutes

**Example Log**:
```
ERROR - LLM API error: anthropic.RateLimitError: Rate limit exceeded
```

---

#### 2. Database Errors

**Pattern**: `Error in chat_onboarding|Error in get_current_agent`

**Severity**: ERROR

**Alert**: > 3 occurrences in 5 minutes

**Example Log**:
```
ERROR - Error in chat_onboarding: sqlalchemy.exc.OperationalError: connection lost
```

---

#### 3. Agent Initialization Failures

**Pattern**: `ANTHROPIC_API_KEY is not configured`

**Severity**: ERROR

**Alert**: Any occurrence

**Example Log**:
```
ERROR - ValueError: ANTHROPIC_API_KEY is not configured
```

---

#### 4. Invalid Step Transitions

**Pattern**: `Invalid onboarding step`

**Severity**: WARNING

**Alert**: > 10 occurrences in 5 minutes

**Example Log**:
```
WARNING - ValueError: Invalid onboarding step: 10
```

---

## Dashboard Configuration

### Recommended Dashboard Panels

#### Panel 1: Agent Response Time (p95)
- Visualization: Line graph
- Metric: `onboarding_agent_response_time_seconds` (p95)
- Group by: `agent_type`
- Time range: Last 1 hour

#### Panel 2: Error Rate by Agent
- Visualization: Stacked area chart
- Metric: `onboarding_agent_errors_total` (rate)
- Group by: `agent_type`, `error_type`
- Time range: Last 1 hour

#### Panel 3: Request Volume
- Visualization: Bar chart
- Metric: `onboarding_agent_requests_total` (rate)
- Group by: `agent_type`
- Time range: Last 1 hour

#### Panel 4: LLM API Latency Distribution
- Visualization: Heatmap
- Metric: `anthropic_api_latency_seconds`
- Percentiles: p50, p95, p99
- Time range: Last 1 hour

#### Panel 5: Database Query Performance
- Visualization: Line graph
- Metric: `onboarding_db_query_time_seconds` (p95)
- Group by: `operation`
- Time range: Last 1 hour

#### Panel 6: Active Onboarding Sessions
- Visualization: Single stat
- Metric: Count of active sessions
- Time range: Current

---

## Alert Rules

### Critical Alerts (Page On-Call)

1. **High Error Rate**
   - Condition: Error rate > 10% for 5 minutes
   - Severity: Critical
   - Action: Page on-call engineer

2. **LLM API Down**
   - Condition: All LLM requests failing for 2 minutes
   - Severity: Critical
   - Action: Page on-call engineer

3. **Database Connection Lost**
   - Condition: Database errors > 50% for 2 minutes
   - Severity: Critical
   - Action: Page on-call engineer

### Warning Alerts (Slack/Email)

1. **Elevated Response Time**
   - Condition: p95 > 5 seconds for 10 minutes
   - Severity: Warning
   - Action: Notify team channel

2. **Moderate Error Rate**
   - Condition: Error rate > 5% for 10 minutes
   - Severity: Warning
   - Action: Notify team channel

3. **Slow Database Queries**
   - Condition: p95 > 500ms for 10 minutes
   - Severity: Warning
   - Action: Notify team channel

---

## Health Check Endpoints

Implement these health check endpoints for monitoring:

### 1. Anthropic API Health

**Endpoint**: `GET /api/v1/health/anthropic`

**Response**:
```json
{
  "status": "healthy",
  "latency_ms": 234,
  "last_check": "2026-02-18T10:00:00Z"
}
```

### 2. Agent Orchestrator Health

**Endpoint**: `GET /api/v1/health/agents`

**Response**:
```json
{
  "status": "healthy",
  "agents": {
    "fitness_assessment": "ready",
    "goal_setting": "ready",
    "workout_planning": "ready",
    "diet_planning": "ready",
    "scheduling": "ready"
  }
}
```

---

## Cost Monitoring

### LLM API Usage

Track Anthropic API costs:

**Metric**: `anthropic_api_tokens_total`

**Labels**:
- `type`: input_tokens, output_tokens
- `model`: Model name
- `agent_type`: Agent making the request

**Cost Calculation**:
- Input tokens: $0.003 per 1K tokens
- Output tokens: $0.015 per 1K tokens

**Alert**: Daily cost > $100

---

## Example Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'shuren-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

# Alert rules
groups:
  - name: onboarding_agents
    interval: 30s
    rules:
      - alert: HighAgentErrorRate
        expr: |
          rate(onboarding_agent_errors_total[5m]) / 
          rate(onboarding_agent_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in onboarding agents"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: SlowAgentResponse
        expr: |
          histogram_quantile(0.95, 
            rate(onboarding_agent_response_time_seconds_bucket[5m])
          ) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow agent response time"
          description: "p95 latency is {{ $value }}s"
```

---

## Example Datadog Configuration

```yaml
# datadog.yaml
logs:
  - type: file
    path: /var/log/shuren/api.log
    service: shuren-api
    source: python
    tags:
      - env:production
      - component:onboarding-agents

monitors:
  - name: "Onboarding Agent Error Rate"
    type: metric alert
    query: |
      sum(last_5m):
        sum:onboarding.agent.errors{*}.as_rate() / 
        sum:onboarding.agent.requests{*}.as_rate() > 0.05
    message: |
      Agent error rate is above 5%
      @slack-backend-alerts
    tags:
      - service:onboarding
      - severity:warning
```

---

## Troubleshooting Guide

### High Response Time

**Symptoms**: p95 latency > 5 seconds

**Possible Causes**:
1. LLM API slow
2. Database connection pool exhausted
3. Large conversation history

**Investigation Steps**:
1. Check LLM API latency metrics
2. Check database query time metrics
3. Check conversation history size
4. Review recent code changes

---

### High Error Rate

**Symptoms**: Error rate > 5%

**Possible Causes**:
1. LLM API rate limit
2. Database connection issues
3. Invalid configuration

**Investigation Steps**:
1. Check error logs for patterns
2. Verify Anthropic API key
3. Check database connectivity
4. Review environment variables

---

## Support

For monitoring setup assistance:
- DevOps Team: devops@shuren.app
- Monitoring Dashboard: https://monitoring.shuren.app
