"""Generate a human-readable root-cause hypothesis and suggested fix.

Given a classification, this module produces a short narrative explaining the
*likely* root cause of the regression and a concrete remediation suggestion.
This mirrors the "explainability" layer of a real AI reliability platform: the
output is meant to be dropped straight into a report or a PR review comment.
"""
from __future__ import annotations

_HYPOTHESES = {
    "EMPTY_ORDER_VALIDATION": {
        "root_cause": (
            "The guard that rejects orders with no line items was removed from "
            "`create_order`. Empty orders now pass through and are persisted."
        ),
        "impact": "Empty/zero-value orders can be created, corrupting downstream billing.",
        "suggested_fix": (
            "Restore the `if not items: raise OrderError(...)` check at the top "
            "of `create_order`."
        ),
        "severity": "HIGH",
    },
    "PRICE_VALIDATION": {
        "root_cause": (
            "The `item.unit_price < 0` validation was removed, so items with a "
            "negative price are accepted."
        ),
        "impact": "Negative prices produce negative totals / unintended refunds.",
        "suggested_fix": (
            "Re-add the per-item negative price check inside the validation loop "
            "of `create_order`."
        ),
        "severity": "HIGH",
    },
    "QUANTITY_VALIDATION": {
        "root_cause": (
            "The non-positive quantity guard was weakened or removed in "
            "`create_order`."
        ),
        "impact": "Orders with zero/negative quantities can be created.",
        "suggested_fix": "Restore `if item.quantity <= 0: raise OrderError(...)`.",
        "severity": "MEDIUM",
    },
    "DISCOUNT_VALIDATION": {
        "root_cause": (
            "The upper bound of the discount check was dropped, so "
            "`apply_discount` no longer rejects values above 100%."
        ),
        "impact": "Discounts > 100% yield negative totals (the store pays the customer).",
        "suggested_fix": (
            "Restore the full bounds check `if discount_percent < 0 or "
            "discount_percent > 100`."
        ),
        "severity": "HIGH",
    },
    "STATE_MACHINE": {
        "root_cause": (
            "`transition_status` no longer enforces the allowed-transition table; "
            "any status can move to any other status (e.g. a delivered order can "
            "revert to pending)."
        ),
        "impact": "Order lifecycle invariants are violated, enabling illegal states.",
        "suggested_fix": (
            "Use `VALID_TRANSITIONS[order.status]` instead of allowing every "
            "status, and keep the `new_status not in allowed` guard."
        ),
        "severity": "HIGH",
    },
    "PATCH_DID_NOT_APPLY": {
        "root_cause": (
            "The patch failed to apply cleanly or the patched module does not "
            "import, so the test suite could not be collected."
        ),
        "impact": "The change is unmergeable in its current form.",
        "suggested_fix": "Rebase the patch against the current source and fix syntax/import errors.",
        "severity": "BLOCKER",
    },
    "UNKNOWN": {
        "root_cause": "One or more tests regressed but the cause did not match a known pattern.",
        "impact": "Unknown behavioural change; manual review required.",
        "suggested_fix": "Inspect the failing assertions listed in the report.",
        "severity": "MEDIUM",
    },
}

_SAFE = {
    "root_cause": "No tests regressed; the patch preserves all existing behaviour.",
    "impact": "None detected by the current suite.",
    "suggested_fix": "Safe to merge (subject to code review and coverage limits).",
    "severity": "NONE",
}


def generate_hypothesis(classification: dict, regression: dict) -> dict:
    """Return a hypothesis dict for the given classification/regression."""
    verdict = regression.get("verdict")
    if verdict in ("SAFE", "IMPROVEMENT"):
        hyp = dict(_SAFE)
        if verdict == "IMPROVEMENT":
            hyp["root_cause"] = (
                "No regressions, and one or more previously failing tests now "
                "pass."
            )
        hyp["confidence"] = 0.9
        return hyp

    category = classification.get("category", "UNKNOWN")
    hyp = dict(_HYPOTHESES.get(category, _HYPOTHESES["UNKNOWN"]))

    # Confidence is higher when the failures all point to a single category.
    counts = classification.get("category_counts", {})
    if counts:
        dominant = max(counts.values())
        total = sum(counts.values())
        hyp["confidence"] = round(dominant / total, 2)
    else:
        hyp["confidence"] = 0.5
    return hyp


if __name__ == "__main__":
    cls = {"category": "DISCOUNT_VALIDATION", "category_counts": {"DISCOUNT_VALIDATION": 1}}
    reg = {"verdict": "REGRESSION"}
    print(generate_hypothesis(cls, reg))
