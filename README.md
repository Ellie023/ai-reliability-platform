# AI Reliability Platform

[![Repo](https://img.shields.io/badge/GitHub-ai--reliability--platform-181717?logo=github)](https://github.com/Ellie023/ai-reliability-platform)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen?logo=pytest&logoColor=white)](sample_repo/tests/test_order_service.py)

> Repository: **https://github.com/Ellie023/ai-reliability-platform**

An end-to-end harness that evaluates **AI-agent-generated code patches** for
reliability. It applies each patch to an isolated copy of a small FastAPI
**Order API**, runs the test suite, detects regressions, classifies the
failure, and generates a root-cause hypothesis — then surfaces everything in a
Streamlit dashboard.

This is the kind of evaluation loop you would put *in front of* an autonomous
coding agent to decide whether its proposed change is safe to merge.

## Project layout

```
ai-reliability-platform/
├── sample_repo/              # the system-under-test (a FastAPI Order API)
│   ├── app/
│   │   ├── models.py         # Pydantic models + OrderStatus enum
│   │   ├── order_service.py  # business logic (validation, discount, state machine)
│   │   └── main.py           # FastAPI endpoints
│   └── tests/
│       └── test_order_service.py   # 18 pytest tests describing correct behaviour
├── patches/                  # agent-generated patches to evaluate
│   ├── agent_case_01.patch   # BUG: empty order allowed
│   ├── agent_case_02.patch   # BUG: discount > 100% allowed
│   ├── agent_case_03.patch   # BUG: negative price allowed
│   ├── agent_case_04.patch   # BUG: invalid status transition allowed
│   ├── agent_case_05.patch   # OK : adds count_items() helper (no regression)
│   └── agent_case_06.patch   # OK : adds can_cancel() helper (no regression)
├── evaluator/
│   ├── apply_patch.py        # isolate a work copy + apply a patch
│   ├── run_tests.py          # run pytest, parse JSON report
│   ├── detect_regression.py  # diff baseline vs patched test runs
│   ├── classify_failure.py   # map regressions to a failure taxonomy
│   ├── generate_hypothesis.py# root-cause + suggested-fix narrative
│   └── generate_report.py    # orchestrator (writes results/ + reports/)
├── dashboard/
│   └── streamlit_app.py      # interactive results dashboard
├── reports/                  # generated Markdown report
├── results/                  # generated per-case + summary JSON
├── requirements.txt
└── README.md
```

## Setup

```bash
cd ~/ai-reliability-platform
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run the evaluation pipeline

```bash
python evaluator/generate_report.py
```

This produces:

- `results/<case>.json` — full machine-readable result per patch
- `results/summary.json` — aggregate verdict counts
- `reports/report.md` — human-readable report

Expected outcome: cases **01–04 → REGRESSION** (each with a classified root
cause), cases **05–06 → SAFE**.

## Launch the dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

## Run the sample API directly (optional)

```bash
cd sample_repo
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/docs
```

## How a patch is judged

1. **Isolate** — copy `sample_repo/` to `results/_work/<case>/`.
2. **Apply** — `patch -p1` the candidate diff.
3. **Test** — run the pytest suite with a JSON report.
4. **Detect** — compare failing tests against the clean baseline.
5. **Classify** — map the newly-failing tests to a failure category.
6. **Hypothesize** — emit a root cause, impact, severity and suggested fix.

A patch is `SAFE` only if it introduces **zero** new failing tests.
