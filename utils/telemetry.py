"""
Telemetry module for P.U.L.S.E.
Provides OpenTelemetry integration for distributed tracing and metrics
"""

import os
import logging
import structlog
from typing import Dict, Any, Optional, List, Set, Union
import time
from datetime import datetime

# Import OpenTelemetry modules with fallback to dummy implementations
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.context.context import Context
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Create dummy classes and functions for fallback
    class DummySpan:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def add_event(self, name, attributes=None): pass
        def set_attribute(self, key, value): pass
        def set_status(self, status): pass
        def record_exception(self, exception): pass
        def end(self): pass
        
    class DummyTracer:
        def start_span(self, name, context=None, kind=None, attributes=None): return DummySpan()
        def start_as_current_span(self, name, context=None, kind=None, attributes=None): return DummySpan()
        
    class DummyMeter:
        def create_counter(self, name, description=None, unit=None): return DummyCounter()
        def create_histogram(self, name, description=None, unit=None): return DummyHistogram()
        def create_gauge(self, name, description=None, unit=None): return DummyGauge()
        
    class DummyCounter:
        def add(self, amount, attributes=None): pass
        
    class DummyHistogram:
        def record(self, value, attributes=None): pass
        
    class DummyGauge:
        def set(self, value, attributes=None): pass
        
    # Create dummy trace and metrics modules
    class DummyTraceModule:
        def get_tracer(self, name, version=None): return DummyTracer()
        
    class DummyMetricsModule:
        def get_meter(self, name, version=None): return DummyMeter()
        
    trace = DummyTraceModule()
    metrics = DummyMetricsModule()

# Logger
logger = structlog.get_logger("telemetry")

# Constants
SERVICE_NAME = "pulse"
SERVICE_VERSION = "0.1.0"  # Should be read from version file or env var

class Telemetry:
    """
    Telemetry manager for P.U.L.S.E.
    Provides OpenTelemetry integration for distributed tracing and metrics
    """
    
    def __init__(self, service_name: str = SERVICE_NAME, service_version: str = SERVICE_VERSION):
        """
        Initialize telemetry manager
        
        Args:
            service_name: Name of the service
            service_version: Version of the service
        """
        self.service_name = service_name
        self.service_version = service_version
        self.enabled = OPENTELEMETRY_AVAILABLE and os.environ.get("PULSE_TELEMETRY_ENABLED", "false").lower() == "true"
        
        # Initialize OpenTelemetry if available
        if self.enabled:
            self._init_opentelemetry()
            logger.info("OpenTelemetry initialized", 
                       service_name=service_name, 
                       service_version=service_version)
        else:
            if not OPENTELEMETRY_AVAILABLE:
                logger.info("OpenTelemetry not available, using dummy implementation")
            else:
                logger.info("OpenTelemetry disabled by configuration")
        
        # Get tracer and meter
        self.tracer = trace.get_tracer(service_name, service_version)
        self.meter = metrics.get_meter(service_name, service_version)
        
        # Create standard metrics
        self._init_metrics()
    
    def _init_opentelemetry(self):
        """Initialize OpenTelemetry components"""
        if not OPENTELEMETRY_AVAILABLE:
            return
        
        # Create resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": os.environ.get("PULSE_ENVIRONMENT", "development")
        })
        
        # Set up trace provider
        trace_provider = TracerProvider(resource=resource)
        
        # Add console exporter for development
        console_processor = BatchSpanProcessor(ConsoleSpanExporter())
        trace_provider.add_span_processor(console_processor)
        
        # Add OTLP exporter if configured
        otlp_endpoint = os.environ.get("PULSE_OTLP_ENDPOINT")
        if otlp_endpoint:
            otlp_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
            trace_provider.add_span_processor(otlp_processor)
        
        # Register trace provider
        trace.set_tracer_provider(trace_provider)
        
        # Set up metrics provider
        metric_readers = []
        
        # Add console exporter for development
        console_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
        metric_readers.append(console_reader)
        
        # Add OTLP exporter if configured
        if otlp_endpoint:
            otlp_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=otlp_endpoint))
            metric_readers.append(otlp_reader)
        
        # Register metrics provider
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=metric_readers))
    
    def _init_metrics(self):
        """Initialize standard metrics"""
        # Counters
        self.request_counter = self.meter.create_counter(
            name="pulse.requests",
            description="Number of requests processed",
            unit="1"
        )
        
        self.error_counter = self.meter.create_counter(
            name="pulse.errors",
            description="Number of errors encountered",
            unit="1"
        )
        
        self.model_request_counter = self.meter.create_counter(
            name="pulse.model.requests",
            description="Number of model API requests",
            unit="1"
        )
        
        # Histograms
        self.request_duration = self.meter.create_histogram(
            name="pulse.request.duration",
            description="Duration of requests",
            unit="ms"
        )
        
        self.model_request_duration = self.meter.create_histogram(
            name="pulse.model.request.duration",
            description="Duration of model API requests",
            unit="ms"
        )
        
        self.token_count = self.meter.create_histogram(
            name="pulse.model.token_count",
            description="Number of tokens in model requests/responses",
            unit="1"
        )
    
    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a new span
        
        Args:
            name: Name of the span
            attributes: Optional attributes to add to the span
            
        Returns:
            Span object
        """
        return self.tracer.start_span(name, attributes=attributes)
    
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """
        Start a new span as the current span
        
        Args:
            name: Name of the span
            attributes: Optional attributes to add to the span
            
        Returns:
            Span context manager
        """
        return self.tracer.start_as_current_span(name, attributes=attributes)
    
    def record_request(self, request_type: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Record a request
        
        Args:
            request_type: Type of request
            attributes: Optional attributes
        """
        attrs = attributes or {}
        attrs["request.type"] = request_type
        self.request_counter.add(1, attrs)
    
    def record_error(self, error_type: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Record an error
        
        Args:
            error_type: Type of error
            attributes: Optional attributes
        """
        attrs = attributes or {}
        attrs["error.type"] = error_type
        self.error_counter.add(1, attrs)
    
    def record_model_request(self, model: str, operation: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Record a model API request
        
        Args:
            model: Model name
            operation: Operation performed
            attributes: Optional attributes
        """
        attrs = attributes or {}
        attrs["model"] = model
        attrs["operation"] = operation
        self.model_request_counter.add(1, attrs)
    
    def record_duration(self, name: str, duration_ms: float, attributes: Optional[Dict[str, Any]] = None):
        """
        Record a duration
        
        Args:
            name: Name of the operation
            duration_ms: Duration in milliseconds
            attributes: Optional attributes
        """
        attrs = attributes or {}
        attrs["operation"] = name
        self.request_duration.record(duration_ms, attrs)
    
    def record_model_duration(self, model: str, duration_ms: float, attributes: Optional[Dict[str, Any]] = None):
        """
        Record a model API request duration
        
        Args:
            model: Model name
            duration_ms: Duration in milliseconds
            attributes: Optional attributes
        """
        attrs = attributes or {}
        attrs["model"] = model
        self.model_request_duration.record(duration_ms, attrs)
    
    def record_token_count(self, model: str, input_tokens: int, output_tokens: int, attributes: Optional[Dict[str, Any]] = None):
        """
        Record token counts for a model request
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            attributes: Optional attributes
        """
        attrs = attributes or {}
        attrs["model"] = model
        
        # Record input tokens
        input_attrs = attrs.copy()
        input_attrs["token_type"] = "input"
        self.token_count.record(input_tokens, input_attrs)
        
        # Record output tokens
        output_attrs = attrs.copy()
        output_attrs["token_type"] = "output"
        self.token_count.record(output_tokens, output_attrs)
        
        # Record total tokens
        total_attrs = attrs.copy()
        total_attrs["token_type"] = "total"
        self.token_count.record(input_tokens + output_tokens, total_attrs)


# Global telemetry instance
_telemetry = None

def get_telemetry() -> Telemetry:
    """
    Get the global telemetry instance
    
    Returns:
        Telemetry instance
    """
    global _telemetry
    if _telemetry is None:
        _telemetry = Telemetry()
    return _telemetry


class TracedFunction:
    """
    Decorator for tracing function calls
    """
    
    def __init__(self, name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
        """
        Initialize traced function decorator
        
        Args:
            name: Optional name for the span (defaults to function name)
            attributes: Optional attributes to add to the span
        """
        self.name = name
        self.attributes = attributes or {}
        self.telemetry = get_telemetry()
    
    def __call__(self, func):
        """
        Decorate the function
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function
        """
        import functools
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = self.name or func.__name__
            start_time = time.time()
            
            with self.telemetry.start_span(span_name, self.attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    self.telemetry.record_duration(span_name, duration_ms, self.attributes)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_attribute("error", True)
                    raise
            
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = self.name or func.__name__
            start_time = time.time()
            
            with self.telemetry.start_span(span_name, self.attributes) as span:
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    self.telemetry.record_duration(span_name, duration_ms, self.attributes)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_attribute("error", True)
                    raise
        
        # Return the appropriate wrapper based on whether the function is async or not
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


def traced(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator for tracing function calls
    
    Args:
        name: Optional name for the span (defaults to function name)
        attributes: Optional attributes to add to the span
        
    Returns:
        Decorated function
    """
    return TracedFunction(name, attributes)


class TracedModelRequest:
    """
    Context manager for tracing model API requests
    """
    
    def __init__(self, model: str, operation: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Initialize traced model request
        
        Args:
            model: Model name
            operation: Operation being performed
            attributes: Optional attributes
        """
        self.model = model
        self.operation = operation
        self.attributes = attributes or {}
        self.telemetry = get_telemetry()
        self.start_time = None
        self.span = None
    
    def __enter__(self):
        """Enter the context manager"""
        self.start_time = time.time()
        span_name = f"model.{self.operation}"
        
        # Add model to attributes
        attrs = self.attributes.copy()
        attrs["model"] = self.model
        attrs["operation"] = self.operation
        
        # Start span
        self.span = self.telemetry.start_span(span_name, attrs)
        self.span.__enter__()
        
        # Record request
        self.telemetry.record_model_request(self.model, self.operation, self.attributes)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager"""
        # Calculate duration
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.telemetry.record_model_duration(self.model, duration_ms, self.attributes)
        
        # Record exception if any
        if exc_type is not None:
            self.span.record_exception(exc_val)
            self.span.set_attribute("error", True)
            
            # Record error
            error_type = exc_type.__name__
            self.telemetry.record_error(error_type, {
                "model": self.model,
                "operation": self.operation
            })
        
        # End span
        self.span.__exit__(exc_type, exc_val, exc_tb)
    
    def record_token_count(self, input_tokens: int, output_tokens: int):
        """
        Record token counts
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.telemetry.record_token_count(
            self.model, 
            input_tokens, 
            output_tokens, 
            self.attributes
        )
        
        # Add to span
        self.span.set_attribute("input_tokens", input_tokens)
        self.span.set_attribute("output_tokens", output_tokens)
        self.span.set_attribute("total_tokens", input_tokens + output_tokens)


def trace_model_request(model: str, operation: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for tracing model API requests
    
    Args:
        model: Model name
        operation: Operation being performed
        attributes: Optional attributes
        
    Returns:
        Context manager
    """
    return TracedModelRequest(model, operation, attributes)
