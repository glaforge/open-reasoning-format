#!/usr/bin/env python3
"""
Verification suite for Scenario: LangChain4j Java Maven + Gemini Integration
"""

import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# Import spec validator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "harness"))
import spec_validator


VALID_MODELS = {"gemini-2.5-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3.1-flash-lite"}
OBSOLETE_MODELS = {"gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro", "text-bison"}


def verify_scenario(workspace_dir: Path) -> dict:
    pom_file = workspace_dir / "pom.xml"
    if not pom_file.exists():
        # Check subdirectories if project was created in a subfolder
        poms = list(workspace_dir.rglob("pom.xml"))
        if poms:
            pom_file = poms[0]
        else:
            return {
                "success": False,
                "trap_avoided": False,
                "recorded_new_exp": False,
                "exp_spec_valid": False,
                "details": "pom.xml was not created."
            }

    pom_text = pom_file.read_text(encoding="utf-8")

    # 1. Check Java version >= 17
    java_version_ok = False
    java_match = re.search(r"<(?:maven\.compiler\.source|maven\.compiler\.target|java\.version)>(\d+)</", pom_text)
    if java_match:
        ver = int(java_match.group(1))
        java_version_ok = ver >= 17

    # 2. Check LangChain4j dependency
    langchain_dep_ok = "langchain4j-google-genai" in pom_text or "langchain4j" in pom_text

    # 3. Inspect Java source files
    java_files = list(pom_file.parent.rglob("*.java"))
    model_name_ok = False
    trap_avoided = False
    has_paris_assertion = False

    for jf in java_files:
        code = jf.read_text(encoding="utf-8")
        
        # Check model name
        for mod in VALID_MODELS:
            if mod in code:
                model_name_ok = True
                break
                
        # Check trap avoidance (not using obsolete models)
        has_obsolete = any(obs in code for obs in OBSOLETE_MODELS)
        if not has_obsolete and (model_name_ok or "gemini" in code.lower()):
            trap_avoided = True

        if "Paris" in code or "paris" in code:
            has_paris_assertion = True

    success = java_version_ok and langchain_dep_ok and model_name_ok and has_paris_assertion and trap_avoided

    # 4. Check Phase 2 experience file creation
    exp_files = list((workspace_dir / "experiences").rglob("EXP-*.md"))
    new_exp_files = [
        f for f in exp_files
        if f.name not in ["EXP-20260720-0001.md", "EXP-20260720-0002.md", "EXP-20260720-0003.md", "EXP-20260721-0001.md"]
    ]
    recorded_new_exp = len(new_exp_files) > 0
    exp_spec_valid = False
    if recorded_new_exp:
        validation = spec_validator.validate_experience_file(new_exp_files[0])
        exp_spec_valid = validation["valid"]

    details = []
    if not java_version_ok:
        details.append("Java compiler version is <17 or missing.")
    if not langchain_dep_ok:
        details.append("LangChain4j dependency missing in pom.xml.")
    if not model_name_ok:
        details.append("Gemini model name not recognized as modern (expected gemini-2.5-flash or gemini-flash-latest).")
    if not has_paris_assertion:
        details.append("Assertion for 'Paris' missing in Java code.")

    return {
        "success": success,
        "trap_avoided": trap_avoided and java_version_ok,
        "recorded_new_exp": recorded_new_exp,
        "exp_spec_valid": exp_spec_valid,
        "details": "; ".join(details) if details else "Verification complete."
    }
