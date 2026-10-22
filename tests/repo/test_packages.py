"""Contracts for the two independently distributed workspace packages."""

import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_every_workspace_member_has_a_required_package_job() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    packages = {path.parent.name for path in ROOT.glob("libs/*/pyproject.toml")}
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    jobs = workflow["jobs"]
    tested = {job["with"]["package"] for job in jobs.values() if job.get("uses", "").endswith("reusable-package.yml")}

    assert packages == tested == {"vosfs", "fss-cli"}
    assert config["tool"]["uv"]["package"] is False
    assert set(config["tool"]["uv"]["workspace"]["members"]) == {"libs/vosfs", "libs/fss-cli"}
    assert tested <= set(jobs["required"]["needs"])


def test_fss_cli_depends_on_vosfs_for_tests() -> None:
    config = tomllib.loads((ROOT / "libs" / "fss-cli" / "pyproject.toml").read_text())
    group = " ".join(config["dependency-groups"]["dev"])

    assert "vosfs" in group


def test_commit_scopes_name_every_package() -> None:
    pattern = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["commitizen"]["customize"]["schema_pattern"]
    scopes = set(re.search(r"\\\(\(([^)]*)\)", pattern).group(1).split("|"))

    assert scopes == {"vosfs", "fss-cli", "repo"}


def test_every_package_supports_the_ci_python_range() -> None:
    for pyproject in ROOT.glob("libs/*/pyproject.toml"):
        assert tomllib.loads(pyproject.read_text())["project"]["requires-python"] == ">=3.10", pyproject
