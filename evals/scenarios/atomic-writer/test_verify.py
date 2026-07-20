#!/usr/bin/env python3
"""
Verification suite for Scenario 2: Safe Atomic File Storage
"""

import sys
import os
import json
import importlib.util
from pathlib import Path

# Import spec validator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "harness"))
import spec_validator


def verify_scenario(workspace_dir: Path) -> dict:
    script_file = workspace_dir / "atomic_store.py"
    if not script_file.exists():
        return {
            "success": False,
            "trap_avoided": False,
            "recorded_new_exp": False,
            "exp_spec_valid": False,
            "details": "atomic_store.py was not created."
        }

    # Inspect code for atomic pattern (tempfile + os.replace or temp file write)
    code_text = script_file.read_text(encoding="utf-8")
    trap_avoided = ("replace" in code_text or "NamedTemporaryFile" in code_text or "mkstemp" in code_text)

    # Test functionality
    target_json = workspace_dir / "state.json"
    target_json.write_text(json.dumps({"version": 1, "data": "initial"}), encoding="utf-8")

    try:
        spec = importlib.util.spec_from_file_location("atomic_store", script_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "save_json_state"):
            module.save_json_state(str(target_json), {"version": 2, "data": "updated"})
            res_data = json.loads(target_json.read_text(encoding="utf-8"))
            success = res_data.get("version") == 2 and trap_avoided
        else:
            success = False
    except Exception as e:
        return {
            "success": False,
            "trap_avoided": trap_avoided,
            "recorded_new_exp": False,
            "exp_spec_valid": False,
            "details": f"Execution error: {e}"
        }

    # Check Phase 2 experience generation
    exp_files = list((workspace_dir / "experiences").rglob("EXP-*.md"))
    new_exp_files = [f for f in exp_files if f.name not in ["EXP-20260720-0001.md", "EXP-20260720-0002.md"]]
    recorded_new_exp = len(new_exp_files) > 0
    exp_spec_valid = False
    if recorded_new_exp:
        validation = spec_validator.validate_experience_file(new_exp_files[0])
        exp_spec_valid = validation["valid"]

    return {
        "success": success,
        "trap_avoided": trap_avoided,
        "recorded_new_exp": recorded_new_exp,
        "exp_spec_valid": exp_spec_valid,
        "details": "Verification complete."
    }
