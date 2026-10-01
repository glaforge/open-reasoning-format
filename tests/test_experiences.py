#!/usr/bin/env python3
"""
Unit tests for manage-experience/scripts/experiences.py helper script.
"""

import datetime
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

        self.today_str = datetime.datetime.now().strftime("%Y%m%d")
        self.sample_id = f"EXP-{self.today_str}-0001"

        # Setup mock experiences folder and INDEX.md
        self.experiences_dir = Path("./experiences")
        self.experiences_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.experiences_dir / "INDEX.md"
        initial_index = f"""---
spec_version: "0.2"
last_updated: "{datetime.date.today().isoformat()}"
categories:
  - id: "test-domain"
    name: "Test Domain"
    description: "Domain used for automated unit testing."
---

# Experiences Index

## Category: Test Domain (`test-domain`)
* [{self.sample_id}](test-domain/{self.sample_id}.md): Initial test experience.
"""
        self.index_path.write_text(initial_index, encoding="utf-8")

        # Create test category and sample file
        category_dir = self.experiences_dir / "test-domain"
        category_dir.mkdir(parents=True, exist_ok=True)

        sample_exp = category_dir / f"{self.sample_id}.md"
        sample_content = f"""---
id: "{self.sample_id}"
title: "Initial test experience"
description: "Trigger when running automated tests."
domain: "test-domain"
keywords:
  - test
  - sample
complexity: "low"
created_at: "{datetime.date.today().isoformat()}"
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
        self.assertEqual(data["experiences"][0]["id"], self.sample_id)
        self.assertEqual(data["experiences"][0]["title"], "Initial test experience")

    def test_read_experience(self):
        class Args:
            id = self.sample_id

        captured_output = io.StringIO()
        sys.stdout = captured_output
        experiences.cmd_read_experience(Args())
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn(self.sample_id, output)
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
            domain_title = None
            domain_description = None

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
        # Verify no duplicate category section
        self.assertEqual(index_text.count("## Category: Test Domain"), 1)

    def test_create_experience_new_category_registered_in_frontmatter(self):
        """Issue 1: A new category must be registered in INDEX.md frontmatter so list-categories can see it."""
        class Args:
            domain = "new-domain"
            title = "First card in new domain"
            description = "Trigger when in new domain."
            keywords = "new, category"
            complexity = "low"
            objective = "Test category registration."
            trap = "Category missing from frontmatter."
            insight = "Always register new domains in INDEX.md frontmatter."
            validated_path = "Insert category block before closing delimiter."
            checklist_item = "Verify list-categories output."
            domain_title = "New Domain"
            domain_description = "Special: description with 'colons' and quotes."

        experiences.cmd_create_experience(Args())
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        experiences.cmd_list_categories(None)
        sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        data = yaml.safe_load(output)
        category_ids = [c["id"] for c in data.get("categories", [])]
        self.assertIn("new-domain", category_ids)

        new_cat = next(c for c in data["categories"] if c["id"] == "new-domain")
        self.assertEqual(new_cat["name"], "New Domain")
        self.assertEqual(new_cat["description"], "Special: description with 'colons' and quotes.")

        # Verify Markdown section in INDEX.md
        index_text = self.index_path.read_text(encoding="utf-8")
        self.assertIn("## Category: New Domain (`new-domain`)", index_text)
        self.assertIn("First card in new domain", index_text)

    def test_checklist_item_multiple(self):
        """Issue 2: Multiple --checklist-item arguments should all be preserved."""
        class Args:
            domain = "test-domain"
            title = "Checklist test experience"
            description = "Trigger for checklist testing."
            keywords = "checklist, test"
            complexity = "low"
            objective = "Test multiple checklist items."
            trap = "Silent overwrite of previous items."
            insight = "Use action='append' to collect multiple checklist items."
            validated_path = "Join all checklist items."
            checklist_item = ["First verification item.", "Second verification item.", "Third item."]
            domain_title = None
            domain_description = None

        captured_output = io.StringIO()
        sys.stdout = captured_output
        experiences.cmd_create_experience(Args())
        sys.stdout = sys.__stdout__

        files = list((self.experiences_dir / "test-domain").glob("EXP-*-0002.md"))
        self.assertEqual(len(files), 1)
        content = files[0].read_text(encoding="utf-8")

        self.assertIn("- [ ] First verification item.", content)
        self.assertIn("- [ ] Second verification item.", content)
        self.assertIn("- [ ] Third item.", content)

    def test_no_duplicate_category_section(self):
        """Issue 3: Adding a card to an existing category must not create a duplicate section header."""
        class Args:
            domain = "test-domain"
            title = "Second card in existing category"
            description = "Trigger test."
            keywords = "duplicate, header"
            complexity = "low"
            objective = "Test non-duplication of category header."
            trap = "Mismatched marker formatting."
            insight = "Match both backtick and non-backtick markers."
            validated_path = "Check category_markers tuple."
            checklist_item = "Verify single header in INDEX.md."
            domain_title = None
            domain_description = None

        experiences.cmd_create_experience(Args())
        index_text = self.index_path.read_text(encoding="utf-8")
        self.assertEqual(index_text.count("## Category: Test Domain"), 1)

    def test_experience_id_no_collision_across_categories(self):
        """Issue 4: IDs must not collide when experiences are created across different categories on the same date."""
        class ArgsCatA:
            domain = "cat-a"
            title = "Card in Cat A"
            description = "Trigger."
            keywords = "a"
            complexity = "low"
            objective = "Obj A"
            trap = "Trap A"
            insight = "Insight A"
            validated_path = "Path A"
            checklist_item = "Check A"
            domain_title = None
            domain_description = None

        class ArgsCatB:
            domain = "cat-b"
            title = "Card in Cat B"
            description = "Trigger."
            keywords = "b"
            complexity = "low"
            objective = "Obj B"
            trap = "Trap B"
            insight = "Insight B"
            validated_path = "Path B"
            checklist_item = "Check B"
            domain_title = None
            domain_description = None

        # self.sample_id is EXP-<today>-0001 in test-domain
        experiences.cmd_create_experience(ArgsCatA())
        experiences.cmd_create_experience(ArgsCatB())

        file_a = list((self.experiences_dir / "cat-a").glob("EXP-*.md"))
        file_b = list((self.experiences_dir / "cat-b").glob("EXP-*.md"))

        self.assertEqual(len(file_a), 1)
        self.assertEqual(len(file_b), 1)

        self.assertTrue(file_a[0].name.endswith("-0002.md"), f"Expected 0002 for Cat A, got {file_a[0].name}")
        self.assertTrue(file_b[0].name.endswith("-0003.md"), f"Expected 0003 for Cat B, got {file_b[0].name}")


if __name__ == "__main__":
    unittest.main()
