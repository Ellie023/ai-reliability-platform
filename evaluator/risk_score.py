"""Compute a numeric risk score for an evaluated patch.

The score turns the raw evaluation signals into a single, sortable number so a
reviewer (or an automated gate) can triage the most dangerous patches first.

Scoring rules
-------------
* regression present .............. +50
* per failing test ................ +10  (failed_tests count * 10)
* test run timed out .............. +20
* touches >= 3 files .............. +10

Risk levels
-----------
* score >= 50 .... HIGH
* score >= 20 .... MEDIUM
* otherwise ...... LOW
"""
from __future__ import annotations

HIGH_RISK_THRESHOLD = 50
MEDIUM_RISK_THRESHOLD = 20


def compute_risk_score(
    *,
    has_regression: bool,
    failed_test_count: int,
    timed_out: bool,
    changed_files: int,
) -> dict:
    """Return ``{risk_score, risk_level, breakdown}`` for one patch."""
    score = 0
    breakdown: dict[str, int] = {}

    if has_regression:
        breakdown["regression"] = 50
        score += 50

    if failed_test_count:
        pts = failed_test_count * 10
        breakdown["failed_tests"] = pts
        score += pts

    if timed_out:
        breakdown["timeout"] = 20
        score += 20

    if changed_files >= 3:
        breakdown["changed_files"] = 10
        score += 10

    if score >= HIGH_RISK_THRESHOLD:
        level = "HIGH"
    elif score >= MEDIUM_RISK_THRESHOLD:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "risk_score": score,
        "risk_level": level,
        "breakdown": breakdown,
        "changed_files": changed_files,
        "timed_out": timed_out,
    }


if __name__ == "__main__":
    print(compute_risk_score(
        has_regression=True, failed_test_count=2, timed_out=False, changed_files=1,
    ))
