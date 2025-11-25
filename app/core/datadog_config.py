import os
from datadog import initialize, statsd
from ddtrace import tracer
import psutil
import logging

logger = logging.getLogger(__name__)

class DatadogMetrics:
    """Datadog metrics client for tracking application metrics."""
    
    def __init__(self):
        self.initialized = False
        self._initialize_datadog()
    
    def _initialize_datadog(self):
        """Initialize Datadog client with configuration from environment."""
        try:
            api_key = os.getenv('DD_API_KEY')
            if not api_key:
                logger.warning("DD_API_KEY not set, Datadog metrics disabled")
                self.initialized = False
                return
            
            options = {
                'api_key': api_key,
                'app_key': os.getenv('DD_APP_KEY', ''),
            }
            
            # Only configure statsd if agent is available
            statsd_host = os.getenv('DD_AGENT_HOST', 'localhost')
            statsd_port = int(os.getenv('DD_DOGSTATSD_PORT', 8125))
            
            # Check if running in agentless mode
            if os.getenv('DD_AGENTLESS_MODE', 'false').lower() == 'true':
                logger.info("Running in agentless mode - using direct API submission")
                options['statsd_host'] = None
            else:
                options['statsd_host'] = statsd_host
                options['statsd_port'] = statsd_port
            
            initialize(**options)
            self.initialized = True
            logger.info("Datadog metrics initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Datadog: {e}")
            self.initialized = False
    
    def increment_counter(self, metric_name: str, value: int = 1, tags: list = None):
        """Increment a counter metric."""
        if self.initialized:
            statsd.increment(metric_name, value=value, tags=tags or [])
    
    def record_gauge(self, metric_name: str, value: float, tags: list = None):
        """Record a gauge metric."""
        if self.initialized:
            statsd.gauge(metric_name, value, tags=tags or [])
    
    def record_histogram(self, metric_name: str, value: float, tags: list = None):
        """Record a histogram metric (for distributions like response times)."""
        if self.initialized:
            statsd.histogram(metric_name, value, tags=tags or [])
    
    def record_timing(self, metric_name: str, value: float, tags: list = None):
        """Record a timing metric in milliseconds."""
        if self.initialized:
            statsd.timing(metric_name, value, tags=tags or [])
    
    def get_system_metrics(self):
        """Get current system metrics (CPU, memory)."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available_mb': psutil.virtual_memory().available / (1024 * 1024)
        }
    
    def track_system_metrics(self):
        """Track and send system metrics to Datadog."""
        if not self.initialized:
            return
        
        try:
            metrics = self.get_system_metrics()
            self.record_gauge('nexus.analytics.system.cpu_percent', metrics['cpu_percent'])
            self.record_gauge('nexus.analytics.system.memory_percent', metrics['memory_percent'])
            self.record_gauge('nexus.analytics.system.memory_available_mb', metrics['memory_available_mb'])
        except Exception as e:
            logger.error(f"Error tracking system metrics: {e}")


# Global instance
datadog_metrics = DatadogMetrics()
