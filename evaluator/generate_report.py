"""End-to-end evaluation pipeline / orchestrator.

For every patch in ``patches/`` this script:

  1. makes a clean copy of the sample repo,
  2. applies the patch,
  3. runs the test suite,
  4. diffs the result against the (cached) baseline run,
  5. classifies any regression,
  6. generates a root-cause hypothesis,

and finally writes:

  * ``results/<case>.json``   - machine-readable per-case result
  * ``results/summary.json``  - aggregate across all cases
  * ``reports/report.md``     - human-readable Markdown report

Run it with:  ``python evaluator/generate_report.py``
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a script (``python evaluator/generate_report.py``).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_patch import PROJECT_ROOT, SAMPLE_REPO, apply_patch, make_work_copy  # noqa: E402
from classify_failure import classify_failure  # noqa: E402
from detect_regression import detect_regression  # noqa: E402
from generate_hypothesis import generate_hypothesis  # noqa: E402
from run_tests import run_tests  # noqa: E402

PATCHES_DIR = PROJECT_ROOT / "patches"
RESULTS_DIR = PROJECT_ROOT / "results"
REPORTS_DIR = PROJECT_ROOT / "reports"


def run_baseline() -> dict:
    """Run the test suite on the unmodified sample repo."""
    work_dir = make_work_copy("_baseline")
    return run_tests(work_dir)


def evaluate_patch(patch_path: Path, baseline: dict) -> dict:
    case = patch_path.stem
    work_dir = make_work_copy(case)
    apply_result = apply_patch(patch_path, work_dir)

    if not apply_result["applied"]:
        patched = {
            "collected": False,
            "passed": 0,
            "failed": 0,
            "failed_tests": [],
            "failures": {},
            "note": "patch did not apply",
        }
    else:
        patched = run_tests(work_dir)

    regression = detect_regression(baseline, patched)
    classification = classify_failure(regression, patched)
    hypothesis = generate_hypothesis(classification, regression)

    return {
        "case": case,
        "patch_file": patch_path.name,
        "patch_applied": apply_result["applied"],
        "apply_detail": apply_result,
        "verdict": regression["verdict"],
        "regression": regression,
        "classification": classification,
        "hypothesis": hypothesis,
        "patched_summary": {
            "passed": patched.get("passed", 0),
            "failed": patched.get("failed", 0),
            "total": patched.get("total", 0),
            "failed_tests": patched.get("failed_tests", []),
        },
    }


def _write_markdown(baseline: dict, results: list[dict]) -> str:
    lines = ["# AI Reliability Platform - Evaluation Report", ""]
    lines.append(f"Baseline: **{baseline.get('passed', 0)} passed**, "
                 f"**{baseline.get('failed', 0)} failed** "
                 f"out of {baseline.get('total', 0)} tests.")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Case | Patch | Verdict | Failed tests | Category | Severity |")
    lines.append("|------|-------|---------|--------------|----------|----------|")
    for r in results:
        cls = r["classification"]
        hyp = r["hypothesis"]
        n_failed = len(r["regression"].get("newly_failing", []))
        lines.append(
            f"| {r['case']} | {r['patch_file']} | **{r['verdict']}** | "
            f"{n_failed} | {cls.get('label', '-')} | {hyp.get('severity', '-')} |"
        )
    lines.append("")

    # Per-case detail
    lines.append("## Details")
    for r in results:
        lines.append("")
        lines.append(f"### {r['case']} - {r['verdict']}")
        lines.append("")
        lines.append(f"- **Patch applied:** {r['patch_applied']}")
        reg = r["regression"]
        if reg.get("newly_failing"):
            lines.append(f"- **Newly failing tests:** {', '.join(reg['newly_failing'])}")
        if reg.get("newly_passing"):
            lines.append(f"- **Newly passing tests:** {', '.join(reg['newly_passing'])}")
        hyp = r["hypothesis"]
        lines.append(f"- **Classification:** {r['classification'].get('label')}")
        lines.append(f"- **Severity:** {hyp.get('severity')}  |  "
                     f"**Confidence:** {hyp.get('confidence')}")
        lines.append(f"- **Root cause:** {hyp.get('root_cause')}")
        lines.append(f"- **Impact:** {hyp.get('impact')}")
        lines.append(f"- **Suggested fix:** {hyp.get('suggested_fix')}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)

    print(f"[*] Sample repo: {SAMPLE_REPO}")
    print("[*] Running baseline test suite...")
    baseline = run_baseline()
    print(f"    baseline: {baseline.get('passed')} passed / "
          f"{baseline.get('failed')} failed")
    (RESULTS_DIR / "_baseline.json").write_text(
        json.dumps(baseline, indent=2), encoding="utf-8"
    )

    patches = sorted(PATCHES_DIR.glob("*.patch"))
    if not patches:
        print("[!] No patches found.")
        return

    results = []
    for patch_path in patches:
        print(f"[*] Evaluating {patch_path.name} ...")
        result = evaluate_patch(patch_path, baseline)
        results.append(result)
        (RESULTS_DIR / f"{result['case']}.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        print(f"    -> {result['verdict']} "
              f"({result['classification'].get('label')})")

    summary = {
        "baseline": {
            "passed": baseline.get("passed", 0),
            "failed": baseline.get("failed", 0),
            "total": baseline.get("total", 0),
        },
        "cases": [
            {
                "case": r["case"],
                "patch_file": r["patch_file"],
                "verdict": r["verdict"],
                "category": r["classification"].get("category"),
                "label": r["classification"].get("label"),
                "severity": r["hypothesis"].get("severity"),
                "confidence": r["hypothesis"].get("confidence"),
                "newly_failing": r["regression"].get("newly_failing", []),
            }
            for r in results
        ],
        "counts": {
            "total_cases": len(results),
            "regressions": sum(1 for r in results if r["verdict"] == "REGRESSION"),
            "safe": sum(1 for r in results if r["verdict"] in ("SAFE", "IMPROVEMENT")),
            "broken": sum(1 for r in results if r["verdict"] == "BROKEN"),
        },
    }
    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    md = _write_markdown(baseline, results)
    (REPORTS_DIR / "report.md").write_text(md, encoding="utf-8")

    print()
    print("[+] Done.")
    print(f"    results : {RESULTS_DIR}")
    print(f"    report  : {REPORTS_DIR / 'report.md'}")
    print(f"    summary : {summary['counts']}")


if __name__ == "__main__":
    main()
