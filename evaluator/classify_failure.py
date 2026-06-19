"""Classify why a patch failed based on which tests regressed.

This is a lightweight, explainable heuristic classifier. It maps failing test
names and failure messages to a small taxonomy of failure categories used by
the reliability platform. The intent is to turn raw red tests into an
actionable label a human (or an upstream agent) can route on.
"""
from __future__ import annotations

# Ordered rules: (category, keywords-in-test-name, keywords-in-message)
_RULES = [
    (
        "EMPTY_ORDER_VALIDATION",
        ("empty",),
        ("at least one item",),
    ),
    (
        "PRICE_VALIDATION",
        ("negative_price", "price"),
        ("unit price", "negative"),
    ),
    (
        "QUANTITY_VALIDATION",
        ("quantity",),
        ("quantity must be positive",),
    ),
    (
        "DISCOUNT_VALIDATION",
        ("discount",),
        ("discount percent",),
    ),
    (
        "STATE_MACHINE",
        ("transition", "status", "terminal", "cancel"),
        ("transition from",),
    ),
]

CATEGORY_LABELS = {
    "EMPTY_ORDER_VALIDATION": "Empty-order validation removed",
    "PRICE_VALIDATION": "Negative-price validation removed",
    "QUANTITY_VALIDATION": "Quantity validation removed",
    "DISCOUNT_VALIDATION": "Discount bounds validation removed",
    "STATE_MACHINE": "Invalid order status transition allowed",
    "PATCH_DID_NOT_APPLY": "Patch could not be applied or imported",
    "UNKNOWN": "Unclassified business-logic regression",
}


def _match_one(test_name: str, message: str) -> str:
    name = test_name.lower()
    msg = (message or "").lower()
    for category, name_kw, msg_kw in _RULES:
        if any(k in name for k in name_kw) or any(k in msg for k in msg_kw):
            return category
    return "UNKNOWN"


def classify_failure(regression: dict, patched: dict) -> dict:
    """Produce a classification for a regression result.

    Returns the dominant category plus a per-test breakdown.
    """
    if regression.get("verdict") == "BROKEN":
        return {
            "category": "PATCH_DID_NOT_APPLY",
            "label": CATEGORY_LABELS["PATCH_DID_NOT_APPLY"],
            "per_test": {},
        }

    failures = patched.get("failures", {})
    per_test = {}
    counts: dict[str, int] = {}
    for test_name in regression.get("newly_failing", []):
        category = _match_one(test_name, failures.get(test_name, ""))
        per_test[test_name] = category
        counts[category] = counts.get(category, 0) + 1

    if not counts:
        dominant = "NONE"
        label = "No regression detected"
    else:
        dominant = max(counts, key=counts.get)
        label = CATEGORY_LABELS.get(dominant, CATEGORY_LABELS["UNKNOWN"])

    return {
        "category": dominant,
        "label": label,
        "per_test": per_test,
        "category_counts": counts,
    }


if __name__ == "__main__":
    reg = {"verdict": "REGRESSION", "newly_failing": ["test_apply_discount_over_100_raises"]}
    pat = {"failures": {"test_apply_discount_over_100_raises": "DID NOT RAISE OrderError"}}
    print(classify_failure(reg, pat))
