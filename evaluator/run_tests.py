"""Run the pytest suite inside a working copy and parse the results.

Uses ``pytest-json-report`` so we get a structured per-test breakdown that the
rest of the pipeline can reason about (passed / failed test ids, durations,
failure messages).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_tests(work_dir: Path) -> dict:
    """Run the test suite in ``work_dir`` and return a structured summary."""
    work_dir = Path(work_dir)
    report_file = work_dir / ".report.json"

    env = dict(os.environ)
    # Make ``app`` importable from the working copy.
    env["PYTHONPATH"] = str(work_dir) + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-q",
            "--json-report",
            f"--json-report-file={report_file}",
        ],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        env=env,
    )

    summary = {
        "returncode": proc.returncode,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "passed_tests": [],
        "failed_tests": [],
        "failures": {},  # test_id -> failure message
        "collected": True,
        "raw_stdout_tail": proc.stdout.strip().splitlines()[-5:],
    }

    if not report_file.exists():
        # Collection error or pytest could not run at all.
        summary["collected"] = False
        summary["raw_stdout_tail"] = proc.stdout.strip().splitlines()[-15:]
        summary["raw_stderr_tail"] = proc.stderr.strip().splitlines()[-15:]
        return summary

    data = json.loads(report_file.read_text(encoding="utf-8"))
    tests = data.get("tests", [])
    summary["total"] = len(tests)
    for test in tests:
        nodeid = test.get("nodeid", "")
        short = nodeid.split("::")[-1]
        outcome = test.get("outcome")
        if outcome == "passed":
            summary["passed"] += 1
            summary["passed_tests"].append(short)
        elif outcome == "failed":
            summary["failed"] += 1
            summary["failed_tests"].append(short)
            message = (
                test.get("call", {}).get("longrepr")
                or test.get("setup", {}).get("longrepr")
                or "no traceback captured"
            )
            summary["failures"][short] = str(message)
        elif outcome == "error":
            summary["errors"] += 1
            summary["failed_tests"].append(short)
            summary["failures"][short] = str(
                test.get("setup", {}).get("longrepr", "error")
            )

    return summary


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python run_tests.py <work_dir>")
        raise SystemExit(2)
    out = run_tests(Path(sys.argv[1]))
    print(json.dumps(out, indent=2))
