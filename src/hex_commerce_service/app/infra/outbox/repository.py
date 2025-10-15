from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from hex_commerce_service.app.infra.db.outbox_models import OutboxMessageModel
from hex_commerce_service.app.infra.outbox.serializer import (
    EventEnvelope,
    serialize_event,
)


def default_idempotency_key(event: object) -> str:
    env = serialize_event(event)
    t = env["type"]
    p = env["payload"]
    order_id = p.get("order_id", "")
    # event type + aggregate id を基本キーに
    return f"{t}:{order_id}"


@dataclass(slots=True)
class OutboxStore:
    session: AsyncSession

    async def enqueue(
        self,
        event: object,
        idempotency_key: str | None = None,
        aggregate_id: str | None = None,
        available_at: datetime | None = None,
    ) -> None:
        env: EventEnvelope = serialize_event(event)
        msg = OutboxMessageModel(
            event_type=env["type"],
            aggregate_id=aggregate_id or env["payload"].get("order_id"),
            idempotency_key=idempotency_key or default_idempotency_key(event),
            payload=env,
            state="pending",
            occurred_at=datetime.fromisoformat(env["occurred_at"]),
            available_at=available_at or datetime.now(tz=datetime.UTC),
            attempt_count=0,
        )
        # Unique constraint (event_type, idempotency_key) により重複を拒否
        self.session.add(msg)
        try:
            await self.session.flush()
        except Exception:
            # UniqueViolation等はここに飛ぶ。重複は黙って冪等に成功扱い。
            await self.session.rollback()
            # 再度実行に備え再開
            await self.session.begin()

    async def claim_batch(
        self, owner: str, batch_size: int = 50, lease_seconds: int = 30
    ) -> list[OutboxMessageModel]:
        now = datetime.now(tz=datetime.UTC)
        lease_until = now + timedelta(seconds=lease_seconds)
        async with self.session.begin():
            # ロックのかかっていない pending を取得
            stmt = (
                select(OutboxMessageModel)
                .where(
                    OutboxMessageModel.state == "pending",
                    OutboxMessageModel.available_at <= now,
                    (OutboxMessageModel.lock_until.is_(None))
                    | (OutboxMessageModel.lock_until < now),
                )
                .order_by(OutboxMessageModel.id.asc())
                .with_for_update(skip_locked=True)
                .limit(batch_size)
            )
            rows = (await self.session.execute(stmt)).scalars().all()
            # 取得できなければ空
            if not rows:
                return []
            # ロック情報を付与して確定
            for r in rows:
                r.lock_owner = owner
                r.lock_until = lease_until
            await self.session.flush()
        return list(rows)

    async def mark_sent(self, msg: OutboxMessageModel) -> None:
        msg.state = "sent"
        msg.dispatched_at = datetime.now(tz=datetime.UTC)
        msg.lock_owner = None
        msg.lock_until = None
        msg.last_error = None
        await self.session.flush()

    async def mark_failed(
        self, msg: OutboxMessageModel, error: str, backoff_seconds: int = 5
    ) -> None:
        msg.attempt_count += 1
        msg.last_error = error[:2000]
        msg.lock_owner = None
        msg.lock_until = None
        msg.available_at = datetime.now(tz=datetime.UTC) + timedelta(
            seconds=max(1, backoff_seconds)
        )
        await self.session.flush()
