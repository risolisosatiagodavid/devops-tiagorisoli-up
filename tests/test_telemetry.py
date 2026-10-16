import pytest

from app.core.telemetry import _get_otlp_headers, _get_traces_endpoint


def test_traces_endpoint_takes_precedence(monkeypatch):
    monkeypatch.setenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "https://traces.example/v1/traces",
    )
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://generic.example/otlp")

    assert _get_traces_endpoint() == "https://traces.example/v1/traces"


@pytest.mark.parametrize(
    ("endpoint", "expected"),
    [
        ("https://otlp.example/otlp", "https://otlp.example/otlp/v1/traces"),
        (
            "https://otlp.example/otlp/v1/traces",
            "https://otlp.example/otlp/v1/traces",
        ),
    ],
)
def test_generic_endpoint_is_normalized(monkeypatch, endpoint, expected):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", raising=False)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", endpoint)

    assert _get_traces_endpoint() == expected


def test_otlp_headers_preserve_equals_in_values(monkeypatch):
    monkeypatch.setenv(
        "OTEL_EXPORTER_OTLP_HEADERS",
        "Authorization=Basic dXNlcjp0b2tlbg==",
    )

    assert _get_otlp_headers() == {
        "Authorization": "Basic dXNlcjp0b2tlbg==",
    }


def test_trace_headers_take_precedence(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "Authorization=generic")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_HEADERS", "Authorization=traces")

    assert _get_otlp_headers() == {"Authorization": "traces"}


def test_invalid_otlp_header_is_reported(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "invalid-header")

    with pytest.raises(ValueError, match="expected key=value"):
        _get_otlp_headers()
