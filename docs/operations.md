# Operations

SQLite is the explicit offline mode: set `INTENTLEDGER_STORAGE=sqlite` and `INTENTLEDGER_DB_PATH=.intentledger/intentledger.db`. PostgreSQL selection currently fails closed and never falls back to SQLite.

See the root README and `docs/implementation-status.md` for installation, startup, test commands, expected outcomes, and environment blockers. Bind API/web services to loopback. Keep `LOCAL_API_TOKEN` server-side; the Next server actions and export proxy attach it. Public hosting requires authentication and authorization not included in this MVP.

Reset is destructive and explicit: stop services, then remove the configured SQLite file. For the future PostgreSQL mode use `docker compose down -v` only after confirming data destruction.
