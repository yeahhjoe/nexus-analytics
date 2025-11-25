import os
import time
from dotenv import load_dotenv

# Load environment variables FIRST before other imports
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.datadog_config import datadog_metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nexus Analytics",
    version="0.1.0",
    description="Analytics microservice with Datadog monitoring"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datadog APM environment variables
os.environ.setdefault('DD_SERVICE', os.getenv('DD_SERVICE', 'nexus-analytics'))
os.environ.setdefault('DD_ENV', os.getenv('DD_ENV', 'production'))
os.environ.setdefault('DD_LOGS_INJECTION', 'true')

# Analytics query counter (in-memory for demo)
analytics_query_count = 0


@app.middleware("http")
async def datadog_middleware(request: Request, call_next):
    """Middleware to track request metrics in Datadog."""
    start_time = time.time()
    
    # Increment request counter
    datadog_metrics.increment_counter(
        'nexus.analytics.request.count',
        tags=[f'method:{request.method}', f'path:{request.url.path}']
    )
    
    # Track system metrics periodically
    datadog_metrics.track_system_metrics()
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Track response time
        datadog_metrics.record_histogram(
            'nexus.analytics.request.duration',
            response_time,
            tags=[
                f'method:{request.method}',
                f'path:{request.url.path}',
                f'status:{response.status_code}'
            ]
        )
        
        # Track successful requests
        if 200 <= response.status_code < 300:
            datadog_metrics.increment_counter(
                'nexus.analytics.request.success',
                tags=[f'method:{request.method}', f'path:{request.url.path}']
            )
        
        return response
        
    except Exception as e:
        # Track errors
        datadog_metrics.increment_counter(
            'nexus.analytics.request.error',
            tags=[
                f'method:{request.method}',
                f'path:{request.url.path}',
                f'error_type:{type(e).__name__}'
            ]
        )
        logger.error(f"Request error: {e}", exc_info=True)
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler to track HTTP errors."""
    datadog_metrics.increment_counter(
        'nexus.analytics.http.error',
        tags=[f'status:{exc.status_code}', f'path:{request.url.path}']
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.on_event("startup")
async def startup_event():
    """Log startup and track service start metric."""
    logger.info("Nexus Analytics service starting up")
    datadog_metrics.increment_counter('nexus.analytics.service.startup')


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown and track service stop metric."""
    logger.info("Nexus Analytics service shutting down")
    datadog_metrics.increment_counter('nexus.analytics.service.shutdown')


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Nexus Analytics Service"}


@app.get("/health")
async def health_check():
    """Health check endpoint with system metrics."""
    system_metrics = datadog_metrics.get_system_metrics()
    
    # Track health check
    datadog_metrics.increment_counter('nexus.analytics.health_check')
    
    return {
        "status": "healthy",
        "service": "nexus-analytics",
        "system_metrics": system_metrics
    }


@app.post("/analytics/query")
async def process_analytics_query(query: dict):
    """
    Process an analytics query and track custom business metrics.
    
    Example request:
    {
        "query_type": "user_activity",
        "parameters": {...}
    }
    """
    global analytics_query_count
    
    try:
        # Increment business metric
        analytics_query_count += 1
        
        # Track custom business metric
        datadog_metrics.increment_counter(
            'nexus.analytics.queries.processed',
            tags=[f'query_type:{query.get("query_type", "unknown")}']
        )
        
        # Track total queries as gauge
        datadog_metrics.record_gauge(
            'nexus.analytics.queries.total',
            analytics_query_count
        )
        
        # Simulate query processing
        processing_start = time.time()
        # Your actual analytics logic would go here
        result = {
            "query_id": f"query_{analytics_query_count}",
            "query_type": query.get("query_type"),
            "status": "processed",
            "result": {"sample_data": [1, 2, 3, 4, 5]}
        }
        processing_time = (time.time() - processing_start) * 1000
        
        # Track query processing time
        datadog_metrics.record_timing(
            'nexus.analytics.queries.processing_time',
            processing_time,
            tags=[f'query_type:{query.get("query_type", "unknown")}']
        )
        
        return result
        
    except Exception as e:
        # Track query errors
        datadog_metrics.increment_counter(
            'nexus.analytics.queries.error',
            tags=[f'error_type:{type(e).__name__}']
        )
        logger.error(f"Query processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Query processing failed")


@app.get("/metrics/summary")
async def metrics_summary():
    """Get a summary of current metrics."""
    system_metrics = datadog_metrics.get_system_metrics()
    
    return {
        "analytics_queries_processed": analytics_query_count,
        "system_metrics": system_metrics,
        "datadog_initialized": datadog_metrics.initialized
    }
