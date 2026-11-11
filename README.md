# Reforge

**Test-verified code migration with deterministic rewrites and small language models.**

Reforge migrates a codebase to a newer library version by applying exact, rule-based rewrites first, and only sending the leftover cases to a language model. Every change is gated by the repository's *original* test suite inside a sandbox, with guards that stop the model from "passing" by weakening the tests.

> **Status: work in progress.** The results table below is empty until the benchmark has been run. Nothing in this README reports a number that has not been measured. See [Roadmap](#roadmap) for what is built.

---

## Why this exists

Large-scale migrations are mostly mechanical, and the hard residue is where models are useful, but also where they cheat or waste money. Reforge asks one question:

> Can a hybrid of deterministic rules, a **LoRA-tuned small language model** and guarded test verification match large-LLM pipelines on correctness at a fraction of the cost and latency?

The headline output is a **cost-versus-correctness Pareto frontier**: test pass rate against cost and latency per repository, for every pipeline variant, on the same corpus.

## How it works

```
repo + target version
        │
   1 Analyze    parse, symbol table, call graph, find affected sites
        │
   2 Rules      deterministic LibCST codemods (cheap, exact, repeatable)
        │
   3 Verify     sandbox: build + lint + original tests   ◄───────┐
        │                                                        │
        ├── all pass ──► 6 Report                                │
        │                                                        │
   4 Context    failing sites + test errors + call-graph slice   │
        │                                                        │
   5 Model      SLM (or LLM baseline) proposes a patch           │
        │                                                        │
        └──► guards ──► apply ───────────────────────────────────┘
             (bounded retries, then flag for human review)
```

1. **Analyze:** builds a symbol table and call graph once, so later stages only touch what matters.
2. **Rules:** LibCST codemods apply the well-defined changes. Each change is tagged with the rule that produced it.
3. **Verify:** runs the build, linters and the repo's existing tests in a Docker sandbox (no network, CPU/memory/time limits).
4. **Context:** gives the model only the failing sites, the test error output and the relevant slice of the call graph, which keeps prompts small.
5. **Model:** a swappable interface. The same pipeline runs with a LoRA-tuned SLM, a hosted LLM, or no model at all (rules only).
6. **Report:** a reviewable diff per change with its provenance (rule ID or model ID), plus any sites left for human review.

### Anti-gaming guards

A model can make tests pass by deleting or weakening them. Before a patch is accepted, Reforge checks that:

- test files are byte-identical to the original,
- measured coverage does not drop,
- the diff stays minimal relative to the sites that needed changing.

The loop also detects oscillation (flipping between two broken states), tracks the best attempt so far, and stops at a token and iteration budget instead of guessing.

## Target migration

The first supported migration is **SQLAlchemy 1.x → 2.0** (planned). It was chosen because it is less covered by existing open-source agents than Python 2 → 3, has a large public corpus of real migration commits, and has a well-defined deterministic portion. Further migrations plug in through the `rules/` package.

## Experiment design

All arms run on the same held-out repositories, with repeated trials because model output varies.

| Arm | Description |
|---|---|
| `rules_only` | Deterministic codemods and verification, no model |
| `llm_single` | Large LLM, single prompt, no feedback |
| `llm_loop` | Large LLM with the verify-and-repair loop |
| `slm_loop` | LoRA-tuned small model with the same loop |
| `hybrid` | Rules first, then SLM, then repair loop (proposed system) |
| external baselines | Existing open-source agents run on the same corpus for comparison |

**Metrics:** original-test pass rate, build success, guard violations, diff size against the maintainers' change, tokens and cost per repo, wall-clock time, and a failure-category breakdown.

**Data:** repositories with permissive licenses that contain a real migration commit and a working test suite. Train and eval repositories are split strictly at the repo level. The evaluation corpus is a manifest of pinned commits, not a copy of the code.

## Results

The initial rules-only seed run uses one pinned public repository and its focused
regression module. It validates the harness, but it is not sufficient evidence
to compare migration strategies.

| Arm | Test pass rate | Build success | Cost / repo | p95 latency | Guard violations |
|---|---|---|---|---|---|
| `rules_only` | 100% (1/1) | 100% (1/1) | $0.00 | 77.03 s | 0 |
| `llm_single` | not yet run | | | | |
| `llm_loop` | not yet run | | | | |
| `slm_loop` | not yet run | | | | |
| `hybrid` | not yet run | | | | |

![Pareto frontier](results/pareto.png)
*Generated by `make bench`; not yet available.*

## Quick start

```bash
git clone https://github.com/rakshithashok/reforge
cd reforge
pip install -e ".[dev]"
docker build --tag reforge-sandbox:latest .

# migrate a repo (rules + model, verified in the sandbox)
reforge migrate ./path/to/repo --target sqlalchemy-2.0 --config configs/pipeline.yaml

# apply only when the original and migrated test and coverage checks pass
reforge migrate ./path/to/repo --verify --config configs/pipeline.yaml

# only verify an existing migration against the original tests
reforge verify ./path/to/repo

# run the benchmark and regenerate tables and plots
make bench
reforge report results/
```

> Commands show the intended interface. Check the [Roadmap](#roadmap) for which are implemented.

## Repository layout

```
src/reforge/     pipeline: analysis, rules, models, context, verify, repair, audit
training/        mine repos, build before/after pairs, repo-level split, LoRA fine-tuning
bench/           corpus manifest, harness, baselines, metrics, plots
configs/         pipeline settings and one YAML per experiment arm
tests/           unit tests, integration tests on small fixture repos
docs/            design notes, threat model, limitations
```

## Safety

Reforge executes untrusted code from third-party repositories. Run it only through the provided containers: no network access, resource limits, and no mounted credentials. See [`docs/threat_model.md`](docs/threat_model.md).

## Related work

Reforge builds on, and should be compared against, existing work:

- [codeshift](https://github.com/gkhurana21/codeshift): LLM agent for Python 2 → 3 with a behavioral-oracle benchmark and repair loop.
- [depfix-ai](https://pypi.org/project/depfix-ai/): scans for affected call sites, generates LLM fixes verified by your test suite, and opens a PR.
- [ZeroDiff](https://pypi.org/project/zerodiff/): deterministic behavior-recording verifier that works with any agent.
- [AIMigrate](https://arxiv.org/abs/2511.00160): open-source package and dataset for diff-based LLM code migration.
- [TimeMachine-bench](https://arxiv.org/abs/2601.22597): software migration benchmark that documents spurious solutions exploiting low test coverage.
- [RepoMod-Bench](https://arxiv.org/abs/2602.22518): repository-level modernization benchmark with hidden, implementation-agnostic tests.
- [OpenRewrite / Moderne](https://docs.moderne.io): the industry standard for deterministic, recipe-based refactoring, and the model for the "rules first" design.

**What Reforge adds:** a head-to-head comparison of small and large models inside the same rules-plus-verification pipeline, anti-gaming guards as a first-class stage, and a published cost-versus-correctness frontier on a migration that existing open-source agents do not cover.

## Roadmap

- [x] Core types, Docker sandbox and verify runner on fixture repos
- [x] Rules-only baseline for SQLAlchemy 1.x → 2.0
- [x] Anti-gaming guards (tests untouched, coverage, minimal diff)
- [x] Benchmark harness, metrics and corpus manifest
- [ ] LLM baselines and repair loop
- [x] Repo mining, training pairs and LoRA fine-tuning recipe
- [ ] Audit report and CLI polish
- [x] CI and Docker image
- [x] Rules-only seed benchmark and results

## Limitations

- Results depend on the test suites of the evaluation repos. Weak tests mean a passing migration is not proof of correctness, which is why the guards exist but do not eliminate the risk.
- Evaluation is limited to one migration and one language.
- Base models may have seen popular evaluation repositories during pre-training. The corpus is checked for this, but it cannot be ruled out entirely.
- Small evaluation sets give wide confidence intervals; results are reported over repeated trials.

## License

TBD (choose a permissive license before publishing).

## Author

Rakshith Ashok Kumar
