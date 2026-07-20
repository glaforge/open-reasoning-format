#!/usr/bin/env python3
"""
Verification suite for Scenario 1: Frontmatter-Preserving Index Mutator
"""

import sys
import unittest
from pathlib import Path
import yaml

# Import spec validator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "harness"))
import spec_validator


def verify_scenario(workspace_dir: Path) -> dict:
    """
    Evaluates workspace result after scenario run.
    Returns {"success": bool, "trap_avoided": bool, "recorded_new_exp": bool, "exp_spec_valid": bool, "details": str}
    """
    index_file = workspace_dir / "experiences" / "INDEX.md"
    script_file = workspace_dir / "update_index.py"

    if not script_file.exists():
        return {
            "success": False,
            "trap_avoided": False,
            "recorded_new_exp": False,
            "exp_spec_valid": False,
            "details": "update_index.py script was not created."
        }

    # Verify script execution
    try:
        content = index_file.read_text(encoding="utf-8")
        fm, body = spec_validator.parse_frontmatter(content)
        
        trap_avoided = fm is not None and content.startswith("---")
        success = trap_avoided and "spec_version" in (fm or {})
    except Exception as e:
        return {
            "success": False,
            "trap_avoided": False,
            "recorded_new_exp": False,
            "exp_spec_valid": False,
            "details": f"Error parsing index file: {e}"
        }

    # Check for recorded new experience (Phase 2)
    exp_files = list((workspace_dir / "experiences").rglob("EXP-*.md"))
    # Exclude initial EXP-20260720-0001
    new_exp_files = [f for f in exp_files if f.name != "EXP-20260720-0001.md"]
    
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
