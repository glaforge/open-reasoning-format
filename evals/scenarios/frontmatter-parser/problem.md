# Scenario Task: Frontmatter-Preserving Index Mutator

## Goal
Create a Python script named `update_index.py` inside the current workspace.

## Requirements
1. `update_index.py` must take a category name and entry text as arguments (or via function `add_index_entry(category: str, title: str, path: str)`).
2. It must parse the workspace `experiences/INDEX.md` file.
3. It must insert a new markdown bullet point item under the matching category section without corrupting or destroying the YAML frontmatter header block (`---`).
4. The YAML frontmatter metadata at the top of `experiences/INDEX.md` must remain intact and valid YAML.

## The Operational Trap
Simple string concatenation or naive file append (`open("INDEX.md", "a")`) appends the content at the very bottom or corrupts `---` frontmatter delimiters, breaking metadata parsers expecting valid YAML at the top.
