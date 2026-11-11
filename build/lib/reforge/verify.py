"""Run repository commands in an isolated Docker container."""

from __future__ import annotations

import shlex
import subprocess
import time
from pathlib import Path

from reforge.types import VerificationResult


def verify(root: Path, config: dict, command: list[str] | None = None) -> VerificationResult:
    options = config.get("verification", config)
    image = str(options.get("docker_image", "python:3.11-slim"))
    command = command or options.get("command", ["python", "-m", "pytest", "-q"])
    timeout = int(options.get("timeout_seconds", 600))
    args = [
        "docker", "run", "--rm", "--network", "none", "--read-only",
        "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt",
        "no-new-privileges:true",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=512m",
        "--tmpfs", "/workspace:rw,nosuid,size=2g",
        "--memory", str(options.get("memory", "4g")), "--cpus", str(options.get("cpus", 2)),
        "--pids-limit", str(options.get("pids_limit", 256)),
        "-v", f"{root.resolve()}:/input:ro", "-w", "/workspace", image,
        # The sandbox user cannot preserve source timestamps on the tmpfs.
        # Copy the content only, then execute the configured command.
        "sh", "-lc", "cp -R /input/. /workspace/ && " + shlex.join(command),
    ]
    started = time.monotonic()
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return VerificationResult(result.returncode == 0, result.returncode,
                                  result.stdout + result.stderr, time.monotonic() - started)
    except (OSError, subprocess.TimeoutExpired) as exc:
        output = str(exc)
        return VerificationResult(False, None, output, time.monotonic() - started)
