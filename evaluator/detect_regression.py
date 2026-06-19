"""Compare a baseline test run against a patched run to detect regressions.

A *regression* is a test that passed on the clean repo but fails after the
patch is applied. We also surface newly-fixed tests (red -> green) so that
genuinely good patches can be distinguished from harmful ones.
"""
from __future__ import annotations


def detect_regression(baseline: dict, patched: dict) -> dict:
    """Diff two ``run_tests`` summaries.

    Returns a dict describing newly failing / newly passing tests and an
    overall verdict.
    """
    base_failed = set(baseline.get("failed_tests", []))
    patched_failed = set(patched.get("failed_tests", []))

    newly_failing = sorted(patched_failed - base_failed)
    newly_passing = sorted(base_failed - patched_failed)

    patch_applied = patched.get("collected", True)

    has_regression = bool(newly_failing) or not patch_applied

    if not patch_applied:
        verdict = "BROKEN"  # patch did not even import / collect
    elif newly_failing:
        verdict = "REGRESSION"
    elif newly_passing:
        verdict = "IMPROVEMENT"
    else:
        verdict = "SAFE"

    return {
        "verdict": verdict,
        "has_regression": has_regression,
        "newly_failing": newly_failing,
        "newly_passing": newly_passing,
        "baseline_passed": baseline.get("passed", 0),
        "baseline_failed": baseline.get("failed", 0),
        "patched_passed": patched.get("passed", 0),
        "patched_failed": patched.get("failed", 0),
    }


if __name__ == "__main__":
    # Tiny self-check.
    base = {"failed_tests": [], "passed": 10, "failed": 0, "collected": True}
    new = {"failed_tests": ["test_x"], "passed": 9, "failed": 1, "collected": True}
    print(detect_regression(base, new))
