"""requirements.txt (local, Railway) and pyproject.toml (Vercel) must pin the same packages."""

import tomllib
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def _requirements() -> set[str]:
    lines = (BACKEND / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def test_pyproject_dependencies_match_requirements() -> None:
    pyproject = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
    assert set(pyproject["project"]["dependencies"]) == _requirements()
