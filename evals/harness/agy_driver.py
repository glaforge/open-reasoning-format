#!/usr/bin/env python3
"""
Antigravity CLI Driver (`agy`)
Executes scenario evaluations non-interactively using the local `agy` CLI binary.
"""

import subprocess
import shutil
from pathlib import Path


def is_agy_installed() -> bool:
    """
    Checks if `agy` command is available in system PATH.
    """
    return shutil.which("agy") is not None


def run_scenario_with_agy(workspace_dir: Path, prompt_text: str, timeout_sec: float = 300.0) -> tuple[int, str, str]:
    """
    Executes a single prompt non-interactively using `agy --print`.
    """
    if not is_agy_installed():
        raise RuntimeError("`agy` CLI binary not found in PATH.")

    cmd = [
        "agy",
        "--dangerously-skip-permissions",
        "--add-dir", str(workspace_dir),
        "--print", prompt_text
    ]


    proc = subprocess.Popen(
        cmd,
        cwd=str(workspace_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        stdout, stderr = proc.communicate(timeout=timeout_sec)
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return -1, stdout, f"TimeoutExpired after {timeout_sec} seconds: {stderr}"
