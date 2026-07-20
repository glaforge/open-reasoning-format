#!/usr/bin/env python3
"""
Unit tests for ORF Evaluation Suite (spec_validator and harness components).
"""

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals" / "harness"))
import spec_validator


class TestORFSpecValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_valid_experience_file(self):
        exp_file = self.temp_dir / "EXP-20260720-0001.md"
        exp_file.write_text("""---
id: "EXP-20260720-0001"
title: "Valid experience"
description: "Sample description"
domain: "python-scripting"
keywords:
  - test
complexity: "low"
created_at: "2026-07-20"
---

## 1. Objective
Objective statement.

## 2. The Trap
Trap description.

## 3. Abstracted Insight
> **Core Principle:** Always validate.

## 4. Validated Path
Follow steps.

## 5. Verification Checklist
- [ ] Check step.
""", encoding="utf-8")

        res = spec_validator.validate_experience_file(exp_file)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)

    def test_missing_frontmatter_key(self):
        exp_file = self.temp_dir / "EXP-20260720-0002.md"
        exp_file.write_text("""---
id: "EXP-20260720-0002"
title: "Incomplete frontmatter"
---

## 1. Objective
Obj

## 2. The Trap
Trap

## 3. Abstracted Insight
> **Core Principle:** Test

## 4. Validated Path
Path

## 5. Verification Checklist
- [ ] Check
""", encoding="utf-8")

        res = spec_validator.validate_experience_file(exp_file)
        self.assertFalse(res["valid"])
        self.assertTrue(any("Missing required frontmatter key" in err for err in res["errors"]))

    def test_missing_core_principle(self):
        exp_file = self.temp_dir / "EXP-20260720-0003.md"
        exp_file.write_text("""---
id: "EXP-20260720-0003"
title: "Missing core principle"
description: "Desc"
domain: "python-scripting"
keywords: ["test"]
complexity: "medium"
created_at: "2026-07-20"
---

## 1. Objective
Obj

## 2. The Trap
Trap

## 3. Abstracted Insight
Insight without core principle format.

## 4. Validated Path
Path

## 5. Verification Checklist
- [ ] Check
""", encoding="utf-8")

        res = spec_validator.validate_experience_file(exp_file)
        self.assertFalse(res["valid"])
        self.assertTrue(any("Core Principle:" in err for err in res["errors"]))


if __name__ == "__main__":
    unittest.main()
