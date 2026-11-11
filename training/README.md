# Training data workflow

1. Clone and license-review a candidate repository, then mine its Git history:
   `python -m training.mine_repos --scan REPOSITORY --output records.json --license MIT --test-command python -m pytest -q`.
2. Validate existing records with `python -m training.mine_repos input.json output.json`.
3. Build before/after patch records with `training.build_pairs` and split by
   repository with `training.split_repos`.
4. Train a selected base model with `python -m training.finetune --dataset pairs.jsonl --base-model MODEL --output adapters/`.
   This downloads the requested model and requires `reforge-migrations[training]`.
