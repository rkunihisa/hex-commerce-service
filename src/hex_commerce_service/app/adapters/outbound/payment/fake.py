from __future__ import annotations

import asyncio
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Literal

from hex_commerce_service.app.application.errors import CircuitOpenError, PermanentExternalError, TransientExternalError
from hex_commerce_service.app.application.ports.payments import PaymentGateway, PaymentResult
from hex_commerce_service.app.domain.value_objects import Money, OrderId


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_backoff: float = 0.1  # seconds
    max_backoff: float = 1.0
    jitter: float = 0.05  # +/- seconds

    async def wait(self, attempt: int) -> None:
        # exponential backoff with jitter
        delay = min(self.base_backoff * (2 ** (attempt - 1)), self.max_backoff)
        delay += secrets.SystemRandom().uniform(-self.jitter, self.jitter)
        await asyncio.sleep(max(0.0, delay))


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 5
    reset_timeout: float = 30.0  # seconds

    _state: Literal["closed", "open", "half_open"] = "closed"
    _failures: int = 0
    _opened_at: float | None = None
    _probe_in_flight: bool = False

    def allow_request(self) -> bool:
        if self._state == "closed":
            return True
        now = time.monotonic()
        if self._state == "open":
            assert self._opened_at is not None
            if (now - self._opened_at) >= self.reset_timeout:
                # allow one probe
                self._state = "half_open"
                self._probe_in_flight = True
                return True
            return False
        if self._state == "half_open":
            # only one probe at a time
            return not self._probe_in_flight
        return False

    def on_success(self) -> None:
        self._failures = 0
        self._probe_in_flight = False
        self._state = "closed"

    def on_failure(self) -> None:
        self._failures += 1
        self._probe_in_flight = False
        if self._failures >= self.failure_threshold:
            self._state = "open"
            self._opened_at = time.monotonic()

    @property
    def state(self) -> str:
        return self._state


@dataclass(slots=True)
class FakePaymentGateway(PaymentGateway):
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    breaker: CircuitBreaker = field(
        default_factory=lambda: CircuitBreaker(
            failure_threshold=int(os.getenv("PAYMENT_BREAKER_THRESHOLD", "3")),
            reset_timeout=float(os.getenv("PAYMENT_BREAKER_RESET", "1.0")),
        )
    )
    network_latency_seconds: float = 0.02

    # behavior controls (for tests)
    transient_failures_before_success: int = 0
    permanent_error: bool = False

    # internal state
    _calls: int = 0
    _idempo_store: dict[str, PaymentResult] = field(default_factory=dict)

    async def charge(
        self,
        order_id: OrderId,
        amount: Money,
        card_token: str,
        idempotency_key: str,
        timeout_seconds: float | None = None,
    ) -> PaymentResult:
        # Idempotent path first
        if idempotency_key in self._idempo_store:
            return self._idempo_store[idempotency_key]

        # Circuit breaker check
        if not self.breaker.allow_request():
            raise CircuitOpenError("payment circuit open")

        return await self._charge_with_retries(order_id, amount, card_token, idempotency_key, timeout_seconds)

    async def _charge_with_retries(
        self,
        order_id: OrderId,
        amount: Money,
        card_token: str,
        idempotency_key: str,
        timeout_seconds: float | None,
    ) -> PaymentResult:
        attempt = 0
        last_exc: Exception | None = None
        while attempt < self.retry.max_attempts:
            attempt += 1
            try:
                # Simulate network latency + timeout
                self._calls += 1
                result = await asyncio.wait_for(self._simulate_remote(order_id, amount, card_token), timeout=timeout_seconds)
                # Success -> store idempotent result, reset breaker
                self.breaker.on_success()
                self._idempo_store[idempotency_key] = result
            except PermanentExternalError as exc:
                # Do not retry
                self.breaker.on_failure()
                raise exc from exc
            except TimeoutError as exc:
                last_exc = exc
                self.breaker.on_failure()
                if attempt >= self.retry.max_attempts:
                    break
                await self.retry.wait(attempt)
            except Exception as exc:  # unknown errors treated as transient
                last_exc = exc
                self.breaker.on_failure()
                if attempt >= self.retry.max_attempts:
                    break
                await self.retry.wait(attempt)
            else:
                return result

        assert last_exc is not None
        if isinstance(last_exc, asyncio.TimeoutError):
            raise TransientExternalError("payment timeout") from last_exc
        raise last_exc

    async def _simulate_remote(self, order_id: OrderId, amount: Money) -> PaymentResult:
        # trivial latency
        await asyncio.sleep(self.network_latency_seconds)

        if self.permanent_error:
            raise PermanentExternalError("card declined")

        if self.transient_failures_before_success > 0:
            self.transient_failures_before_success -= 1
            raise TransientExternalError("temporary payment service error")

        charge_id = f"ch_{str(order_id)[:8]}_{self._calls}"
        return PaymentResult(charge_id=charge_id, order_id=order_id, amount=amount)

    @property
    def calls(self) -> int:
        return self._calls
