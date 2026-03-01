# gamification-core

Backend: gamification engine — quests, progress, rules, events, REST API. FastAPI, PostgreSQL, Redis. Pip-installable.

Part of the Gamification & Mini Exchange ecosystem. See `ARCHITECTURE_AND_PROJECTS.md` in the workspace root for full architecture and repo map.

## Dev setup (Docker)

- Copy `.env.example` to `.env` (optional; compose has defaults).
- Run: `docker compose up -d`. API: http://localhost:8000, docs: http://localhost:8000/docs.
- Code is mounted into the container; change files and save — no rebuild needed (hot reload).
- Stop: `docker compose down`.
