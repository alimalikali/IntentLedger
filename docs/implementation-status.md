# Implementation status

Updated: 2026-09-23; current HEAD inspected before work: `3d0f413`.

Status vocabulary: **written** means source exists, **integrated** means a real application path uses it, and **verified** means the named command actually ran in this environment.

## Storage selection

`INTENTLEDGER_STORAGE=sqlite` selects the verified offline database and `INTENTLEDGER_DB_PATH` selects its file. If PostgreSQL is selected, startup fails explicitly because that workflow adapter is not complete. If `DATABASE_URL` names PostgreSQL without an explicit storage choice, startup also fails. IntentLedger never silently falls back from PostgreSQL to SQLite. The SQLAlchemy/Alembic PostgreSQL-shaped schema remains future integration work.

## Workflow status

| Workflow | Written | Integrated | Executed here |
|---|---|---|---|
| Service workflow | register → immutable/idempotent ADR+rule ingestion → SHA-frozen analysis → exact approval → checker execution → persisted findings | `DatabaseStore` and FastAPI call the same business methods | **Yes:** service integration test passes, including store reconstruction |
| HTTP workflow | registration, ingestion, analysis, pre-approval rejection, stale rejection, exact approval, resume, findings, evidence and Markdown export | FastAPI endpoints call `DatabaseStore` only | **No:** test is written but skipped because FastAPI/httpx are not installed |
| API process restart | start uvicorn, read completed analysis, terminate, restart, read same output | Uses the configured SQLite file | **No:** test is written but skipped because FastAPI/uvicorn are not installed |
| Browser workflow | repository selection, registration, ingestion/rule input, analysis creation, exact approval/rejection, resume, evidence passage/revision, coverage and export | Next server components/actions call persisted APIs; API token stays server-side | **No:** Playwright test is written, but pnpm/Next/Playwright could not be installed or run |
| Worker lease recovery | Schema prototypes only | Not integrated | **No; incomplete** |

The UI has route-level loading and retry/error states. The report download uses a server-side proxy so the local API token is not exposed to browser JavaScript. Decision timeline and evaluation pages still need persisted API integration.

## Tests and checks executed

- `PYTHONPATH=services/api pytest -q` — **12 passed, 3 skipped**. Skips are dependency-gated HTTP/API-process tests; the persisted service workflow and fail-closed storage-selection test passed.
- `python -m compileall -q services fixtures evals` — passed.
- `git diff --check` — passed before commit.
- `tsc --noEmit -p apps/web/tsconfig.json` — failed because the globally available compiler cannot find the uninstalled Next.js, React, or Node type packages; this is an environment limitation, not recorded as a passing typecheck.
- Dependency cache inspection found no usable FastAPI, pnpm, Next.js, or Playwright artifacts.
- Registry requests were not repeatedly retried: the prior verified failures remain PyPI HTTPS tunnel rejection and npm/corepack HTTP 403.
- Docker remains absent.

## Local validation handoff

Required: Python 3.12, uv, Node 20+, pnpm 9.15.1, Git, and a Playwright Chromium installation. PostgreSQL is not required for explicit SQLite offline mode.

```sh
cp .env.example .env
# Set a generated LOCAL_API_TOKEN and keep:
# INTENTLEDGER_STORAGE=sqlite
# INTENTLEDGER_DB_PATH=.intentledger/intentledger.db
uv lock && uv sync --extra dev
corepack enable && pnpm install
pnpm exec playwright install chromium
PYTHONPATH=services/api uv run pytest -q
pnpm -r typecheck
pnpm --filter @intentledger/web build
```

Run services for the browser test:

```sh
PYTHONPATH=services/api uv run uvicorn intentledger.main:app --host 127.0.0.1 --port 8000
pnpm --filter @intentledger/web dev
# in a third terminal with matching LOCAL_API_TOKEN/API_URL/WEB_URL
pnpm --filter @intentledger/web e2e
```

Expected outcomes: Python HTTP and process-restart tests no longer skip; all workflow requests succeed except intentional pre-approval and stale-approval `409` responses; the browser sees the exact ADR passage and introduced `payment-sdk` finding; the production build succeeds.

## Remaining blockers

The original definition of done is not satisfied. PostgreSQL persistence/migrations, leased-worker recovery, isolated Node-worker invocation, decision/evaluation UI integration, and executed browser validation remain incomplete. Live AI work was intentionally not expanded in this iteration.
