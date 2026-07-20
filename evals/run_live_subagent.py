#!/usr/bin/env python3
"""
Live Subagent Trial Helper
Sets up persistent workspace directories for running Antigravity subagent evaluations.
"""

import shutil
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
HARNESS_DIR = EVALS_DIR / "harness"
SCENARIOS_DIR = EVALS_DIR / "scenarios"
WORKSPACES_DIR = EVALS_DIR / "workspaces"

sys.path.insert(0, str(HARNESS_DIR))
import spec_validator
from sandbox import ScenarioSandbox


def prepare_live_workspace(scenario_id: str, condition: str) -> Path:
    """
    Prepares a persistent workspace directory for a live AI agent trial.
    """
    scenario_path = SCENARIOS_DIR / scenario_id
    if not scenario_path.exists():
        raise ValueError(f"Scenario '{scenario_id}' does not exist.")

    trial_dir = WORKSPACES_DIR / f"{scenario_id}_{condition.lower()}"
    if trial_dir.exists():
        shutil.rmtree(trial_dir)

    trial_dir.mkdir(parents=True, exist_ok=True)

    # Copy starter files
    starter_dir = scenario_path / "workspace"
    if starter_dir.exists():
        for item in starter_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, trial_dir / item.name)
            else:
                shutil.copy2(item, trial_dir / item.name)

    # Copy experiences & manage-experience
    project_root = EVALS_DIR.parent
    shutil.copytree(project_root / "manage-experience", trial_dir / "manage-experience")
    
    exp_dir = trial_dir / "experiences"
    exp_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(project_root / "experiences" / "INDEX.md", exp_dir / "INDEX.md")

    if condition == "warm":
        # Inject matching playbook
        exp_id_map = {
            "frontmatter-parser": "EXP-20260720-0001",
            "atomic-writer": "EXP-20260720-0002",
            "subprocess-pipe": "EXP-20260720-0003",
        }
        exp_id = exp_id_map.get(scenario_id)
        if exp_id:
            for exp_file in (project_root / "experiences").rglob(f"{exp_id}.md"):
                rel_domain = exp_file.parent.name
                (exp_dir / rel_domain).mkdir(parents=True, exist_ok=True)
                shutil.copy2(exp_file, exp_dir / rel_domain / exp_file.name)

    return trial_dir


if __name__ == "__main__":
    scenario = sys.argv[1] if len(sys.argv) > 1 else "frontmatter-parser"
    cond = sys.argv[2] if len(sys.argv) > 2 else "cold"
    ws = prepare_live_workspace(scenario, cond)
    print(f"Prepared live workspace: {ws}")
