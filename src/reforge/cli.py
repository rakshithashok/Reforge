from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

from reforge.config import load_yaml
from reforge.pipeline import migrate, migrate_verified
from reforge.report import write_report
from reforge.verify import verify


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reforge", description="Guarded code migration")
    commands = parser.add_subparsers(dest="command", required=True)
    migration = commands.add_parser("migrate", help="Apply supported deterministic migration rules")
    migration.add_argument("repository", type=Path)
    migration.add_argument("--target", default="sqlalchemy-2.0")
    migration.add_argument("--config", type=Path, default=Path("configs/pipeline.yaml"))
    migration.add_argument("--dry-run", action="store_true", help="Print changes without writing them")
    migration.add_argument("--verify", action="store_true", help="Accept changes only after guarded verification")
    migration.add_argument("--report-dir", type=Path, default=Path("results/migration"))

    verification = commands.add_parser("verify", help="Run a repository's tests in Docker")
    verification.add_argument("repository", type=Path)
    verification.add_argument("--config", type=Path, default=Path("configs/pipeline.yaml"))
    verification.add_argument(
        "--command",
        dest="command_override",
        nargs=argparse.REMAINDER,
        help="Override configured test command; place this option last",
    )

    reporting = commands.add_parser("report", help="Inspect a generated report directory")
    reporting.add_argument("directory", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "migrate":
            if args.verify and args.dry_run:
                raise ValueError("--verify cannot be combined with --dry-run")
            result = (migrate_verified(args.repository, load_yaml(args.config), args.target)
                      if args.verify else migrate(args.repository, args.target, apply=not args.dry_run))
            for change in result.changes:
                print("".join(difflib.unified_diff(
                    change.before.splitlines(True), change.after.splitlines(True),
                    fromfile=f"a/{change.path}", tofile=f"b/{change.path}")))
            output = write_report(result, args.report_dir)
            if result.human_review:
                print("Migration reverted; review required: " + "; ".join(result.human_review), file=sys.stderr)
                return 1
            print(f"{len(result.changes)} file(s) changed; report: {output}")
            return 0
        if args.command == "verify":
            result = verify(args.repository, load_yaml(args.config), args.command_override)
            print(result.output, end="" if result.output.endswith("\n") else "\n")
            print(json.dumps({"passed": result.passed, "exit_code": result.exit_code,
                              "duration_seconds": result.duration_seconds}))
            return 0 if result.passed else 1
        report_path = args.directory / "report.json"
        benchmark_path = args.directory / "benchmark.json"
        if report_path.is_file():
            print(report_path.read_text(encoding="utf-8"))
            return 0
        if benchmark_path.is_file():
            data = json.loads(benchmark_path.read_text(encoding="utf-8"))
            summary = data["summary"]
            print(f"Arm: {data['arm']}\nRepositories: {summary['repositories']}\n"
                  f"Test pass rate: {summary['test_pass_rate']}\n"
                  f"Mean cost: {summary['mean_cost_usd']}\n")
            return 0
        print(f"No report found in {args.directory}", file=sys.stderr)
        return 2
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"reforge: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
