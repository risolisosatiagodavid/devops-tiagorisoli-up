import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_telemetry(engine=None) -> TracerProvider:
    provider = trace.get_tracer_provider()

    if not isinstance(provider, TracerProvider):
        resource = Resource.create({
            "service.name": os.getenv("OTEL_SERVICE_NAME", "inventory-api"),
            "service.version": os.getenv("APP_VERSION", "0.1.0"),
            "deployment.environment": os.getenv("ENVIRONMENT", "production"),
        })
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

    endpoint = (
        os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
        or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    )

    if endpoint and not getattr(provider, "_otel_exporter_configured", False):
        if not endpoint.endswith("/v1/traces"):
            endpoint = f"{endpoint.rstrip('/')}/v1/traces"

        headers_raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        headers = {}
        if headers_raw:
            for item in headers_raw.split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    headers[key.strip()] = value.strip()

        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=headers or None,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        provider._otel_exporter_configured = True

    if engine is not None and not getattr(engine, "_otel_sqlalchemy_instrumented", False):
        SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)
        setattr(engine, "_otel_sqlalchemy_instrumented", True)

    return provider


def instrument_app(app):
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,metrics",
    )