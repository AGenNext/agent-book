"""
OpenTelemetry & SigNoz Integration

Initialize tracing and metrics for observability.
"""

import os
from loguru import logger


def init_telemetry():
    """
    Initialize OpenTelemetry tracing and metrics.
    
    Supports:
    - SigNoz (OTLP exporter)
    - Jaeger
    - Zipkin
    - Console exporter (development)
    """
    
    # Check if telemetry is disabled
    if os.getenv("OTEL_ENABLED", "true").lower() == "false":
        logger.info("OpenTelemetry disabled")
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.semconv.resource import ResourceAttributes
        
        # Service name
        service_name = os.getenv("OTEL_SERVICE_NAME", "open-notebook")
        
        # Create resource with service info
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("OTEL_ENV", "production"),
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        # Get OTLP endpoint
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        
        if otlp_endpoint:
            # Use OTLP exporter (SigNoz, Jaeger, etc.)
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                
                exporter = OTLPSpanExporter(
                    endpoint=otlp_endpoint,
                    insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true",
                )
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(f"OpenTelemetry initialized with OTLP: {otlp_endpoint}")
                
            except ImportError:
                logger.warning("OTLP exporter not available, trying HTTP")
                try:
                    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                    
                    exporter = OTLPSpanExporter(
                        endpoint=otlp_endpoint,
                    )
                    provider.add_span_processor(BatchSpanProcessor(exporter))
                    logger.info(f"OpenTelemetry initialized with OTLP HTTP: {otlp_endpoint}")
                except ImportError:
                    logger.warning("No OTLP exporter available")
        
        # Add console exporter for development
        if os.getenv("OTEL_CONSOLE_EXPORTER", "false").lower() == "true":
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
            
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            logger.info("Console exporter enabled")
        
        # Instrument FastAPI
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            
            # Will be applied when app is created
            logger.info("FastAPI instrumentation ready")
        except ImportError:
            logger.warning("FastAPI instrumentation not available")
        
        # Instrument httpx
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumentation enabled")
        except ImportError:
            logger.warning("HTTPX instrumentation not available")
        
        # Instrument requests
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
            
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")
        except ImportError:
            logger.warning("Requests instrumentation not available")
        
        logger.info(f"Telemetry initialized for service: {service_name}")
        
    except ImportError as e:
        logger.warning(f"OpenTelemetry not available: {e}")
    except Exception as e:
        logger.warning(f"Failed to initialize telemetry: {e}")


def get_tracer(name: str = "open-notebook"):
    """Get a tracer instance."""
    from opentelemetry import trace
    return trace.get_tracer(name)


# =============================================================================
# Environment Variables
# =============================================================================

"""
OTEL_ENABLED=true/false
OTEL_SERVICE_NAME=open-notebook
OTEL_SERVICE_VERSION=1.0.0
OTEL_ENV=production
OTEL_CONSOLE_EXPORTER=true/false

# SigNoz/OTLP
OTEL_EXPORTER_OTLP_ENDPOINT=http://signoz:4317
OTEL_EXPORTER_OTLP_INSECURE=true

# Alternative: Jaeger
# OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14250
"""


__all__ = ["init_telemetry", "get_tracer"]