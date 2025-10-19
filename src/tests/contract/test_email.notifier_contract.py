from __future__ import annotations

import asyncio

import pytest

from hex_commerce_service.app.adapters.outbound.email.fake import CircuitBreaker, FakeEmailNotifier, RetryPolicy
from hex_commerce_service.app.application.errors import CircuitOpenError, PermanentExternalError, TransientExternalError
from hex_commerce_service.app.application.ports.email import EmailNotifier
from hex_commerce_service.app.domain.value_objects import Email, OrderId


pytestmark = pytest.mark.asyncio


async def test_email_retry_and_idempotency() -> None:
    notifier: EmailNotifier = FakeEmailNotifier(
        retry=RetryPolicy(max_attempts=3, base_backoff=0.01, max_backoff=0.02, jitter=0.0),
        breaker=CircuitBreaker(failure_threshold=3, reset_timeout=0.05),
        transient_failures_before_success=2,
    )
    to = Email("user@example.com")
    oid = OrderId.new()
    d1 = await notifier.send_order_confirmation(to, oid)
    d2 = await notifier.send_order_confirmation(to, oid)
    assert d1 == d2  # idempotent


async def test_email_permanent_error_no_retry() -> None:
    notifier = FakeEmailNotifier(permanent_error=True)
    with pytest.raises(PermanentExternalError):
        await notifier.send_order_confirmation(Email("user@example.com"), OrderId.new())
    assert notifier.calls == 1


async def test_email_circuit_breaker_open_and_recovery() -> None:
    notifier = FakeEmailNotifier(
        retry=RetryPolicy(max_attempts=2, base_backoff=0.01, max_backoff=0.02, jitter=0.0),
        breaker=CircuitBreaker(failure_threshold=2, reset_timeout=0.1),
    )
    notifier.transient_failures_before_success = 10  # keep failing

    with pytest.raises(TransientExternalError):
        await notifier.send_order_confirmation(Email("user@example.com"), OrderId.new())
    with pytest.raises(TransientExternalError):
        await notifier.send_order_confirmation(Email("user@example.com"), OrderId.new())

    assert notifier.breaker._state == "open"  # type: ignore[attr-defined]

    with pytest.raises(CircuitOpenError):
        await notifier.send_order_confirmation(Email("user@example.com"), OrderId.new())

    # Cooldown
    await asyncio.sleep(0.12)
    # allow success
    notifier.transient_failures_before_success = 0
    d = await notifier.send_order_confirmation(Email("user@example.com"), OrderId.new())
    assert isinstance(d, str)
