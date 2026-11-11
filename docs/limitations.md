# Limitations

- The deterministic SQLAlchemy rules cover only unambiguous legacy call forms:
  `Session.query(Model).get(key)`, `select([Entity])`, and `case([(when, then)])`.
  Other SQLAlchemy 2.0 migration patterns still need dedicated, tested rules.
- Static analysis indexes definitions, imports, and syntactic call sites. It
  cannot resolve dynamic imports, runtime dispatch, or aliases across packages.
- Guarded migrations and rules-only benchmark trials preserve test files,
  compare coverage, enforce a minimal-diff guard, and run the repository's
  configured command in Docker. Repositories still need their dependencies
  available in the sandbox image and a passing baseline test command.
- A local command-model adapter and guarded Git patch application are available.
  Hosted providers require an adapter and credentials supplied by the operator.
- The LoRA recipe requires a selected base model, a mined JSONL patch dataset,
  compatible hardware, and the optional training dependencies. It does not
  publish or imply trained-model results.
- The corpus is intentionally empty until repositories have been license-reviewed
  and mined. Evaluation quality remains bounded by the original repository tests.
