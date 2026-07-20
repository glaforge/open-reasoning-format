#!/usr/bin/env python3
"""
Verification suite for Scenario 3: Non-Blocking Subprocess Pipe Streaming
"""

import sys
import importlib.util
from pathlib import Path

# Import spec validator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "harness"))
import spec_validator


def verify_scenario(workspace_dir: Path) -> dict:
    script_file = workspace_dir / "safe_runner.py"
    if not script_file.exists():
        return {
            "success": False,
            "trap_avoided": False,
            "recorded_new_exp": False,
            "exp_spec_valid": False,
            "details": "safe_runner.py was not created."
        }

    code_text = script_file.read_text(encoding="utf-8")
    # Trap avoidance check: communicate() or select() or poll() used instead of naive proc.wait()
    trap_avoided = ("communicate" in code_text or "selector" in code_text or "poll" in code_text)

    try:
        spec = importlib.util.spec_from_file_location("safe_runner", script_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "run_command_with_timeout"):
            # Run test command producing 150KB output to test pipe buffer handling
            cmd = [sys.executable, "-c", "import sys; print('A' * 150000); sys.stderr.write('B' * 150000)"]
            ret, out, err = module.run_command_with_timeout(cmd, timeout=5.0)
            success = ret == 0 and len(out.strip()) >= 150000 and len(err.strip()) >= 150000 and trap_avoided
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
    new_exp_files = [f for f in exp_files if f.name not in ["EXP-20260720-0001.md", "EXP-20260720-0002.md", "EXP-20260720-0003.md"]]
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
