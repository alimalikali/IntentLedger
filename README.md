# IntentLedger

IntentLedger is a local-first architectural-intent review tool. It pins analysis to Git SHAs and evidence cutoffs, distinguishes acceptance from review/activation, preserves conflicts, and runs trusted TypeScript boundary checks on base and head.

## Quick start

See [operations](docs/operations.md), [architecture/semantics](docs/architecture.md), [schemas](docs/schemas.md), the [three-minute demo](docs/demo.md), and [implementation status](docs/implementation-status.md). The generated [benchmark report](evals/reports/benchmark.md) is explicitly synthetic.

```sh
cp .env.example .env
make setup
docker compose up -d db
make migrate
make demo-seed
make demo-analyze
```

This MVP is not production-ready and makes no guarantee that inferred intent is correct. Unsupported analysis never counts as passing.
