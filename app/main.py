import json
import logging
from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(title="DevOps Portfolio", docs_url=None, redoc_url=None, openapi_url=None)
logger = logging.getLogger("uvicorn.error")
requests = Counter("portfolio_http_requests", "Application requests", ["status_class"])
duration = Histogram("portfolio_http_request_duration_seconds", "Request duration")
for status_class in ("2xx", "3xx", "4xx", "5xx"):
    requests.labels(status_class=status_class)

internal_paths = {"/livez", "/readyz", "/metrics"}


@app.middleware("http")
async def observe(request: Request, call_next):
    if request.url.path in internal_paths:
        return await call_next(request)

    started = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        elapsed = perf_counter() - started
        requests.labels(status_class=f"{status // 100}xx").inc()
        duration.observe(elapsed)
        logger.info(json.dumps({
            "event": "http_request",
            "status": status,
            "duration_ms": round(elapsed * 1000, 2),
        }))


@app.get("/")
def home():
    return {"service": "portfolio-api"}


@app.get("/livez")
@app.get("/readyz")
def health():
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
