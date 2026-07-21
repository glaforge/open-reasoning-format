# Open Reasoning Format (ORF) Evaluation Framework

The **ORF Evaluation Framework** provides an empirical, automated testbed for evaluating AI agent trajectories. It measures whether reading past experience playbooks (Phase 1) reduces agent step counts and eliminates debugging loops, and verifies whether agents successfully record compliant operational playbooks (Phase 2) when resolving new traps.

---

## 📁 Directory Structure

```text
evals/
├── README.md               # Framework documentation & scenario authoring guide
├── runner.py               # Benchmark CLI runner (supports --dry-run and --agy)
├── run_live_subagent.py    # Live subagent execution wrapper
├── harness/                # Core evaluation engine
│   ├── agy_driver.py       # Integration driver for local Antigravity (`agy`) CLI
│   ├── evaluator.py        # Trajectory result aggregator & report builder
│   ├── sandbox.py          # Temporary workspace manager with isolated environment setup
│   └── spec_validator.py   # Automated ORF schema & frontmatter compliance validator
├── scenarios/              # Benchmark scenario definitions
│   ├── atomic-writer/      # Atomic JSON state writing scenario
│   ├── frontmatter-parser/ # Markdown YAML frontmatter mutator scenario
│   ├── langchain4j-gemini/ # Java LangChain4j & Gemini Maven setup scenario
│   └── subprocess-pipe/    # Non-blocking subprocess pipe streaming scenario
├── reports/                # Exported Markdown and JSON evaluation matrices
└── workspaces/             # Temporary runtime execution sandboxes (gitignored)
```

---

## 🔄 3-Stage Evaluation Pipeline

The benchmark runner evaluates scenarios across three distinct stages to quantify learning and retrieval efficacy:

```text
[ Stage 1: Cold Run ]       -->       [ Stage 2: Spec Validation ]       -->       [ Stage 3: Warm Run ]
Without Prior Experience                Validate New EXP-*.md File                 With Newly Minted EXP
- Baseline steps & errors               - Checks 7 frontmatter fields              - Evaluates Phase 1 retrieval
- Tests Phase 2 recording               - Audits 5 required sections               - Measures step reduction &
  (`create-experience`)                 - Confirms INDEX.md update                   first-attempt trap avoidance
```

1. **Stage 1 (Cold Run - Baseline)**: An agent attempts a scenario without prior experience playbooks. If it encounters and resolves a trap, we test whether it automatically triggers **Phase 2** (`create-experience`) to record a new playbook.
2. **Stage 2 (Spec Validation)**: An automated validator (`spec_validator.py`) audits any dynamically generated `EXP-*.md` file against the 7 required YAML frontmatter fields and 5 mandatory Markdown headers.
3. **Stage 3 (Warm Run - Accelerated Execution)**: A fresh agent context attempts the scenario with the newly recorded playbook available. We evaluate **Phase 1** retrieval (`manage-experience`), first-attempt trap avoidance, and percentage step count reduction.

---

## 🛠️ Running Evaluations

The evaluation runner supports both dry-run simulation mode (for verifying harness logic) and live execution mode using the local `agy` (Antigravity CLI) binary.

### 1. Dry-Run Verification Mode

Runs the 3-stage pipeline using simulated agent outputs to verify sandbox setup and test logic:

```bash
# Run all benchmark scenarios in dry-run mode
python3 evals/runner.py --dry-run

# Run a specific benchmark scenario
python3 evals/runner.py --scenario frontmatter-parser --dry-run
```

### 2. Live Agent Benchmarks (`agy`)

Executes live AI agent trials using the local `agy` binary:

```bash
python3 evals/runner.py --agy
```

### 3. Exporting Evaluation Reports

Export comparative Markdown tables or JSON matrices:

```bash
python3 evals/runner.py --dry-run \
  --export-markdown evals/reports/dry_run_report.md \
  --export-json evals/reports/dry_run_report.json
```

---

## ✍️ Scenario Authoring Guide

To add a new benchmark scenario to the evaluation harness, create a directory under `evals/scenarios/<scenario-id>/` containing two required files: `problem.md` and `test_verify.py`.

### Step 1: Create `evals/scenarios/<scenario-id>/problem.md`

Define the goal, requirements, and operational trap presented to the agent:

```markdown
# Scenario Task: <Title>

## Goal
<Description of task goal>

## Requirements
1. <Requirement 1>
2. <Requirement 2>

## The Operational Trap
<Description of the naive attempt or trap that causes failure or debugging loops>
```

### Step 2: Create `evals/scenarios/<scenario-id>/test_verify.py`

Implement a `verify_scenario(workspace_dir: Path) -> dict` entry point that checks whether the agent's solution avoided the trap and succeeded:

```python
#!/usr/bin/env python3
"""
Verification suite for scenario: <scenario-id>
"""

from pathlib import Path

def verify_scenario(workspace_dir: Path) -> dict:
    """
    Evaluates workspace result after scenario run.
    Must return a dictionary with the following keys:
    """
    # 1. Inspect workspace outputs
    solution_file = workspace_dir / "my_solution.py"
    
    success = solution_file.exists()
    trap_avoided = False  # Set based on code analysis or runtime test
    
    # 2. Check if agent recorded a new experience file (Phase 2)
    exp_files = list((workspace_dir / "experiences").rglob("EXP-*.md"))
    recorded_new_exp = len(exp_files) > 0
    
    exp_spec_valid = False
    if recorded_new_exp:
        # Import spec validator to verify schema
        import sys
        harness_dir = Path(__file__).resolve().parent.parent.parent / "harness"
        sys.path.insert(0, str(harness_dir))
        import spec_validator
        
        validation = spec_validator.validate_experience_file(exp_files[0])
        exp_spec_valid = validation["valid"]

    return {
        "success": success,
        "trap_avoided": trap_avoided,
        "recorded_new_exp": recorded_new_exp,
        "exp_spec_valid": exp_spec_valid,
        "details": "Scenario verification completed."
    }
```

### Step 3: Register Scenario in `evals/runner.py`

Add the scenario ID and corresponding ORF experience ID mapping to `SCENARIO_EXP_MAP` in `evals/runner.py`:

```python
SCENARIO_EXP_MAP = {
    "frontmatter-parser": "EXP-20260720-0001",
    "atomic-writer": "EXP-20260720-0002",
    "subprocess-pipe": "EXP-20260720-0003",
    "langchain4j-gemini": "EXP-20260721-0001",
    "<scenario-id>": "EXP-YYYYMMDD-XXXX",
}
```

---

## 🔍 Spec Validator Rules (`harness/spec_validator.py`)

The spec validator enforces compliance against **ORF Specification v0.1.0**:

1. **Required Frontmatter Keys**: `id`, `title`, `description`, `domain`, `keywords`, `complexity`, `created_at`.
2. **Required Markdown Headers (in exact sequence)**:
   - `## 1. Objective`
   - `## 2. The Trap`
   - `## 3. Abstracted Insight`
   - `## 4. Validated Path`
   - `## 5. Verification Checklist`
3. **Core Principle Requirement**: The `## 3. Abstracted Insight` section MUST begin with a blockquote formatted as `> **Core Principle:** ...`.

---

## 🧪 Testing Harness Logic

Run unit tests covering `spec_validator` and harness utilities:

```bash
python3 -m unittest discover -s tests
```
