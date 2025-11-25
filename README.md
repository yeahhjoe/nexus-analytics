# Nexus Analytics

Microservice for Nexus Analytics functionality with Datadog monitoring integration.

## Features

- RESTful API for analytics queries
- Datadog APM and metrics integration
- Tracks:
  - API request counts and response times
  - Error rates
  - Custom business metrics (analytics queries processed)
  - System metrics (CPU, memory usage)
  - Service health checks

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update with your Datadog API key and settings

4. Run the application:
   
   **Without Datadog Agent (Development):**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```
   
   **With Datadog Agent (Production):**
   ```bash
   ddtrace-run uvicorn app.main:app --reload --port 8001
   ```
   
   Note: If you see errors about connecting to `169.254.169.254`, install the Datadog Agent:
   ```bash
   DD_API_KEY=your_key DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_mac_os.sh)"
   ```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check with system metrics
- `POST /analytics/query` - Process analytics queries
- `GET /metrics/summary` - Get metrics summary

## Datadog Integration

The service automatically sends the following metrics to Datadog:

- `nexus.analytics.request.count` - Total HTTP requests
- `nexus.analytics.request.duration` - Request response times (histogram)
- `nexus.analytics.request.success` - Successful requests
- `nexus.analytics.request.error` - Failed requests
- `nexus.analytics.queries.processed` - Analytics queries processed
- `nexus.analytics.queries.total` - Total queries (gauge)
- `nexus.analytics.queries.processing_time` - Query processing time
- `nexus.analytics.system.cpu_percent` - CPU usage
- `nexus.analytics.system.memory_percent` - Memory usage
- `nexus.analytics.health_check` - Health check calls

## Example Usage

```bash
# Process an analytics query
curl -X POST http://localhost:8001/analytics/query \
  -H "Content-Type: application/json" \
  -d '{"query_type": "user_activity", "parameters": {}}'
```
