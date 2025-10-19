from __future__ import annotations

import asyncio

import pytest

from hex_commerce_service.app.application.errors import CircuitOpenError, PermanentExternalError, TransientExternalError
from hex_commerce_service.app.application.ports.payments import PaymentGateway
from hex_commerce_service.app.adapters.outbound.payment.fake import FakePaymentGateway, RetryPolicy, CircuitBreaker
from hex_commerce_service.app.domain.value_objects import Money, OrderId


pytestmark = pytest.mark.asyncio


async def test_payment_retry_and_idempotency() -> None:
    gw: PaymentGateway = FakePaymentGateway(
        retry=RetryPolicy(max_attempts=3, base_backoff=0.01, max_backoff=0.02, jitter=0.0),
        breaker=CircuitBreaker(failure_threshold=5, reset_timeout=0.05),
        transient_failures_before_success=2,  # first 2 attempts fail -> third succeeds
    )
    order_id = OrderId.new()
    res = await gw.charge(order_id, Money.from_major(10, "USD"), card_token="tok_visa", idempotency_key="k1", timeout_seconds=0.2)
    assert res.order_id == order_id
    # idempotent second call
    res2 = await gw.charge(order_id, Money.from_major(10, "USD"), card_token="tok_visa", idempotency_key="k1", timeout_seconds=0.2)
    assert res2.charge_id == res.charge_id


async def test_payment_permanent_error_no_retry() -> None:
    gw = FakePaymentGateway(
        retry=RetryPolicy(max_attempts=5, base_backoff=0.01, max_backoff=0.02, jitter=0.0),
        breaker=CircuitBreaker(failure_threshold=3, reset_timeout=0.05),
        permanent_error=True,
    )
    with pytest.raises(PermanentExternalError):
        await gw.charge(OrderId.new(), Money.from_major(1, "USD"), "tok_bad", "k2", timeout_seconds=0.1)
    # should not retry many times when permanent
    assert gw.calls == 1


async def test_payment_timeout_and_circuit_breaker_open_and_recovery() -> None:
    gw = FakePaymentGateway(
        retry=RetryPolicy(max_attempts=2, base_backoff=0.01, max_backoff=0.02, jitter=0.0),
        breaker=CircuitBreaker(failure_threshold=2, reset_timeout=0.1),
    )
    # make timeout by setting latency larger than timeout
    gw.network_latency_seconds = 0.2

    # 2 failures -> circuit opens
    with pytest.raises(TransientExternalError):
        await gw.charge(OrderId.new(), Money.from_major(1, "USD"), "tok", "k3", timeout_seconds=0.05)
    with pytest.raises(TransientExternalError):
        await gw.charge(OrderId.new(), Money.from_major(1, "USD"), "tok", "k4", timeout_seconds=0.05)

    assert gw.breaker.state == "open"

    # short-circuited
    with pytest.raises(CircuitOpenError):
        await gw.charge(OrderId.new(), Money.from_major(1, "USD"), "tok", "k5", timeout_seconds=0.05)

    # after reset_timeout, allow probe; set to succeed
    await asyncio.sleep(0.12)
    gw.network_latency_seconds = 0.01
    res = await gw.charge(OrderId.new(), Money.from_major(2, "USD"), "tok", "k6", timeout_seconds=0.2)
    assert res.amount.amount == Money.from_major(2, "USD").amount
    # breaker should be closed after success
    assert gw.breaker.state == "closed"
