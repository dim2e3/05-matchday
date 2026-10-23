# MatchDay Alerts — Product Specification

## Problem

Fans who follow a few teams across leagues (NFL, NBA, NHL, MLB) must open a sports app or
site and dig through every league's scoreboard to learn whether *their* team is playing,
whether the game has started, and how it ended. Generic sports apps push far more than the
fan wants, need an account, and bury the one score that matters.

**MatchDay Alerts** shows only the games of the teams you follow, live, on one page, and
sends a Telegram message when a followed team's game starts and when it ends with the final
score. No sign-up: open the page, follow teams, connect Telegram with one tap.

## Users

- **Fan** — follows 1–10 teams, checks scores on a phone, wants a ping at kickoff and at
  the final whistle, nothing else.
- **Operator** (the project owner) — runs the service on one EC2 host, needs to know when
  fans stop getting scores or notifications, and wants an agent to fix routine breakage
  (ESPN schema drift) without waking up.

## Out of scope

Accounts with passwords, play-by-play, odds, push notifications other than Telegram,
leagues beyond the four above, LLM-generated content.

## Glossary

- **Game state** — ESPN `status.type.state`: `pre` (scheduled), `in` (live), `post` (final).
- **Transition** — a change of a game's state between two worker polls.
- **Outbox** — the `notification` table; one row per (user, game, kind), sent at most once.

## User stories and acceptance criteria

Each story is tracked as a GitHub issue (template `.github/ISSUE_TEMPLATE/story.yml`). Issue
IDs are filled in once the issues exist.

### S1 Anonymous identity
As a fan I can use the app without signing up.
- [ ] Given no `md_uid` cookie, when I call any `/api/*` endpoint, then a user row is created
      and an HttpOnly, SameSite=Lax, Secure (in prod) cookie `md_uid` with a random 128-bit id
      is set.
- [ ] Given a valid cookie, the same user is reused; an unknown cookie value creates a new user.
- [ ] The cookie value never appears in logs, traces or metrics.

### S2 Browse and follow teams
As a fan I can find my teams and follow them.
- [ ] `GET /api/teams/{league}` returns the league's teams (id, name, abbreviation, logo),
      cached for 24 h; unknown league → 422.
- [ ] `POST /api/follows` `{league, team_id}` follows a team; repeating it returns 200 and no
      duplicate row (idempotent).
- [ ] `DELETE /api/follows/{league}/{team_id}` returns 204 whether or not it existed.
- [ ] `GET /api/follows` lists only the current user's follows.
- [ ] UI: team picker per league with a follow toggle; followed teams show first.

### S3 My Games (key journey)
As a fan I see today's games of the teams I follow, live.
- [ ] `GET /api/my-games` returns games (any league) where a competitor is followed by the
      current user, sorted by start time, each tagged with its league.
- [ ] With no follows it returns `{"games": [], "stale": false}` and the UI shows
      "Follow a team to see their games".
- [ ] When ESPN fails and cached data exists, it returns the cached games with `stale: true`
      and the UI shows a "scores may be out of date" banner.
- [ ] When ESPN fails or returns unparseable data for a league with followed teams and no
      cache exists, it returns 502 `{"error": "upstream_unavailable"}`.
- [ ] The UI polls every 15 s, pauses while the tab is hidden, and updates without flicker.

### S4 Connect Telegram
As a fan I link my Telegram chat with one tap.
- [ ] `POST /api/telegram/link` returns `{url}` = `https://t.me/<bot>?start=<token>`, token
      single-use, expires in 15 min.
- [ ] `POST /api/telegram/webhook` rejects requests without the correct
      `X-Telegram-Bot-Api-Secret-Token` header (401).
- [ ] `/start <token>` from Telegram links the chat to the user and replies "Connected";
      expired/used token replies "Link expired, press Connect again".
- [ ] `/stop` unlinks; no further messages are sent to that chat.
- [ ] `GET /api/me` shows `telegram_connected: true|false`; the UI shows Connect/Disconnect.

### S5 Game notifications
As a fan I get a Telegram message at kickoff and at the final.
- [ ] The worker polls ESPN every 30 s, only for leagues with at least one follow.
- [ ] On `pre → in` it enqueues `kickoff` for every connected user following either team:
      "🟢 Kickoff: BOS @ NYR (NHL)".
- [ ] On `in → post` it enqueues `final`: "🏁 Final: BOS 3 – 2 NYR (NHL)".
- [ ] A game first seen already `post` does not notify (no back-fill after downtime > 6 h).
- [ ] Each (user, game, kind) is delivered at most once, even across worker restarts.
- [ ] Telegram failures retry with backoff (3 attempts); then status `failed`.

### S6 Notification history
- [ ] `GET /api/notifications` returns the current user's last 50 notifications with
      kind, text, status (`pending|sent|failed`) and timestamps.
- [ ] UI shows them in a "Notifications" tab.

### S7 Operability (operator stories)
- [ ] `GET /api/health` (liveness) and `GET /api/ready` (DB reachable) exist; `GET /api/version`
      returns the deployed git sha.
- [ ] The key journey emits correlated metrics, traces and logs (see `docs/observability.md`).
- [ ] An alert fires when fans stop getting live scores or notifications (see `docs/runbook.md`).
- [ ] The on-call agent opens a fix PR for an ESPN schema change within one alert cycle.

### S8 Daily digest (stretch)
- [ ] At 09:00 (UTC, configurable) each connected user with games today gets one message
      listing them.

## Non-functional requirements

- p95 `GET /api/my-games` < 500 ms on a cache hit, < 3 s on a miss.
- ESPN is unofficial and unreliable: every call has a 5 s timeout; one malformed event never
  breaks a whole response.
- No customer data (cookie ids, chat ids, Telegram usernames, link tokens) and no secrets in
  telemetry.
