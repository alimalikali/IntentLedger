# Three-minute offline demo

1. `make demo-seed` creates a synthetic repository with fixed Git identities and timestamps.
2. Open Decision timeline: compare old direct-SDK guidance with accepted ADR-002 and its legacy exception.
3. Open Change review: the unmerged newer “maybe” comment is proposal evidence and cannot override accepted policy.
4. Open Rule review: inspect exact JSON/hash, add rationale, approve the version, then separately activate it.
5. `make check`; exit 1 and JSON identify the introduced direct import in `refund.ts`.
6. Compare `main~2..main~1` to see adapter usage pass; remove the regression on a new local commit to see a resolved result.
7. Evaluation shows ambiguous rename/conflicting-decision cases abstaining and non-literal loading unsupported.

The provider label is **Demo fixture provider**. No output is represented as live AI analysis.
