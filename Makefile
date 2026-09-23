.PHONY: setup dev migrate demo-seed demo-analyze lint typecheck test e2e evaluate check reset
setup:
	uv sync --extra dev && pnpm install --frozen-lockfile

dev:
	uv run uvicorn intentledger.main:app --app-dir services/api --host 127.0.0.1 --port 8000
migrate:
	uv run alembic -c services/api/alembic.ini upgrade head
demo-seed:
	uv run intentledger demo seed --path .intentledger/demo
demo-analyze:
	uv run intentledger analyze --repo .intentledger/demo --base main~1 --head main --json
lint:
	uv run ruff check services tests evals fixtures && pnpm -r lint
typecheck:
	uv run python -m compileall -q services fixtures evals && pnpm -r typecheck
test:
	uv run pytest -q
e2e:
	uv run pytest -q tests/e2e

evaluate:
	uv run python evals/run.py --output evals/reports
check:
	uv run intentledger check --repo .intentledger/demo --base main~1 --head main --rule fixtures/demo/rule.json --json
reset:
	@echo 'Refusing implicit destructive reset. Run: docker compose down -v && rm -rf .intentledger'
