from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hex_commerce_service.app.application.message_bus import MessageBus
from hex_commerce_service.app.infra.outbox.repository import OutboxStore
from hex_commerce_service.app.infra.outbox.serializer import deserialize_event


@dataclass(slots=True)
class OutboxDispatcher:
    sessionmaker: async_sessionmaker[AsyncSession]
    owner: str
    bus: MessageBus
    batch_size: int = 50
    lease_seconds: int = 30
    max_attempts: int = 10

    delivered: list[object] = field(default_factory=list)

    async def run_once(self) -> int:
        async with self.sessionmaker() as session:
            store = OutboxStore(session)
            messages = await store.claim_batch(
                owner=self.owner, batch_size=self.batch_size, lease_seconds=self.lease_seconds
            )
            if not messages:
                return 0

            for msg in messages:
                event = deserialize_event(msg.payload)
                try:
                    before_errors = len(self.bus.errors)
                    self.bus.publish(event)
                    after_errors = len(self.bus.errors)
                    if after_errors > before_errors:
                        # last error belongs to this publish; mark failed
                        err = str(self.bus.errors[-1][1])
                        await store.mark_failed(
                            msg, err, backoff_seconds=min(60, 2 ** min(msg.attempt_count, 5))
                        )
                    else:
                        await store.mark_sent(msg)
                        self.delivered.append(event)
                except Exception as exc:
                    await store.mark_failed(
                        msg, str(exc), backoff_seconds=min(60, 2 ** min(msg.attempt_count, 5))
                    )
            await session.commit()
            return len(messages)

    async def run_forever(
        self, interval_seconds: float = 2.0, stop_event: asyncio.Event | None = None
    ) -> None:
        stop = stop_event or asyncio.Event()
        while not stop.is_set():
            try:
                n = await self.run_once()
            except Exception:
                n = 0
            await asyncio.sleep(interval_seconds if n == 0 else 0)
