import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def _get_traces_endpoint() -> str | None:
    traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    if traces_endpoint:
        return traces_endpoint

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return None

    endpoint = endpoint.rstrip("/")
    if endpoint.endswith("/v1/traces"):
        return endpoint
    return f"{endpoint}/v1/traces"


def _get_otlp_headers() -> dict[str, str] | None:
    headers_raw = (
        os.getenv("OTEL_EXPORTER_OTLP_TRACES_HEADERS")
        or os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    )
    if not headers_raw:
        return None

    headers = {}
    for item in headers_raw.split(","):
        if "=" not in item:
            raise ValueError("Invalid OTLP header: expected key=value")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError("Invalid OTLP header: key and value must not be empty")
        headers[key] = value
    return headers


def setup_telemetry(engine=None, *, service_version: str) -> TracerProvider:
    provider = trace.get_tracer_provider()

    if isinstance(provider, TracerProvider):
        if engine is not None and not SQLAlchemyInstrumentor().is_instrumented_by_opentelemetry:
            SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)
        return provider

    #configurar resource
    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "inventory-api"),
        "service.version": service_version,
        "deployment.environment": os.getenv("ENVIRONMENT", "production"),
    })

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    endpoint = _get_traces_endpoint()
    if endpoint:
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=_get_otlp_headers(),
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))

    if engine is not None and not SQLAlchemyInstrumentor().is_instrumented_by_opentelemetry:
        SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)

    return provider


def instrument_app(app: FastAPI) -> None:
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,metrics",
    )