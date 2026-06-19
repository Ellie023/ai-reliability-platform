"""Streamlit dashboard for the AI Reliability Platform.

Reads the JSON artifacts produced by ``evaluator/generate_report.py`` from the
``results/`` directory and renders an interactive overview of every evaluated
agent patch.

Run with:  ``streamlit run dashboard/streamlit_app.py``
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
REPORTS_DIR = PROJECT_ROOT / "reports"

VERDICT_COLOR = {
    "SAFE": "🟢",
    "IMPROVEMENT": "🟢",
    "REGRESSION": "🔴",
    "BROKEN": "🟠",
}


def load_summary() -> dict | None:
    path = RESULTS_DIR / "summary.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_case(case: str) -> dict | None:
    path = RESULTS_DIR / f"{case}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    st.set_page_config(page_title="AI Reliability Platform", layout="wide")
    st.title("🛡️ AI Reliability Platform")
    st.caption("Automated regression detection & root-cause analysis for agent patches")

    summary = load_summary()
    if summary is None:
        st.warning(
            "No results found. Run `python evaluator/generate_report.py` first."
        )
        return

    # ---- Top-level metrics -------------------------------------------------
    counts = summary["counts"]
    base = summary["baseline"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cases evaluated", counts["total_cases"])
    c2.metric("Regressions", counts["regressions"])
    c3.metric("Safe patches", counts["safe"])
    c4.metric("Baseline tests", f"{base['passed']}/{base['total']} passing")

    st.divider()

    # ---- High Risk Patches -------------------------------------------------
    high_risk = [c for c in summary["cases"] if c.get("risk_level") == "HIGH"]
    if high_risk:
        st.subheader("⚠️ High Risk Patches")
        st.error(
            f"{len(high_risk)} patch(es) scored HIGH risk — review before merging."
        )
        hr_rows = []
        for c in sorted(high_risk, key=lambda x: x.get("risk_score", 0), reverse=True):
            breakdown = c.get("risk_breakdown") or {}
            parts = ", ".join(f"{k} +{v}" for k, v in breakdown.items()) or "—"
            hr_rows.append(
                {
                    "Case": c["case"],
                    "Verdict": c["verdict"],
                    "Risk Score": c.get("risk_score", 0),
                    "Breakdown": parts,
                    "Severity": c.get("severity", "—"),
                    "Newly Failing": len(c.get("newly_failing", [])),
                }
            )
        st.dataframe(
            pd.DataFrame(hr_rows),
            use_container_width=True,
            hide_index=True,
        )
        st.divider()

    # ---- Overview table ----------------------------------------------------
    st.subheader("Patch overview")
    rows = []
    for c in summary["cases"]:
        rows.append(
            {
                "": VERDICT_COLOR.get(c["verdict"], "⚪"),
                "Case": c["case"],
                "Verdict": c["verdict"],
                "Category": c["label"],
                "Severity": c["severity"],
                "Confidence": c["confidence"],
                "Newly failing": len(c["newly_failing"]),
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # ---- Per-case drill-down ----------------------------------------------
    st.subheader("Case detail")
    case_names = [c["case"] for c in summary["cases"]]
    selected = st.selectbox("Select a case", case_names)
    detail = load_case(selected)
    if detail is None:
        st.error(f"No detail file for {selected}")
        return

    verdict = detail["verdict"]
    st.markdown(f"### {VERDICT_COLOR.get(verdict, '⚪')} {selected} — **{verdict}**")

    left, right = st.columns(2)
    with left:
        st.markdown("**Test results (after patch)**")
        ps = detail["patched_summary"]
        st.write(f"Passed: {ps['passed']} / {ps['total']}")
        st.write(f"Failed: {ps['failed']}")
        if ps["failed_tests"]:
            st.markdown("**Failing tests**")
            for t in ps["failed_tests"]:
                st.markdown(f"- `{t}`")

    with right:
        hyp = detail["hypothesis"]
        cls = detail["classification"]
        st.markdown("**Root-cause analysis**")
        st.write(f"**Category:** {cls.get('label')}")
        st.write(f"**Severity:** {hyp.get('severity')}")
        st.write(f"**Confidence:** {hyp.get('confidence')}")
        st.info(hyp.get("root_cause", ""))
        st.write(f"**Impact:** {hyp.get('impact')}")
        st.success(f"Suggested fix: {hyp.get('suggested_fix')}")

    with st.expander("Raw result JSON"):
        st.json(detail)

    # ---- Full markdown report ---------------------------------------------
    report_path = REPORTS_DIR / "report.md"
    if report_path.exists():
        with st.expander("Full Markdown report"):
            st.markdown(report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
