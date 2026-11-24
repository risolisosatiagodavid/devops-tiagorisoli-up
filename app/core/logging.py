from datetime import UTC, datetime
import json
import logging
import logging.config
from time import perf_counter
from typing import Any

from opentelemetry import metrics, trace

logger = logging.getLogger("inventory_api")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "path": getattr(record, "path", None),
            "status_code": getattr(record, "status_code", None),
            "method": getattr(record, "method", None),
            "duration_seconds": getattr(record, "duration_seconds", None),
            "trace_id": getattr(record, "trace_id", None),
            "span_id": getattr(record, "span_id", None),
        }
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, ensure_ascii=False)


class RequestLoggingMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app
        meter = metrics.get_meter("inventory_api")
        self._http_requests = meter.create_counter(
            name="inventory.http.requests",
            description="Total HTTP requests handled by the API.",
            unit="{request}",
        )
        self._http_request_duration = meter.create_histogram(
            name="inventory.http.request.duration",
            description="HTTP request duration in seconds.",
            unit="s",
        )

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        record_metrics = not self._is_excluded_from_metrics(scope["path"])
        start_time = perf_counter()
        status_code = 500

        async def record_status(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, record_status)
        finally:
            route = scope.get("route")
            route_path = getattr(route, "path", "unmatched")
            method = scope["method"]
            duration = perf_counter() - start_time
            span_context = trace.get_current_span().get_span_context()
            logger.info(
                "HTTP request completed",
                extra={
                    "path": scope["path"],
                    "status_code": status_code,
                    "method": method,
                    "duration_seconds": duration,
                    "trace_id": f"{span_context.trace_id:032x}" if span_context.is_valid else None,
                    "span_id": f"{span_context.span_id:016x}" if span_context.is_valid else None,
                },
            )
            if record_metrics:
                metric_attributes = {
                    "http.request.method": method,
                    "http.route": route_path,
                    "http.response.status_code": status_code,
                }
                self._http_requests.add(1, metric_attributes)
                self._http_request_duration.record(duration, metric_attributes)

    @staticmethod
    def _is_excluded_from_metrics(path: str) -> bool:
        return (
            path == "/healthz"
            or path == "/health"
            or path.startswith("/static/")
        )


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "json",
                }
            },
            "root": {"level": "INFO", "handlers": ["console"]},
            "loggers": {
                "uvicorn": {"handlers": [], "propagate": True},
                "uvicorn.access": {"handlers": [], "propagate": False},
            },
        }
    )
