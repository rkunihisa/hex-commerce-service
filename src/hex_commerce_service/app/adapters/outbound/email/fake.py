from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass, field
from typing import Literal

from hex_commerce_service.app.application.errors import CircuitOpenError, PermanentExternalError, TransientExternalError
from hex_commerce_service.app.application.ports.email import EmailNotifier
from hex_commerce_service.app.domain.value_objects import Email, OrderId


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_backoff: float = 0.05
    max_backoff: float = 0.5
    jitter: float = 0.02

    async def wait(self, attempt: int) -> None:
        delay = min(self.base_backoff * (2 ** (attempt - 1)), self.max_backoff)
        delay += secrets.SystemRandom().uniform(-self.jitter, self.jitter)
        await asyncio.sleep(max(0.0, delay))


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 3
    reset_timeout: float = 1.0

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
                self._state = "half_open"
                self._probe_in_flight = True
                return True
            return False
        if self._state == "half_open":
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


@dataclass(slots=True)
class FakeEmailNotifier(EmailNotifier):
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    network_latency_seconds: float = 0.01

    # behavior controls
    transient_failures_before_success: int = 0
    permanent_error: bool = False

    sent: list[tuple[str, str, str]] = field(default_factory=list)  # (template, to, subject)
    _idempo_store: dict[str, str] = field(default_factory=dict)  # idempotency_key -> delivery_id
    _calls: int = 0

    async def send_order_confirmation(self, to: Email, order_id: OrderId) -> str:
        key = f"order_confirmation:{order_id}:{to.value}"
        return await self._send_with_policy("order_confirmation", to, key)

    async def send_order_allocated(self, to: Email, order_id: OrderId, location: str) -> str:
        key = f"order_allocated:{order_id}:{to.value}:{location}"
        return await self._send_with_policy("order_allocated", to, key)

    async def _send_with_policy(self, template: str, to: Email, key: str) -> str:
        if key in self._idempo_store:
            return self._idempo_store[key]

        if not self.breaker.allow_request():
            raise CircuitOpenError("email circuit open")

        attempt = 0
        last_exc: Exception | None = None
        while attempt < self.retry.max_attempts:
            attempt += 1
            try:
                self._calls += 1
                delivery_id = await self._simulate_send(template, to)
                self.breaker.on_success()
                self.sent.append((template, to.value, template))
                self._idempo_store[key] = delivery_id
            except PermanentExternalError as exc:
                self.breaker.on_failure()
                raise exc from exc
            except TransientExternalError as exc:
                last_exc = exc
                self.breaker.on_failure()
                if attempt >= self.retry.max_attempts:
                    break
                await self.retry.wait(attempt)
            except Exception as exc:
                last_exc = exc
                self.breaker.on_failure()
                if attempt >= self.retry.max_attempts:
                    break
                await self.retry.wait(attempt)
            else:
                return delivery_id

        assert last_exc is not None
        raise last_exc

    async def _simulate_send(self, template: str, to: Email) -> str:
        await asyncio.sleep(self.network_latency_seconds)
        if self.permanent_error:
            raise PermanentExternalError("smtp 550 invalid recipient")
        if self.transient_failures_before_success > 0:
            self.transient_failures_before_success -= 1
            raise TransientExternalError("smtp 451 try again later")

        return f"em_{hash((template, to.value, self._calls)) & 0xFFFF:x}"

    @property
    def calls(self) -> int:
        return self._calls
