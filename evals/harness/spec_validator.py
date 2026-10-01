#!/usr/bin/env python3
"""
ORF Spec Validator
Validates whether an experience file complies strictly with Open Reasoning Format (v0.2.0).
"""

import re
from pathlib import Path
import yaml


REQUIRED_FRONTMATTER_KEYS = ["id", "title", "description", "domain", "keywords", "complexity", "created_at"]
ALLOWED_COMPLEXITIES = {"low", "medium", "high"}

REQUIRED_SECTIONS = [
    "## 1. Objective",
    "## 2. The Trap",
    "## 3. Abstracted Insight",
    "## 4. Validated Path",
    "## 5. Verification Checklist",
]


def parse_frontmatter(content: str):
    """
    Splits YAML frontmatter and body content using line-anchored '---' delimiters.
    """
    parts = re.split(r"^---\s*$", content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        return None, content
    try:
        fm = yaml.safe_load(parts[1])
        return fm, parts[2]
    except Exception:
        return None, parts[2]


def validate_experience_file(filepath: Path) -> dict:
    """
    Validates an experience markdown file against ORF v0.2 specification rules.
    Returns dict: {"valid": bool, "errors": list[str], "warnings": list[str], "metadata": dict}
    """
    errors = []
    warnings = []
    metadata = {}

    if not filepath.exists():
        return {"valid": False, "errors": [f"File {filepath} does not exist."], "warnings": [], "metadata": {}}

    content = filepath.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    # 1. Frontmatter check
    if fm is None or not isinstance(fm, dict):
        errors.append("Invalid or missing YAML frontmatter header (must be delimited by line-anchored '---').")
    else:
        metadata = fm
        for key in REQUIRED_FRONTMATTER_KEYS:
            if key not in fm or fm[key] is None:
                errors.append(f"Missing required frontmatter key: '{key}'.")
        
        if "id" in fm and not str(fm["id"]).startswith("EXP-"):
            errors.append(f"Invalid experience ID format: '{fm['id']}' (must start with 'EXP-').")
            
        if "complexity" in fm and fm["complexity"] not in ALLOWED_COMPLEXITIES:
            errors.append(f"Invalid complexity: '{fm['complexity']}' (must be low, medium, or high).")
            
        if "keywords" in fm and not isinstance(fm["keywords"], list):
            errors.append("Frontmatter 'keywords' must be a YAML list of strings.")

    # 2. Required sections check
    section_indices = []
    for section in REQUIRED_SECTIONS:
        pos = body.find(section)
        if pos == -1:
            errors.append(f"Missing mandatory section header: '{section}'.")
        else:
            section_indices.append(pos)

    # Check section order
    if len(section_indices) == len(REQUIRED_SECTIONS):
        if section_indices != sorted(section_indices):
            errors.append("Mandatory sections are out of order. Required order: Objective, The Trap, Abstracted Insight, Validated Path, Verification Checklist.")

    # 3. Core Principle check in Abstracted Insight
    if "> **Core Principle:**" not in body:
        errors.append("Section '## 3. Abstracted Insight' must begin with blockquote '> **Core Principle:** ...'")

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "metadata": metadata
    }


def validate_index_registration(index_path: Path, exp_id: str) -> bool:
    """
    Checks if an experience ID is referenced in the INDEX.md file.
    """
    if not index_path.exists():
        return False
    content = index_path.read_text(encoding="utf-8")
    return exp_id in content
