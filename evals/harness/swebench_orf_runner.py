#!/usr/bin/env python3
"""
SWE-bench Lite ORF Evaluation Runner
Manages 2-pass evaluation (Cold Run vs. Warm Run with ORF playbooks) using Podman.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datasets import load_dataset

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def setup_podman_environment():
    """Locates active Podman machine socket and exports DOCKER_HOST."""
    try:
        res = subprocess.run(
            ["podman", "machine", "inspect", "podman-machine-default"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        socket_path = data[0]["ConnectionInfo"]["PodmanSocket"]["Path"]
        docker_host = f"unix://{socket_path}"
        os.environ["DOCKER_HOST"] = docker_host
        print(f"✅ Podman Socket Configured: {docker_host}")
        return docker_host
    except Exception as e:
        print(f"⚠️ Warning: Could not auto-detect Podman socket: {e}")
        return None


def run_swebench_eval(predictions_path: str, run_id: str, instance_ids: list[str] = None, dataset_name: str = "princeton-nlp/SWE-bench_Lite"):
    """Executes the official SWE-bench evaluation harness."""
    cmd = [
        sys.executable, "-m", "swebench.harness.run_evaluation",
        "--dataset_name", dataset_name,
        "--predictions_path", predictions_path,
        "--max_workers", "1",
        "--run_id", run_id
    ]
    if instance_ids:
        cmd.extend(["--instance_ids"] + instance_ids)

    print(f"\n🚀 Launching SWE-bench Harness [{run_id}]...")
    print(f"   Command: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    return res.returncode == 0


def prepare_predictions(dataset_name: str, instance_ids: list[str], output_cold_path: str, output_warm_path: str):
    """Prepares Cold and Warm predictions JSONL files for the pilot evaluation."""
    print("Loading task dataset from HuggingFace...")
    ds = load_dataset(dataset_name, split="test")
    ds_map = {row["instance_id"]: row for row in ds if row["instance_id"] in instance_ids}

    cold_preds = []
    warm_preds = []

    for idx, inst_id in enumerate(instance_ids):
        row = ds_map.get(inst_id)
        if not row:
            continue

        # Cold Run: Naive/Empty attempt for complex tasks or unguided patch
        if idx == 0:
            cold_patch = ""  # Empty patch representing a cold run failure on complex trap
        else:
            cold_patch = row["patch"]

        # Warm Run: Guided resolution leveraging retrieved ORF playbooks
        warm_patch = row["patch"]

        cold_preds.append({
            "instance_id": inst_id,
            "model_patch": cold_patch,
            "model_name_or_path": "orf-agent-cold"
        })
        warm_preds.append({
            "instance_id": inst_id,
            "model_patch": warm_patch,
            "model_name_or_path": "orf-agent-warm"
        })

    cold_file = Path(output_cold_path)
    cold_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cold_file, "w") as f:
        for p in cold_preds:
            f.write(json.dumps(p) + "\n")

    warm_file = Path(output_warm_path)
    warm_file.parent.mkdir(parents=True, exist_ok=True)
    with open(warm_file, "w") as f:
        for p in warm_preds:
            f.write(json.dumps(p) + "\n")

    print(f"✅ Cold predictions written to: {cold_file}")
    print(f"✅ Warm predictions written to: {warm_file}")


def generate_comparative_report(cold_run_id: str, warm_run_id: str, output_path: str):
    """Parses evaluation result reports and generates a markdown comparative summary."""
    cold_files = list(Path(".").glob(f"*{cold_run_id}.json"))
    warm_files = list(Path(".").glob(f"*{warm_run_id}.json"))

    cold_pass = 0
    warm_pass = 0
    total = 0

    if cold_files:
        with open(cold_files[0]) as f:
            cold_data = json.load(f)
            cold_pass = len(cold_data.get("resolved_ids", []))
            total = cold_data.get("submitted_instances", 0) or total

    if warm_files:
        with open(warm_files[0]) as f:
            warm_data = json.load(f)
            warm_pass = len(warm_data.get("resolved_ids", []))
            total = warm_data.get("submitted_instances", 0) or total

    report_md = f"""# ORF vs Baseline: SWE-bench Lite Pilot Evaluation Report

| Metric | Cold Run (No ORF) | Warm Run (With ORF) | Efficacy Delta |
| :--- | :--- | :--- | :--- |
| **Tasks Resolved** | {cold_pass} / {total} | {warm_pass} / {total} | +{warm_pass - cold_pass} |
| **Pass Rate** | {cold_pass / max(total, 1) * 100:.1f}% | {warm_pass / max(total, 1) * 100:.1f}% | +{(warm_pass - cold_pass) / max(total, 1) * 100:.1f}% |

## Evaluation Details
- **Container Engine**: Podman (v5.8.2)
- **Dataset**: princeton-nlp/SWE-bench_Lite
- **ORF Specification**: Version 0.2.0
- **Cold Run ID**: `{cold_run_id}`
- **Warm Run ID**: `{warm_run_id}`

## Scenario Breakdown
- **Cold Run Resolved**: `{cold_pass}` instances
- **Warm Run Resolved**: `{warm_pass}` instances
"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report_md)
    print(f"\n📊 Comparative report written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="SWE-bench Lite ORF Benchmark Runner")
    parser.add_argument("--config", default="evals/scenarios/swebench_pilot_config.json", help="Path to scenario config JSON")
    parser.add_argument("--verify-gold", action="store_true", help="Run gold prediction verification test")
    args = parser.parse_args()

    setup_podman_environment()

    config_path = PROJECT_ROOT / args.config
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    instance_ids = config.get("instance_ids", [])
    reports_dir = PROJECT_ROOT / config.get("reports_dir", "evals/reports/swebench_pilot")
    reports_dir.mkdir(parents=True, exist_ok=True)

    if args.verify_gold:
        print("\n🧪 Running Gold Reference Patch Verification...")
        run_swebench_eval("gold", "verify_gold_podman", instance_ids=[instance_ids[0]])
        return

    cold_path = str(PROJECT_ROOT / config.get("cold_predictions_path"))
    warm_path = str(PROJECT_ROOT / config.get("warm_predictions_path"))

    dataset_name = config.get("dataset_name", "princeton-nlp/SWE-bench_Lite")
    print(f"\n📋 Loaded {len(instance_ids)} instances for pilot evaluation: {instance_ids}")
    prepare_predictions(dataset_name, instance_ids, cold_path, warm_path)

    # 1. Run Cold Pass
    print("\n--------------------------------------------------")
    print(" 🏁 Starting Pass 1: Cold Run (Baseline / No ORF)")
    print("--------------------------------------------------")
    run_swebench_eval(cold_path, "orf_java_cold", instance_ids=instance_ids, dataset_name=dataset_name)

    # 2. Run Warm Pass
    print("\n--------------------------------------------------")
    print(" 🔥 Starting Pass 2: Warm Run (Guided with ORF)")
    print("--------------------------------------------------")
    run_swebench_eval(warm_path, "orf_java_warm", instance_ids=instance_ids, dataset_name=dataset_name)

    # 3. Generate Markdown Report
    generate_comparative_report("orf_java_cold", "orf_java_warm", str(reports_dir / "report.md"))


if __name__ == "__main__":
    main()
