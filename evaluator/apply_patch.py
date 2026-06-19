"""Apply an agent-generated patch to an isolated copy of the sample repo.

Each patch is applied to a fresh working copy so cases never interfere with
one another. The original ``sample_repo`` is never modified.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_REPO = PROJECT_ROOT / "sample_repo"


def make_work_copy(case_name: str, base_dir: Path | None = None) -> Path:
    """Create a clean copy of the sample repo for ``case_name``."""
    base_dir = base_dir or (PROJECT_ROOT / "results" / "_work")
    base_dir.mkdir(parents=True, exist_ok=True)
    work_dir = base_dir / case_name
    if work_dir.exists():
        shutil.rmtree(work_dir)
    shutil.copytree(SAMPLE_REPO, work_dir)
    return work_dir


def apply_patch(patch_path: Path, work_dir: Path) -> dict:
    """Apply ``patch_path`` inside ``work_dir`` using the ``patch`` utility.

    Returns a dict describing whether the patch applied cleanly.
    """
    patch_text = Path(patch_path).read_text(encoding="utf-8")
    proc = subprocess.run(
        ["patch", "-p1", "--no-backup-if-mismatch", "--forward"],
        input=patch_text,
        cwd=str(work_dir),
        capture_output=True,
        text=True,
    )
    applied = proc.returncode == 0
    return {
        "applied": applied,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def prepare_case(case_name: str, patch_path: Path) -> dict:
    """Make a work copy and apply the patch in one step."""
    work_dir = make_work_copy(case_name)
    result = apply_patch(patch_path, work_dir)
    result["work_dir"] = str(work_dir)
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python apply_patch.py <patch_file>")
        raise SystemExit(2)
    patch = Path(sys.argv[1])
    out = prepare_case(patch.stem, patch)
    print(out)
