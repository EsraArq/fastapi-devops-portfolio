from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

from app.main import app

client = TestClient(app)


def request_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    return {
        (sample.name, tuple(sorted(sample.labels.items()))): sample.value
        for family in text_string_to_metric_families(response.text)
        for sample in family.samples
        if sample.name in (
            "portfolio_http_requests_total",
            "portfolio_http_request_duration_seconds_count",
            "portfolio_http_request_duration_seconds_bucket",
        )
    }


def test_service_and_probes():
    assert client.get("/").json() == {"service": "portfolio-api"}
    for path in ("/livez", "/readyz"):
        assert client.get(path).json() == {"status": "ok"}


def test_metrics_capture_success_and_missing_route():
    for path, status, status_class in (("/", 200, "2xx"), ("/missing", 404, "4xx")):
        before = request_metrics()
        assert client.get(path).status_code == status
        after = request_metrics()

        for label in ("2xx", "3xx", "4xx", "5xx"):
            key = ("portfolio_http_requests_total", (("status_class", label),))
            assert after[key] == before[key] + int(label == status_class)

        count = ("portfolio_http_request_duration_seconds_count", ())
        assert after[count] == before[count] + 1
        bucket = ("portfolio_http_request_duration_seconds_bucket", (("le", "+Inf"),))
        assert after[bucket] == before[bucket] + 1


def test_health_probes_and_metrics_scrapes_do_not_count():
    baseline = request_metrics()
    for path in ("/livez", "/readyz"):
        assert client.get(path).status_code == 200
        assert request_metrics() == baseline
    assert request_metrics() == baseline
