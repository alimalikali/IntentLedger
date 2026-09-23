# Connector and rule schemas

PR import accepts repository, identifier, title/body, optional base/head/merge SHAs, state, created/updated/merged timestamps, and individually identified comments with author, timestamp, body, and optional snapshot history. Missing values remain null. Merge status is context—not acceptance.

Rules validate against `packages/contracts/rule.schema.json`; unknown fields fail. `forbidden_import` uses scope, forbidden targets, exceptions, mode, and type-only policy. `adapter_boundary` uses protected packages, allowed adapter paths, consumer scope, exceptions, mode, and type-only policy. Parameters compile into trusted checker branches: no `eval`, generated source, model commands, or shell interpolation.
