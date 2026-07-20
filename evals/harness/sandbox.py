#!/usr/bin/env python3
"""
ORF Scenario Sandbox Manager
Creates and cleans up isolated environments for evaluating scenario trajectories.
"""

import shutil
import tempfile
from pathlib import Path


class ScenarioSandbox:
    def __init__(self, scenario_dir: Path, enable_orf: bool = False, experience_ids: list[str] = None):
        self.scenario_dir = scenario_dir
        self.enable_orf = enable_orf
        self.experience_ids = experience_ids or []
        self.temp_dir = None
        self.workspace = None

    def __enter__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="orf_eval_"))
        self.workspace = self.temp_dir / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Copy starter workspace files if scenario provides a workspace directory
        starter_workspace = self.scenario_dir / "workspace"
        if starter_workspace.exists():
            for item in starter_workspace.iterdir():
                if item.is_dir():
                    shutil.copytree(item, self.workspace / item.name)
                else:
                    shutil.copy2(item, self.workspace / item.name)

        # Setup experiences folder inside workspace
        exp_dir = self.workspace / "experiences"
        exp_dir.mkdir(parents=True, exist_ok=True)

        # Copy manage-experience helper script to workspace
        project_root = Path(__file__).resolve().parent.parent.parent
        manage_exp_src = project_root / "manage-experience"
        if manage_exp_src.exists():
            shutil.copytree(manage_exp_src, self.workspace / "manage-experience")

        # Copy INDEX.md
        index_src = project_root / "experiences" / "INDEX.md"
        if index_src.exists():
            shutil.copy2(index_src, exp_dir / "INDEX.md")

        if self.enable_orf and self.experience_ids:
            # Copy requested experience playbooks
            for exp_id in self.experience_ids:
                for exp_file in (project_root / "experiences").rglob(f"{exp_id}.md"):
                    rel_parent = exp_file.parent.name
                    target_domain_dir = exp_dir / rel_parent
                    target_domain_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(exp_file, target_domain_dir / exp_file.name)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
