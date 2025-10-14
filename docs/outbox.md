## Outbox 概要

- 目的: トランザクションに含めてイベントを永続化し、非同期で確実に配送する（at-least-once）。
- モデル: outbox_messages
  - 冪等性: (event_type, idempotency_key) の一意制約。
  - 配信制御: state(pending/sent)、attempt_count、last_error、available_at（バックオフ）、lock_owner/lock_until（ワーカー間排他）。
- ディスパッチ: SKIP LOCKED によるクレーム + 同期 MessageBus publish（失敗は記録して再送）。
- バックオフ: 失敗時に指数バックオフ（最小 1s, 最大 60s）。

## 切り替え戦略

- In-memory EventPublisher の代わりに、UseCase で DB UoW を用いる場合は OutboxStore.enqueue を use case トランザクション内で呼ぶ。
- 配送先が外部（Kafka/SQS 等）の場合は MessageBus の代わりに送信アダプタを注入し、deliver 関数で publish する。
