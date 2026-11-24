from dataclasses import dataclass
import logging
import os

from fastapi import FastAPI
from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


@dataclass(frozen=True)
class OtlpSignalConfig:
    endpoint: str | None
    headers: dict[str, str]


@dataclass
class TelemetryRuntime:
    tracer_provider: TracerProvider
    meter_provider: MeterProvider | None = None
    logger_provider: LoggerProvider | None = None
    log_handler: LoggingHandler | None = None

    def shutdown(self) -> None:
        if self.log_handler is not None:
            logging.getLogger().removeHandler(self.log_handler)
            self.log_handler = None
        if self.logger_provider is not None:
            self.logger_provider.shutdown()
        if self.meter_provider is not None:
            self.meter_provider.shutdown()
        self.tracer_provider.shutdown()


def _parse_otlp_headers(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"Invalid OTLP header entry (expected key=value): {item!r}")
        key, value = item.split("=", 1)
        headers[key.strip()] = value.strip()
    return headers


def _normalize_signal_endpoint(endpoint: str, signal_path: str) -> str:
    cleaned = endpoint.strip().rstrip("/")
    if cleaned.endswith(signal_path):
        return cleaned
    return f"{cleaned}{signal_path}"


def resolve_otlp_signal_config(signal: str) -> OtlpSignalConfig:
    """Resolve vendor-agnostic OTLP HTTP endpoint and headers for 'traces', 'metrics', or 'logs'."""
    signal_upper = signal.upper()
    signal_path = f"/v1/{signal}"

    specific_endpoint = os.getenv(f"OTEL_EXPORTER_OTLP_{signal_upper}_ENDPOINT", "").strip()
    generic_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()

    endpoint: str | None = None
    if specific_endpoint:
        endpoint = _normalize_signal_endpoint(specific_endpoint, signal_path)
    elif generic_endpoint:
        endpoint = _normalize_signal_endpoint(generic_endpoint, signal_path)

    headers: dict[str, str] = {}
    generic_headers_raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    if generic_headers_raw:
        headers.update(_parse_otlp_headers(generic_headers_raw))

    specific_headers_raw = os.getenv(f"OTEL_EXPORTER_OTLP_{signal_upper}_HEADERS", "")
    if specific_headers_raw:
        headers.update(_parse_otlp_headers(specific_headers_raw))

    return OtlpSignalConfig(endpoint=endpoint, headers=headers)


def build_resource(service_version: str) -> Resource:
    service_name = os.getenv("OTEL_SERVICE_NAME") or "inventory-api"
    environment = os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "production"
    return Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": environment,
            "deployment.environment.name": environment,
        }
    )


def setup_telemetry(engine=None, *, service_version: str = "0.1.0") -> TelemetryRuntime:
    existing_provider = trace.get_tracer_provider()
    if isinstance(existing_provider, TracerProvider):
        if engine is not None and not SQLAlchemyInstrumentor().is_instrumented_by_opentelemetry:
            SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)
        return TelemetryRuntime(tracer_provider=existing_provider)

    resource = build_resource(service_version)

    # 1. Traces
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    traces_cfg = resolve_otlp_signal_config("traces")
    if traces_cfg.endpoint:
        span_exporter = OTLPSpanExporter(
            endpoint=traces_cfg.endpoint,
            headers=traces_cfg.headers or None,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

    # 2. Metrics (respects OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE natively)
    metrics_cfg = resolve_otlp_signal_config("metrics")
    metric_readers = []
    if metrics_cfg.endpoint:
        metric_exporter = OTLPMetricExporter(
            endpoint=metrics_cfg.endpoint,
            headers=metrics_cfg.headers or None,
        )
        export_interval_ms = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "30000"))
        metric_readers.append(
            PeriodicExportingMetricReader(
                metric_exporter,
                export_interval_millis=export_interval_ms,
            )
        )
    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)

    # 3. Logs (correlated with active trace_id / span_id)
    logger_provider: LoggerProvider | None = None
    log_handler: LoggingHandler | None = None
    logs_cfg = resolve_otlp_signal_config("logs")
    if logs_cfg.endpoint:
        logger_provider = LoggerProvider(resource=resource)
        _logs.set_logger_provider(logger_provider)
        log_exporter = OTLPLogExporter(
            endpoint=logs_cfg.endpoint,
            headers=logs_cfg.headers or None,
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        log_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        logging.getLogger().addHandler(log_handler)

    if engine is not None and not SQLAlchemyInstrumentor().is_instrumented_by_opentelemetry:
        SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)

    return TelemetryRuntime(
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
        logger_provider=logger_provider,
        log_handler=log_handler,
    )


def instrument_app(app: FastAPI) -> None:
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health",
    )
