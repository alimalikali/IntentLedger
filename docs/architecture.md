# Architecture and semantics

FastAPI owns writes, review events, and PostgreSQL state. A Python job claimant leases durable jobs and invokes the trusted Node worker through `worker.schema.json`; stdout is JSON and diagnostics belong on stderr. The worker reads immutable Git objects with argument arrays and TypeScript's parser. It never checks out a revision, executes configuration, runs hooks/scripts, or installs repository dependencies. Next.js polls FastAPI and contains no policy logic.

## Temporal model

Revision names are resolved to 40-character SHAs before analysis. Git ancestry—not timestamps—determines applicability. Acceptance, ancestry, path/symbol scope, exceptions, and checker coverage remain independent. Confirmed scoped supersession suppresses only overlapping scope. Unsupported anchors, ambiguous lineage, and accepted unresolved contradictions abstain. Strict replay excludes sources without demonstrable availability at the cutoff; ingestion time is never substituted. Current reconstruction is separately labeled. Enforcement freezes approved policy at the base SHA.

Evidence snapshots are immutable and citations retain exact offsets/lines. Quote validation requires the quote to equal the snapshot slice. Historical acceptance, system review, and exact rule approval/activation are separate events. Rule approvals bind the canonical JSON SHA-256; edits require a new approval.

## Isolation and limitations

The MVP worker supports TS imports/re-exports, type imports, literal `require`, and literal/non-literal dynamic imports. Path aliases and transitive/barrel graphs are represented by the Node analyzer contract; the compact offline CLI checker currently enforces direct package imports only. Non-literal loads become `unsupported`, never pass. Adapter checks constrain static references and do not prove runtime behavior. Configure an external read-only/time-limited container before using untrusted repositories; absent that mechanism, production gating is unavailable. Public hosting needs real authentication/authorization and is out of scope.
