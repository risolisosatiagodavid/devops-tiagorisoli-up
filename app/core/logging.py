from datetime import UTC, datetime
import json
import logging
import logging.config
from time import perf_counter
from typing import Any

from opentelemetry import trace

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

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

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
