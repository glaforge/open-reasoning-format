#!/usr/bin/env python3
"""
Unit tests for manage-experience/scripts/experiences.py helper script.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

# Import script functions
sys.path.insert(0, str(Path(__file__).parent.parent / "manage-experience" / "scripts"))
import experiences


class TestExperiencesCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Setup mock experiences folder and INDEX.md
        self.experiences_dir = Path("./experiences")
        self.experiences_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.experiences_dir / "INDEX.md"
        initial_index = """---
spec_version: "0.1"
last_updated: "2026-07-20"
categories:
  - id: "test-domain"
    name: "Test Domain"
    description: "Domain used for automated unit testing."
---

# Experiences Index

## Category: Test Domain (`test-domain`)
* [EXP-20260720-0001](test-domain/EXP-20260720-0001.md): Initial test experience.
"""
        self.index_path.write_text(initial_index, encoding="utf-8")

        # Create test category and sample file
        category_dir = self.experiences_dir / "test-domain"
        category_dir.mkdir(parents=True, exist_ok=True)

        sample_exp = category_dir / "EXP-20260720-0001.md"
        sample_content = """---
id: "EXP-20260720-0001"
title: "Initial test experience"
description: "Trigger when running automated tests."
domain: "test-domain"
keywords:
  - test
  - sample
complexity: "low"
created_at: "2026-07-20"
---

## 1. Objective
Run unit tests successfully.

## 2. The Trap
Failing to isolate test directory state.

## 3. Abstracted Insight
> **Core Principle:** Always use isolated temporary directories for file system tests.

## 4. Validated Path
Use tempfile.mkdtemp() in setUp and cleanup in tearDown.

## 5. Verification Checklist
- [ ] Verify clean test run.
"""
        sample_exp.write_text(sample_content, encoding="utf-8")

        # Patch experiences.EXPERIENCES_DIR and INDEX_PATH
        experiences.EXPERIENCES_DIR = self.experiences_dir
        experiences.INDEX_PATH = self.index_path

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir)

    def test_list_categories(self):
        captured_output = io.StringIO()
        sys.stdout = captured_output
        experiences.cmd_list_categories(None)
        sys.stdout = sys.__stdout__

        data = yaml.safe_load(captured_output.getvalue())
        self.assertIn("categories", data)
        self.assertEqual(len(data["categories"]), 1)
        self.assertEqual(data["categories"][0]["id"], "test-domain")

    def test_get_frontmatter(self):
        class Args:
            category = "test-domain"

        captured_output = io.StringIO()
        sys.stdout = captured_output
        experiences.cmd_get_frontmatter(Args())
        sys.stdout = sys.__stdout__

        data = yaml.safe_load(captured_output.getvalue())
        self.assertIn("experiences", data)
        self.assertEqual(len(data["experiences"]), 1)
        self.assertEqual(data["experiences"][0]["id"], "EXP-20260720-0001")
        self.assertEqual(data["experiences"][0]["title"], "Initial test experience")

    def test_read_experience(self):
        class Args:
            id = "EXP-20260720-0001"

        captured_output = io.StringIO()
        sys.stdout = captured_output
        experiences.cmd_read_experience(Args())
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("EXP-20260720-0001", output)
        self.assertIn("Core Principle:", output)

    def test_create_experience(self):
        class Args:
            domain = "test-domain"
            title = "New generated experience"
            description = "Trigger when creating a new experience via CLI."
            keywords = "cli, generate, new"
            complexity = "medium"
            objective = "Test creation of experience file."
            trap = "Missing index update."
            insight = "Always append new links to INDEX.md."
            validated_path = "Execute cmd_create_experience."
            checklist_item = "Verify file exists."

        captured_output = io.StringIO()
        sys.stdout = captured_output
        experiences.cmd_create_experience(Args())
        sys.stdout = sys.__stdout__

        # Verify new experience file created
        files = list((self.experiences_dir / "test-domain").glob("EXP-*-0002.md"))
        self.assertEqual(len(files), 1)

        content = files[0].read_text(encoding="utf-8")
        self.assertIn("New generated experience", content)
        self.assertIn("Always append new links to INDEX.md.", content)

        # Verify INDEX.md updated
        index_text = self.index_path.read_text(encoding="utf-8")
        self.assertIn("EXP-", index_text)
        self.assertIn("New generated experience", index_text)


if __name__ == "__main__":
    unittest.main()
