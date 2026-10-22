"""The artifact gate permits backend identity changes, but no payload changes."""

import runpy
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMPARE = runpy.run_path(str(ROOT / "libs/fss-cli/tests/_installed_wheel_gate.py"))["_compare_wheels"]


def wheel(path: Path, *, generator: str, payload: bytes = b"code", tag: str = "py3-none-any") -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("example/__init__.py", payload)
        archive.writestr("example.dist-info/WHEEL", f"Wheel-Version: 1.0\nGenerator: {generator}\nTag: {tag}\n")
        archive.writestr("example.dist-info/RECORD", generator)


def test_compatible_backend_generators_do_not_change_distribution_contents(tmp_path: Path) -> None:
    first, second = tmp_path / "first.whl", tmp_path / "second.whl"
    wheel(first, generator="uv bundled")
    wheel(second, generator="uv isolated")
    COMPARE(first, second)


@pytest.mark.parametrize("change", [{"payload": b"changed"}, {"tag": "cp312-none-any"}])
def test_source_or_compatibility_changes_fail_the_rebuild_gate(tmp_path: Path, change: dict) -> None:
    first, second = tmp_path / "first.whl", tmp_path / "second.whl"
    wheel(first, generator="uv bundled")
    wheel(second, generator="uv isolated", **change)
    with pytest.raises(RuntimeError, match="sdist rebuild differs"):
        COMPARE(first, second)
