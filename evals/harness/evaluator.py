#!/usr/bin/env python3
"""
ORF Trajectory Evaluator & Metric Aggregator
Tracks trajectory execution metrics, compares A/B condition performance, and formats evaluation reports.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TrajectoryResult:
    scenario_id: str
    condition: str  # "Cold" (Baseline), "Phase2_Creation", "Warm" (With ORF)
    success: bool
    trap_avoided: bool
    step_count: int
    error_count: int
    recorded_new_experience: bool = False
    valid_new_experience_spec: bool = False
    details: str = ""


class TrajectoryEvaluator:
    def __init__(self):
        self.results: list[TrajectoryResult] = []

    def record_result(self, result: TrajectoryResult):
        self.results.append(result)

    def compute_summary(self) -> dict:
        scenarios = sorted(list({r.scenario_id for r in self.results}))
        summary = {}

        for scenario in scenarios:
            sc_results = [r for r in self.results if r.scenario_id == scenario]
            cold_run = next((r for r in sc_results if r.condition == "Cold"), None)
            phase2_run = next((r for r in sc_results if r.condition == "Phase2_Creation"), None)
            warm_run = next((r for r in sc_results if r.condition == "Warm"), None)

            summary[scenario] = {
                "cold_run": asdict(cold_run) if cold_run else None,
                "phase2_creation": asdict(phase2_run) if phase2_run else None,
                "warm_run": asdict(warm_run) if warm_run else None,
                "step_reduction_pct": (
                    round((cold_run.step_count - warm_run.step_count) / cold_run.step_count * 100, 1)
                    if cold_run and warm_run and cold_run.step_count > 0
                    else 0.0
                ),
                "error_reduction_pct": (
                    round((cold_run.error_count - warm_run.error_count) / max(cold_run.error_count, 1) * 100, 1)
                    if cold_run and warm_run
                    else 0.0
                ),
            }
        return summary

    def generate_markdown_report(self) -> str:
        summary = self.compute_summary()
        lines = [
            "# ORF Trajectory Evaluation Report",
            "",
            "| Scenario | Cold Success | Cold Steps | Warm Success | Warm Steps | Step Reduction | Phase 2 EXP Created | EXP Spec Valid |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"
        ]

        for sc_id, sc_data in summary.items():
            cold = sc_data.get("cold_run") or {}
            warm = sc_data.get("warm_run") or {}
            p2 = sc_data.get("phase2_creation") or {}

            cold_succ = "✅" if cold.get("success") else "❌"
            cold_steps = str(cold.get("step_count", "-"))
            warm_succ = "✅" if warm.get("success") else "❌"
            warm_steps = str(warm.get("step_count", "-"))
            step_red = f"{sc_data.get('step_reduction_pct', 0)}%"
            p2_created = "✅" if p2.get("recorded_new_experience") else "❌"
            p2_valid = "✅" if p2.get("valid_new_experience_spec") else "❌"

            lines.append(f"| `{sc_id}` | {cold_succ} | {cold_steps} | {warm_succ} | {warm_steps} | {step_red} | {p2_created} | {p2_valid} |")

        return "\n".join(lines)

    def export_report_json(self, target_path: Path):
        target_path.parent.mkdir(parents=True, exist_ok=True)
        summary = self.compute_summary()
        raw_results = [asdict(r) for r in self.results]
        target_path.write_text(
            json.dumps({"summary": summary, "raw_results": raw_results}, indent=2),
            encoding="utf-8"
        )

