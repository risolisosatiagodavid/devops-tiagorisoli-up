import logging
from time import perf_counter
from typing import Any

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from starlette.responses import Response

logger = logging.getLogger("inventory_api")
REGISTRY = CollectorRegistry()

HTTP_REQUESTS = Counter(
    "inventory_http_requests",
    "Total HTTP requests handled by the API.",
    labelnames=("method", "route", "status"),
    registry=REGISTRY,
)
HTTP_REQUEST_DURATION = Histogram(
    "inventory_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("method", "route"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    registry=REGISTRY,
)


class PrometheusMetricsMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        record_metrics = not self._is_excluded(scope["path"])
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
            logger.info(
                "HTTP request completed",
                extra={
                    "path": scope["path"],
                    "status_code": status_code,
                    "method": method,
                    "duration_seconds": duration,
                },
            )
            if record_metrics:
                HTTP_REQUESTS.labels(method, route_path, str(status_code)).inc()
                HTTP_REQUEST_DURATION.labels(method, route_path).observe(duration)

    @staticmethod
    def _is_excluded(path: str) -> bool:
        return (
            path == "/metrics"
            or path == "/healthz"
            or path == "/health"
            or path.startswith("/static/")
        )


def metrics_response() -> Response:
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
