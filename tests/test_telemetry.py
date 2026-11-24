import pytest

from app.core.telemetry import build_resource, resolve_otlp_signal_config


@pytest.fixture(autouse=True)
def clear_telemetry_env(monkeypatch):
    for var in (
        "ENVIRONMENT",
        "APP_ENV",
        "OTEL_SERVICE_NAME",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
        "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
        "OTEL_EXPORTER_OTLP_HEADERS",
        "OTEL_EXPORTER_OTLP_TRACES_HEADERS",
        "OTEL_EXPORTER_OTLP_METRICS_HEADERS",
        "OTEL_EXPORTER_OTLP_LOGS_HEADERS",
    ):
        monkeypatch.delenv(var, raising=False)


def test_resolve_returns_no_endpoint_without_env():
    for signal in ("traces", "metrics", "logs"):
        cfg = resolve_otlp_signal_config(signal)
        assert cfg.endpoint is None
        assert cfg.headers == {}


@pytest.mark.parametrize(
    ("signal", "raw_endpoint", "expected"),
    [
        ("traces", "https://otlp.example", "https://otlp.example/v1/traces"),
        ("traces", "https://otlp.example/v1/traces", "https://otlp.example/v1/traces"),
        ("metrics", "https://otlp.example/", "https://otlp.example/v1/metrics"),
        ("logs", "https://otlp.example", "https://otlp.example/v1/logs"),
    ],
)
def test_generic_endpoint_is_normalized_per_signal(monkeypatch, signal, raw_endpoint, expected):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", raw_endpoint)

    assert resolve_otlp_signal_config(signal).endpoint == expected


def test_signal_specific_endpoint_overrides_generic(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://otlp.generic.example")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", "https://logs.example/v1/logs")

    assert resolve_otlp_signal_config("traces").endpoint == "https://otlp.generic.example/v1/traces"
    assert resolve_otlp_signal_config("logs").endpoint == "https://logs.example/v1/logs"


def test_otlp_headers_merge_and_preserve_equals_in_values(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "Authorization=Basic dXNlcjpwYXNz==,x-custom=a=b")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_HEADERS", "compute_stats=true")

    assert resolve_otlp_signal_config("traces").headers == {
        "Authorization": "Basic dXNlcjpwYXNz==",
        "x-custom": "a=b",
        "compute_stats": "true",
    }
    assert resolve_otlp_signal_config("logs").headers == {
        "Authorization": "Basic dXNlcjpwYXNz==",
        "x-custom": "a=b",
    }


def test_invalid_otlp_header_is_reported(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "malformed-header-without-equals")

    with pytest.raises(ValueError, match="Invalid OTLP header entry"):
        resolve_otlp_signal_config("traces")


def test_build_resource_uses_standard_otel_env(monkeypatch):
    monkeypatch.setenv("OTEL_SERVICE_NAME", "inventory-prod")
    monkeypatch.setenv("ENVIRONMENT", "staging")

    resource = build_resource("1.2.3")
    attrs = dict(resource.attributes)
    assert attrs["service.name"] == "inventory-prod"
    assert attrs["service.version"] == "1.2.3"
    assert attrs["deployment.environment"] == "staging"
    assert attrs["deployment.environment.name"] == "staging"
