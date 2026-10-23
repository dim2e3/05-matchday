# ADR-002: Transactional outbox for at-most-once notifications

**Status:** accepted · 2026-10-23

## Context
The worker detects game transitions by comparing ESPN state with a stored snapshot. Restarts,
overlapping cycles or a replayed transition must never send a fan the same "Final" twice, and
a Telegram outage must not lose messages.

## Decision
- Snapshot update and notification rows are written in one transaction.
- `notification` has `UNIQUE(user_id, game_id, kind)`; each insert runs in a savepoint and a
  unique violation is treated as "already enqueued" (dialect-neutral, no `ON CONFLICT`).
- A separate sender claims `pending` rows (`FOR UPDATE SKIP LOCKED` on Postgres), retries
  with backoff (10 s, 60 s) and marks `failed` after 3 attempts.
- No snapshot, or a snapshot older than 6 h → store state only, never notify (no back-fill).

## Consequences
- At most one message per (fan, game, kind), proven by `test_s5_enqueue_is_idempotent_across_restarts`.
- A crash between `sendMessage` and the status update can still re-send once (at-least-once at
  the very last step); accepted for this scope.
- Delivery state is visible to fans (Notifications tab) and to operators (metrics, alert).
