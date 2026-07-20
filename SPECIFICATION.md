# Specification: Open Reasoning Format (ORF)

- **Version:** 0.1.0
- **Status:** Draft
- **Scope:** File-based cognitive architecture for AI agent experience retrieval and progressive disclosure.

---

## 1. Overview

The Open Reasoning Format (ORF) defines a file-based memory architecture for AI agents. ORF synthesizes principles from three core AI paradigms:

- **The Reasoning Bank paper (Google):** For storing procedural knowledge, abstracted heuristics, and execution traps learned through experience.
- **Open Knowledge Format (OKF):** For human-readable, token-optimized, structured Markdown and YAML documentation.
- **Agent Skills Specification:** For enabling progressive disclosure and zero-runtime indirection layers.

ORF relies strictly on local file I/O within the workspace (`./experiences`). It operates without runtime server components (such as vector databases) and without direct intervention in host version control systems (such as Git).

---

## 2. Directory Layout

All reasoning bank assets **MUST** reside within a root directory named `experiences/` located at the project root:

```text
<project-root>/
└── experiences/
    ├── INDEX.md
    └── <domain>/
        └── EXP-<YYYYMMDD>-<sequence>.md
```

- **`INDEX.md`**: The root entry point containing category metadata and links to individual experience records.
- **`<domain>/`**: A lower-case, hyphenated directory grouping experiences by domain (e.g., `cloud-run`, `data-analytics`, `python-scripting`).
- **`EXP-<YYYYMMDD>-<sequence>.md`**: An individual experience file featuring a date-based prefix (e.g., `EXP-20260720-0001.md`).

---

## 3. Data Schema Specifications

### 3.1. Category Index (`INDEX.md`)

The `INDEX.md` file acts as the primary indirection layer. It **MUST** contain a YAML frontmatter block defining the domain categories, followed by a Markdown body mapping categories to individual experience files.

#### Schema

```markdown
---
spec_version: "0.1"
last_updated: "YYYY-MM-DD"
categories:
  - id: "<domain-id>"
    name: "<Display Name>"
    description: "<A concise, 1-2 sentence description of problems falling under this domain. Used by agents during Layer 1 routing.>"
---

# Experiences Index

## Category: <Display Name> (`<domain-id>`)
* [EXP-<YYYYMMDD>-<sequence>](<domain-id>/EXP-<YYYYMMDD>-<sequence>.md): <One line summary of the insight or trap.>
```

---

### 3.2. Experience File (`EXP-<YYYYMMDD>-<sequence>.md`)

Each experience entry **MUST** be a standalone Markdown file containing YAML frontmatter and five mandatory Markdown sections.

#### Schema

```markdown
---
id: "EXP-<YYYYMMDD>-<sequence>"
title: "<Short, imperative title describing the learned capability>"
description: "<Detailed trigger conditions describing WHEN an agent should load this experience file. Max 1024 chars.>"
domain: "<domain-id>"
keywords: [<keyword1>, <keyword2>, ...]
complexity: "low" | "medium" | "high"
created_at: "YYYY-MM-DD"
---

## 1. Objective
<Description of the task or prompt that initiated the experience.>

## 2. The Trap
<Description of the naive attempt, edge case, error message, or failure mode encountered.>

## 3. Abstracted Insight
> **Core Principle:** <Generalized, domain-agnostic heuristic derived from the experience.>

## 4. Validated Path
<Step-by-step resolution path, code snippet, or tool sequence that successfully solved the problem.>

## 5. Verification Checklist
- [ ] <Checklist item to verify successful execution in future runs>
```

---

## 4. Agent Skill Specification (`manage-experience/SKILL.md`)

To enable agent interaction with the `experiences` directory, the host agent framework **MUST** include the `manage-experience` skill, compliant with the `agentskills.io` specification.

### File Structure

```text
manage-experience/
├── SKILL.md
└── scripts/
    └── experiences.py
```

### `manage-experience/SKILL.md`

```markdown
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
```

---

## 5. Reference Script Implementation

The helper script `manage-experience/scripts/experiences.py` handles deterministic file I/O operations, ensuring schema validity and preventing syntax corruption in `INDEX.md` and experience files.

```python
#!/usr/bin/env python3
"""
ORF Reference Implementation Helper Script
Handles reading, parsing, writing, and indexing for Open Reasoning Format files.
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path
import yaml

EXPERIENCES_DIR = Path("./experiences")
INDEX_PATH = EXPERIENCES_DIR / "INDEX.md"


def parse_frontmatter(content):
    """
    Safely split frontmatter and body by line-anchored '---' delimiters.
    Returns (frontmatter_dict, body_str).
    """
    parts = re.split(r"^---\s*$", content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        return None, content
    
    try:
        fm = yaml.safe_load(parts[1])
        return fm, parts[2]
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to parse YAML frontmatter: {e}\n")
        return None, parts[2]


def load_index():
    if not INDEX_PATH.exists():
        sys.stderr.write("Error: ./experiences/INDEX.md not found.\n")
        sys.exit(1)
    
    content = INDEX_PATH.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    if frontmatter is None:
        sys.stderr.write("Error: Invalid YAML frontmatter in INDEX.md\n")
        sys.exit(1)
        
    return frontmatter, body, content


def cmd_list_categories(args):
    frontmatter, _, _ = load_index()
    categories = frontmatter.get("categories", [])
    print(yaml.dump({"categories": categories}, sort_keys=False))


def cmd_get_frontmatter(args):
    category = args.category
    category_dir = EXPERIENCES_DIR / category
    
    if not category_dir.exists():
        sys.stderr.write(f"Error: Category directory {category_dir} does not exist.\n")
        sys.exit(1)
        
    results = []
    for filepath in category_dir.glob("EXP-*.md"):
        content = filepath.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(content)
        if fm:
            results.append({
                "id": fm.get("id"),
                "title": fm.get("title"),
                "description": fm.get("description"),
                "keywords": fm.get("keywords", []),
                "file_path": str(filepath)
            })
            
    print(yaml.dump({"experiences": results}, sort_keys=False))


def cmd_read_experience(args):
    exp_id = args.id
    target_file = None
    
    for filepath in EXPERIENCES_DIR.rglob(f"{exp_id}.md"):
        target_file = filepath
        break
        
    if not target_file or not target_file.exists():
        sys.stderr.write(f"Error: Experience file for ID {exp_id} not found.\n")
        sys.exit(1)
        
    print(target_file.read_text(encoding="utf-8"))


def cmd_create_experience(args):
    frontmatter, body, full_index_content = load_index()
    
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")  # YYYYMMDD
    category_dir = EXPERIENCES_DIR / args.domain
    category_dir.mkdir(parents=True, exist_ok=True)
    
    existing_files = list(category_dir.glob(f"EXP-{date_str}-*.md"))
    seq = len(existing_files) + 1
    exp_id = f"EXP-{date_str}-{seq:04d}"
    
    file_path = category_dir / f"{exp_id}.md"
    
    fm_data = {
        "id": exp_id,
        "title": args.title,
        "description": args.description,
        "domain": args.domain,
        "keywords": [k.strip() for k in args.keywords.split(",") if k.strip()],
        "complexity": args.complexity,
        "created_at": datetime.date.today().isoformat()
    }
    
    md_content = f"""---
{yaml.dump(fm_data, sort_keys=False)}---

## 1. Objective
{args.objective}

## 2. The Trap
{args.trap}

## 3. Abstracted Insight
> **Core Principle:** {args.insight}

## 4. Validated Path
{args.validated_path}

## 5. Verification Checklist
- [ ] {args.checklist_item}
"""

    file_path.write_text(md_content, encoding="utf-8")
    
    # Append entry to INDEX.md
    new_entry = f"* [{exp_id}]({args.domain}/{exp_id}.md): {args.title}\n"
    
    updated_index = full_index_content
    category_marker = f"({args.domain})"
    
    if category_marker in updated_index:
        lines = updated_index.splitlines(keepends=True)
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if category_marker in line and not inserted:
                new_lines.append(new_entry)
                inserted = True
        updated_index = "".join(new_lines)
    else:
        updated_index += f"\n\n## Category: {args.domain.replace('-', ' ').title()} (`{args.domain}`)\n{new_entry}"
        
    INDEX_PATH.write_text(updated_index, encoding="utf-8")
    print(f"Successfully created experience record {exp_id} at {file_path}")


def main():
    parser = argparse.ArgumentParser(description="ORF Experiences Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    subparsers.add_parser("list-categories")
    
    cmd_fm = subparsers.add_parser("get-frontmatter")
    cmd_fm.add_argument("--category", required=True, help="Domain category ID")
    
    cmd_read = subparsers.add_parser("read-experience")
    cmd_read.add_argument("--id", required=True, help="Experience ID (e.g., EXP-20260720-0001)")
    
    cmd_create = subparsers.add_parser("create-experience")
    cmd_create.add_argument("--domain", required=True)
    cmd_create.add_argument("--title", required=True)
    cmd_create.add_argument("--description", required=True)
    cmd_create.add_argument("--keywords", required=True, help="Comma-separated keywords")
    cmd_create.add_argument("--complexity", choices=["low", "medium", "high"], default="medium")
    cmd_create.add_argument("--objective", required=True)
    cmd_create.add_argument("--trap", required=True)
    cmd_create.add_argument("--insight", required=True)
    cmd_create.add_argument("--validated-path", required=True)
    cmd_create.add_argument("--checklist-item", default="Verify fix in target runtime environment.")
    
    args = parser.parse_args()
    
    if args.command == "list-categories":
        cmd_list_categories(args)
    elif args.command == "get-frontmatter":
        cmd_get_frontmatter(args)
    elif args.command == "read-experience":
        cmd_read_experience(args)
    elif args.command == "create-experience":
        cmd_create_experience(args)


if __name__ == "__main__":
    main()
```

---

## 6. Execution Lifecycle Sequence

```text
[ User Prompt ]
      │
      ▼
[ Agent Context Initialization ]
      │
      ├──> Calls: `manage-experience/scripts/experiences.py list-categories`
      │    Returns: High-level category list (~200 tokens)
      │
      ├──> Matches Category? 
      │    ├─ YES ──> Calls: `manage-experience/scripts/experiences.py get-frontmatter --category <domain>`
      │    │          Returns: Frontmatter metadata for domain playbooks (~500 tokens)
      │    └─ NO  ──> Proceed to Task Execution
      │
      ├──> Matches Specific Experience?
      │    └─ YES ──> Calls: `manage-experience/scripts/experiences.py read-experience --id EXP-<YYYYMMDD>-<sequence>`
      │               Returns: Full playbook body (~800 tokens)
      │
      ▼
[ Task Execution Phase ]
 (Agent applies lessons learned or resolves new complex problem)
      │
      ▼
[ Post-Task Learning Phase ]
      │
      └──> Discovered new heuristic/trap?
           └─ YES ──> Calls: `manage-experience/scripts/experiences.py create-experience ...`
                      Result: Local `./experiences` updated; developer can review via `git status`
```
