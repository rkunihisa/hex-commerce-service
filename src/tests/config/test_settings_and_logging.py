from __future__ import annotations

import json
import os

import pytest
from httpx import AsyncClient

from hex_commerce_service.app.adapters.inbound.api.app import create_app
from hex_commerce_service.app.config.settings import get_settings


pytestmark = pytest.mark.asyncio


def test_settings_load_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear singleton cache
    get_settings.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.setenv("APP_NAME", "hexapp-test")
    monkeypatch.setenv("ENV", "staging")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("JWT_SECRET", "s3cr3t")
    s = get_settings()
    assert s.app_name == "hexapp-test"
    assert s.env == "staging"
    assert s.log_level == "DEBUG"
    assert s.jwt_secret == "s3cr3t"


async def test_json_logs_contain_request_and_correlation_ids(caplog: pytest.LogCaptureFixture) -> None:
    # Ensure JSON logs are enabled
    get_settings.cache_clear()  # type: ignore[attr-defined]
    os.environ["LOG_JSON"] = "1"
    os.environ["LOG_LEVEL"] = "INFO"

    app = create_app()
    caplog.clear()
    caplog.set_level("INFO")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Provide incoming IDs to verify propagation
        headers = {"x-request-id": "req-123", "x-correlation-id": "corr-xyz"}
        r = await ac.get("/health", headers=headers)
        assert r.status_code == 200
        # Response should echo headers
        assert r.headers["x-request-id"] == "req-123"
        assert r.headers["x-correlation-id"] == "corr-xyz"

    # Collect structlog JSON messages
    json_logs = []
    for rec in caplog.records:
        # Each record.message is a JSON string as configured by JSONRenderer
        try:
            obj = json.loads(rec.message)
            json_logs.append(obj)
        except Exception:
            continue

    # Expect at least: request_started, health_checked, request_finished
    names = {j.get("event") for j in json_logs}
    assert {"request_started", "health_checked", "request_finished"}.issubset(names)

    # All logs in this request share same IDs
    req_ids = {j.get("request_id") for j in json_logs if j.get("event") in {"request_started", "request_finished", "health_checked"}}
    corr_ids = {j.get("correlation_id") for j in json_logs if j.get("event") in {"request_started", "request_finished", "health_checked"}}
    assert req_ids == {"req-123"}
    assert corr_ids == {"corr-xyz"}

    # Each log has service and ts
    for j in json_logs:
        assert "service" in j
        assert "ts" in j
