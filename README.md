# Gamification Core

**Event-driven gamification engine** for quests, user progress, rule evaluation, and rewards. REST API only — no frontend. Built for trading and fintech platforms (e.g. “Complete 5 trades”, “Reach $10k volume”) and designed to be **pip-installable** for multi-tenant SaaS layers.

Part of the [Gamification](https://github.com/meetrakib/gamification-core) & [Mini Exchange]([https://github.com](https://github.com/meetrakib/mini-derivatives-exchange)) ecosystem: this repo is the core engine; optional [gamification-demo-ui]([https://github.com](https://github.com/meetrakib/gamification-demo-ui)) provides a minimal demo, and [mini-derivatives-exchange]([https://github.com](https://github.com/meetrakib/mini-exchange-ui)) can emit trade events here.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [System Design](#system-design)
- [API Documentation](#api-documentation)
- [Event-Driven Rules](#event-driven-rules)
- [Docker Setup](#docker-setup)
- [Local Development (no Docker)](#local-development-no-docker)
- [Install as Library](#install-as-library)
- [Testing](#testing)
- [Scaling & Future Work](#scaling--future-work)

---

## Features

- **Quest model**: slug, name, description, `quest_type` (repeated / one_shot), **rules** (JSON, e.g. `trade_count`, `volume`, `signup`), **reward** (JSON), schedule (start/end), `is_active`.
- **User progress**: per user per quest — `state` (not_started → in_progress → completed → reward_claimed), `progress_payload` (JSON), `completed_at`, `reward_claimed_at`.
- **Events**: `POST /api/v1/events` with `user_id`, `event_type`, `payload`. Engine loads active quests, runs rule evaluator, updates progress; completion is derived from rules (no cron).
- **Rule evaluator**: Pure domain — rule + current progress + event → new progress + `completed` flag. Built-in types: **trade_count**, **volume**, **signup**.
- **API**: Quests CRUD, list active quests, get user progress, post events, **claim reward** (idempotent). Optional seed creates a sample “Complete 5 Trades” quest when DB is empty.

---

## Architecture

High-level flow:

```
┌─────────────┐     POST /events      ┌──────────────────┐     ┌─────────────┐
│  Clients /  │ ───────────────────►  │  Gamification    │     │  PostgreSQL │
│  Exchange   │                       │  Core API        │◄───►│  (quests,   │
└─────────────┘                       │  (FastAPI)       │     │   progress) │
                                      └────────┬─────────┘     └─────────────┘
                                               │
                                      ┌────────▼─────────┐
                                      │  Events module   │
                                      │  → ProgressSvc   │
                                      │  → RuleEngine    │
                                      └──────────────────┘
```

**Modular monolith** (single deployable, clear module boundaries):

| Module   | Responsibility                          | Public interface / usage                    |
|----------|------------------------------------------|---------------------------------------------|
| **core** | Config, DB session, app bootstrap, seed | `Settings`, `get_db`, `seed_if_empty`       |
| **quests** | Quest CRUD, list active quests        | `QuestService.get_by_id`, `list_active`, `create`, `update` |
| **progress** | User progress, state transitions    | `ProgressService.get_or_create`, `get_for_user`, `record_event`, `claim_reward` |
| **rules** | Pure domain: evaluate rule + progress + event | `RuleEngine.evaluate(...)` → `(new_progress, completed)` |
| **events** | HTTP for `POST /events`               | Validates body, calls `ProgressService.record_event` |

Other code must not import a module’s internals; they use only the module’s public interface so that modules can be extracted to microservices later.

---

## System Design

### Why a modular monolith first?

- Single deployable reduces operational complexity (one DB, one app, one pipeline).
- Module boundaries and interfaces make it straightforward to extract services (e.g. progress, rules) to HTTP/gRPC later without rewriting business logic.
- Fits the “core engine” role: consumed by a multi-tenant SaaS API or by other backends (e.g. mini exchange) via events.

### Why PostgreSQL?

- Strong consistency for progress and rewards (no double-claim).
- JSONB for flexible `rules` and `progress_payload` without schema churn.
- Mature ecosystem (SQLAlchemy, Alembic) and path to read replicas for analytics.

### Why event-driven progress (no cron)?

- Progress is updated only when events arrive (`POST /events`). Completion is derived from rule evaluation, so there is no need for a periodic job to “check” progress.
- Keeps the engine stateless and easy to scale horizontally; only the DB holds state.

### Scaling strategy

- **Current**: Stateless API; horizontal scaling behind a load balancer; indexes on `(user_id, quest_id)` and `(quest_id, state)`; optional Redis cache for hot quests or rate limiting.
- **Later**: Read replica for heavy read paths (e.g. leaderboards); optional extraction of progress/rules into separate services with the same interfaces.

---

## API Documentation

- **OpenAPI (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs) when running locally.
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc).

Base path: `/api/v1`.

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/quests` | List active quests (optional `?quest_type=`) |
| `GET`  | `/quests/{quest_id}` | Get quest by ID |
| `POST` | `/quests` | Create quest |
| `PATCH`| `/quests/{quest_id}` | Update quest |
| `GET`  | `/users/{user_id}/progress` | Get all progress for user |
| `POST` | `/users/{user_id}/progress/{quest_id}/claim` | Claim reward (idempotent) |
| `POST` | `/events` | Submit event (`user_id`, `event_type`, `payload`) |

**Health**: `GET /health` → `{"status": "ok"}`.

---

## Event-Driven Rules

Rules are stored in quest `rules` JSON with a `type` and parameters. The **RuleEngine** is pure domain logic:

- **Input**: `rule_type`, `rule_params`, `current_progress`, `event_type`, `event_payload`.
- **Output**: `RuleResult(new_progress, completed)`.

| Rule type     | Params        | Event types | Progress fields   | Completed when        |
|---------------|---------------|------------|--------------------|------------------------|
| `trade_count` | `target`      | `trade`    | `trade_count`      | `trade_count >= target` |
| `volume`      | `target_usd` or `target` | `trade` | `volume_usd`       | `volume_usd >= target`  |
| `signup`      | —             | `signup`   | `signed_up`        | on first `signup` event  |

Example quest rule: `{"type": "trade_count", "target": 5}`. Each `POST /events` with `event_type: "trade"` increments the user’s progress for that quest; when `trade_count` reaches 5, the quest is marked completed and the user can call **claim**.

---

## Docker Setup

**Requirements**: Docker and Docker Compose.

1. Clone the repo and enter it:
   ```bash
   cd gamification-core
   ```
2. Copy env (optional; compose has defaults):
   ```bash
   cp .env.example .env
   ```
3. Start API, Postgres, and Redis:
   ```bash
   docker compose up -d
   ```
4. API: **http://localhost:8000**  
   Docs: **http://localhost:8000/docs**  
   Code is mounted; edit files and save for hot reload (no rebuild).
5. Stop:
   ```bash
   docker compose down
   ```

---

## Local Development (no Docker)

- Python 3.11+.
- PostgreSQL 16 and Redis (optional for future cache/queue).

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env       # set DATABASE_URL, REDIS_URL if needed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Install as Library

For use by a multi-tenant SaaS backend (e.g. quest-saas-api):

```bash
pip install -e /path/to/gamification-core
```

The SaaS layer can import `QuestService`, `ProgressService`, `RuleEngine`, and models, and mount the same API under tenant-scoped routes.

---

## Testing

- **Unit tests**: `RuleEngine.evaluate(...)` and progress state transitions (e.g. in `tests/unit/`).
- **Integration tests**: API tests with a test DB (e.g. `tests/integration/`), including `POST /events` → progress update → claim.

Run (when added):

```bash
pytest
```

---

## Scaling & Future Work

- **Leaderboard**: Expose “top users by completed quests” or by custom metrics derived from `progress_payload` (e.g. total volume). Can be a new endpoint or a separate read model fed from the same events.
- **Rate limiting**: Add per-`user_id` or per-IP limits on `POST /events` (e.g. Redis-based) before production.
- **Webhooks**: Not in this repo; the **quest-saas-api** (private) adds tenant webhooks on completion/claim; this core stays event-agnostic.

---

## License

See repository license. Part of the Gamification & Mini Exchange OSS ecosystem; for full architecture and repo map, see `ARCHITECTURE_AND_PROJECTS.md` in the workspace root (if present) or the main ecosystem repo.
