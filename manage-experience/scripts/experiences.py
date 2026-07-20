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
