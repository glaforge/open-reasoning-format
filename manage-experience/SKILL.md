---
name: manage-experience
description: Dynamically routes, retrieves, and records procedural playbooks from the local `./experiences` folder. Use at the start of complex tasks to consult past experience, and at the end of a successful execution to record new operational learnings.
license: Apache-2.0
compatibility: Requires local file-system read/write permissions and Python 3.10+
metadata:
  version: "0.1.0"
  spec_format: "ORF-0.1"
---

# Instructions

You interact with the local `./experiences` folder to load past operational heuristics and record new ones.

## Phase 1: Progressive Discovery & Retrieval
1. Execute `python3 manage-experience/scripts/experiences.py list-categories` to view available domain categories.
2. If your task matches a category description, run `python3 manage-experience/scripts/experiences.py get-frontmatter --category <domain-id>` to inspect matching experience descriptions.
3. If an experience description explicitly matches your current problem or trap, run `python3 manage-experience/scripts/experiences.py read-experience --id EXP-<YYYYMMDD>-<sequence>`.
4. Incorporate the "Abstracted Insight" and "Validated Path" into your active execution context.

## Phase 2: Recording New Experiences
If you resolve a complex task that involved a multi-step debugging loop, an unexpected trap, or a domain-specific workaround:
1. Run `python3 manage-experience/scripts/experiences.py create-experience` with the required parameters to write the new experience file and automatically update `INDEX.md`.
