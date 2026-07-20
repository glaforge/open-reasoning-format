# ORF Live AI Agent Trajectory Evaluation Report

*Evaluation Date: 2026-07-20*
*Agent Type: Antigravity Subagent (`orf_eval_agent`)*

## Trajectory Comparison Matrix

| Scenario | Cold Success | Cold Steps | Warm Success | Warm Steps | Step Reduction | Phase 2 EXP Created | EXP Spec Valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `frontmatter-parser` | ✅ | 25 | ✅ | 12 | **52.0%** | ✅ | ✅ |

---

## Detailed Scenario Logs

### Scenario: `frontmatter-parser`
- **Cold Run Workspace**: `evals/workspaces/frontmatter-parser_cold`
  - Subagent Conversation ID: `561914cc-76be-4985-963b-79dab6e0d1e6`
  - Outcome: Solved task in ~25 steps after debugging PyYAML string wrapping and regex delimiter edge cases.
  - Phase 2 Action: Triggered `experiences.py create-experience` to produce `EXP-20260720-0001.md`.
  - Spec Audit: `spec_validator.py` verified 100% compliance with ORF v0.1 format.

- **Warm Run Workspace**: `evals/workspaces/frontmatter-parser_warm`
  - Subagent Conversation ID: `f84d9028-b541-482f-a08e-c892f1de3fe1`
  - Outcome: Retrieved `EXP-20260720-0001.md` via Phase 1 discovery, cited playbook in code, and solved task on 1st attempt in 12 steps.
  - Trajectory Efficiency: **52% step reduction**, 0 debug error loops.
