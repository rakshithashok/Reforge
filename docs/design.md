# Design notes

The pipeline keeps deterministic transformations separate from model proposals.
Each transformation records provenance. Rules-only benchmark trials check out a
pinned source revision, run the migration, preserve the test snapshot, compare
coverage, enforce a minimal-diff guard, and verify the configured command in a
Docker sandbox. Model patches are Git-style diffs that are rejected when they
touch a test file and reverted when verification fails.

Static analysis indexes definitions, imports, and syntactic call sites without
executing project code. It provides focused context but does not claim to
resolve dynamic dispatch or imports.

## Migration rule policy

Rules should be narrow, idempotent, syntax preserving, and accompanied by
fixtures for both changed and unchanged source. Ambiguous transformations must
be reported for human review rather than guessed.
