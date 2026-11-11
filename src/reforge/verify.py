"""Run repository commands in an isolated Docker container."""

from __future__ import annotations

import json
import shlex
import subprocess
import time
from pathlib import Path

from reforge.types import VerificationResult

_COVERAGE_MARKER = "__REFORGE_COVERAGE_JSON__"


def verify(root: Path, config: dict, command: list[str] | None = None,
           collect_coverage: bool = False, coverage_command: list[str] | None = None) -> VerificationResult:
    repository = root.resolve()
    if not repository.is_dir():
        raise ValueError(f"Repository does not exist or is not a directory: {root}")
    options = config.get("verification", config)
    image = str(options.get("docker_image", "python:3.11-slim"))
    command = command or options.get("command", ["python", "-m", "pytest", "-q"])
    if collect_coverage:
        command = coverage_command or options.get("coverage_command", ["coverage", "run", "-m", "pytest", "-q"])
    timeout = int(options.get("timeout_seconds", 600))
    args = [
        "docker", "run", "--rm", "--network", "none", "--read-only",
        "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt",
        "no-new-privileges:true",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=512m",
        "--tmpfs", "/workspace:rw,nosuid,size=2g,mode=1777",
        "-e", "PYTEST_ADDOPTS=-o cache_dir=/tmp/pytest-cache",
        "-e", "PYTHONPATH=/workspace/src:/workspace",
        "--memory", str(options.get("memory", "4g")), "--cpus", str(options.get("cpus", 2)),
        "--pids-limit", str(options.get("pids_limit", 256)),
        "-v", f"{repository}:/input:ro", "-w", "/workspace", image,
        "sh", "-lc", _script(command, collect_coverage),
    ]
    started = time.monotonic()
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        coverage = _coverage(result.stdout) if collect_coverage else None
        return VerificationResult(result.returncode == 0, result.returncode,
                                  result.stdout + result.stderr, time.monotonic() - started, coverage)
    except (OSError, subprocess.TimeoutExpired) as exc:
        output = str(exc)
        return VerificationResult(False, None, output, time.monotonic() - started)


def _script(command: list[str], collect_coverage: bool) -> str:
    # The sandbox user cannot preserve source timestamps on the tmpfs. Copy the
    # content only, then run the command. Coverage stays inside the container
    # and is emitted with a marker for parsing by the parent process.
    script = "cp -R /input/. /workspace/ && " + shlex.join(command)
    if collect_coverage:
        script += " && coverage json -o /tmp/reforge-coverage.json"
        script += f" && printf '\\n{_COVERAGE_MARKER}\\n' && cat /tmp/reforge-coverage.json"
    return script


def _coverage(stdout: str) -> float | None:
    if _COVERAGE_MARKER not in stdout:
        return None
    _, payload = stdout.rsplit(_COVERAGE_MARKER, 1)
    try:
        return float(json.loads(payload.strip()).get("totals", {}).get("percent_covered"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
