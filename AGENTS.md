# AGENTS.md - Open Reasoning Format (ORF)

## Project Overview

The **Open Reasoning Format (ORF)** (Version 0.1.0) is a file-based memory and experience retrieval architecture for AI agents. It enables progressive disclosure of procedural playbooks, abstracted heuristics, and execution traps without requiring vector databases or runtime server infrastructure.

For detailed specification guidelines, refer to [SPECIFICATION.md](SPECIFICATION.md) and [README.md](README.md).

---

## Directory & File Structure

```text
.
├── AGENTS.md                              # AI agent operational guidelines
├── README.md                              # Project overview and CLI guide
├── SPECIFICATION.md                       # Full ORF v0.1.0 Specification
├── requirements.txt                        # Python dependencies (PyYAML)
├── experiences/
│   ├── INDEX.md                           # Category index with YAML frontmatter
│   └── <domain>/                          # Hyphenated domain directories (e.g., python-scripting)
│       └── EXP-<YYYYMMDD>-<sequence>.md   # Standalone experience playbooks
├── manage-experience/
│   ├── SKILL.md                           # Agent Skill Specification (agentskills.io)
│   └── scripts/
│       └── experiences.py                 # Reference Python CLI helper script
└── tests/
    └── test_experiences.py                # Automated test suite
```

---

## Commands & Tooling

### Setup & Dependencies

Python 3.10+ and `PyYAML>=6.0` are required. Use `uv` or `pip`:

```bash
# Using uv (recommended)
uv run --with pyyaml python3 -m unittest discover -s tests

# Or using pip / virtualenv
pip install -r requirements.txt
python3 -m unittest discover -s tests
```

### Reference CLI Usage (`manage-experience/scripts/experiences.py`)

Agents interact with the `./experiences` directory via `experiences.py`:

```bash
# 1. List available domain categories
python3 manage-experience/scripts/experiences.py list-categories

# 2. Inspect experience metadata in a category
python3 manage-experience/scripts/experiences.py get-frontmatter --category python-scripting

# 3. Read full experience playbook by ID
python3 manage-experience/scripts/experiences.py read-experience --id EXP-20260720-0001

# 4. Record a new experience playbook
python3 manage-experience/scripts/experiences.py create-experience \
  --domain "<domain-id>" \
  --title "<Title>" \
  --description "<Trigger condition>" \
  --keywords "kw1,kw2" \
  --complexity "medium" \
  --objective "<Task objective>" \
  --trap "<Failure mode or trap>" \
  --insight "<Core Principle>" \
  --validated-path "<Resolution path>" \
  --checklist-item "<Verification step>"
```

---

## Code & Data Conventions

### 1. Experience Files (`EXP-<YYYYMMDD>-<sequence>.md`)

All experience files in `experiences/<domain>/` MUST:
- Be named following the pattern `EXP-<YYYYMMDD>-<sequence>.md` (e.g., `EXP-20260720-0001.md`).
- Contain YAML frontmatter with `id`, `title`, `description`, `domain`, `keywords`, `complexity`, and `created_at`.
- Include all five mandatory Markdown sections in order:
  1. `## 1. Objective`
  2. `## 2. The Trap`
  3. `## 3. Abstracted Insight` (starting with `> **Core Principle:** ...`)
  4. `## 4. Validated Path`
  5. `## 5. Verification Checklist`

### 2. Category Index (`experiences/INDEX.md`)

- `experiences/INDEX.md` MUST maintain YAML frontmatter with `spec_version: "0.1"`, `last_updated`, and a list of `categories`.
- Frontmatter MUST be parsed using line-anchored regex delimiters (`^---\s*$`) to prevent string splitting errors on inline `---` occurrences.

### 3. Agent Skill (`manage-experience/SKILL.md`)

- Conforms to the `agentskills.io` specification.
- Instructs host agents to perform **Phase 1 (Progressive Discovery & Retrieval)** before complex execution, and **Phase 2 (Post-Task Learning & Experience Recording)** after resolving complex traps.

---

## Testing & Verification

Always run unit tests when modifying `experiences.py`, `INDEX.md`, or schema definitions:

```bash
uv run --with pyyaml python3 -m unittest discover -s tests
```
