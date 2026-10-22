"""Contracts for independent releases and guarded publishing/deployment."""

import json
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "release-please-config.json").read_text())
MANIFEST = json.loads((ROOT / ".release-please-manifest.json").read_text())
PACKAGES = {"libs/vosfs": "vosfs", "libs/fss-cli": "fss-cli"}
UPSTREAM_GUARD = "github.repository == 'opencadc/fsspec-tools'"
BASELINE = "58673da71cdf49a390c7cf750e4402f6f041ef38"


def workflow(name: str) -> dict:
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def triggers(loaded: dict) -> dict:
    return loaded.get("on", loaded.get(True))


def test_release_baseline_excludes_import_and_preserves_unreleased_changes() -> None:
    assert {
        path: tomllib.loads((ROOT / path / "pyproject.toml").read_text())["project"]["version"] for path in PACKAGES
    } == MANIFEST
    assert CONFIG["separate-pull-requests"] is True
    assert CONFIG["pull-request-title-pattern"] == "chore(repo): release${component} ${version}"
    assert CONFIG["include-component-in-tag"] is True
    assert CONFIG["draft"] is True
    if "bootstrap-sha" in CONFIG:
        assert CONFIG["bootstrap-sha"] == BASELINE
    assert "last-release-sha" not in CONFIG
    assert set(CONFIG["packages"]) == set(PACKAGES)


@pytest.mark.parametrize(("path", "component"), PACKAGES.items())
def test_each_package_updates_its_own_version_and_lock_entry(path: str, component: str) -> None:
    package = CONFIG["packages"][path]
    assert package["release-type"] == "python"
    assert package["component"] == component
    assert package["package-name"] == component
    assert package["changelog-path"] == "CHANGELOG.md"
    assert package["bump-minor-pre-major"] is True
    assert package["bump-patch-for-minor-pre-major"] is False
    assert package["extra-files"] == [
        {"type": "toml", "path": "/uv.lock", "jsonpath": f"$.package[?(@.name.value=='{component}')].version"}
    ]


def test_release_automation_is_disabled_until_explicitly_enabled() -> None:
    job = workflow("cd.yml")["jobs"]["release-please"]
    assert job["if"] == f"{UPSTREAM_GUARD} && vars.RELEASE_ENABLED == 'true'"
    release = next(step for step in job["steps"] if step.get("id") == "release")
    assert "token" not in release["with"]
    dispatch = next(step for step in job["steps"] if step["name"] == "Dispatch each released package")
    assert dispatch["env"]["GH_TOKEN"] == "${{ secrets.GITHUB_TOKEN }}"
    assert "pypi-release" in dispatch["run"]
    assert "docs-publish" not in dispatch["run"]
    correction = next(step for step in job["steps"] if step.get("run") == "python tools/migration_notes.py")
    assert correction["if"] == "steps.release.outputs.prs_created == 'true'"
    assert correction["env"]["RELEASE_PRS"] == "${{ steps.release.outputs.prs }}"
    assert "^libs/(vosfs|fss-cli)$" in dispatch["run"]


def test_publishing_requires_a_verified_tag_main_history_and_ci() -> None:
    jobs = workflow("pypi.yml")["jobs"]
    text = (ROOT / ".github/workflows/pypi.yml").read_text()
    assert "vars.PYPI_ENABLED == 'true'" in jobs["build"]["if"]
    assert "github.ref == 'refs/heads/main'" in jobs["build"]["if"]
    assert "git merge-base --is-ancestor" in text
    assert "refs/tags/$TAG^{commit}" in text
    assert "actions/workflows/ci.yml/runs" in text
    assert "uv lock --check" in text
    assert 'uv build --no-sources --package "$PACKAGE"' in text
    assert "tools/release.py" in text
    assert jobs["publish"]["permissions"]["id-token"] == "write"
    assert "id-token" not in jobs["build"]["permissions"]
    assert "environment" in jobs["publish"]


def test_recovery_reuses_artifacts_and_never_clobbers_release_assets() -> None:
    loaded = workflow("pypi.yml")
    text = (ROOT / ".github/workflows/pypi.yml").read_text()
    assert "artifact_run_id" in triggers(loaded)["workflow_dispatch"]["inputs"]
    assert "run-id: ${{ inputs.artifact_run_id }}" in text
    assert "retention-days: 90" in text
    assert "--require-published" in text
    assert set(loaded["jobs"]["verify"]["needs"]) == {"build", "publish"}
    assert "--clobber" not in text
    finalization = loaded["jobs"]["github-release"]["steps"][-1]["run"]
    release_commands = [line for line in finalization.splitlines() if "gh release " in line]
    assert len(release_commands) == 2
    assert all('--repo "$GITHUB_REPOSITORY"' in line for line in release_commands)
    assert "sha256sum" in text
    assert "needs.build.outputs.index == 'pypi'" in loaded["jobs"]["github-release"]["if"]
    assert set(loaded["jobs"]["github-release"]["needs"]) == {"build", "verify"}


def test_docs_deploy_successful_main_builds_independently_of_releases() -> None:
    loaded = workflow("docs.yml")
    jobs = loaded["jobs"]
    assert triggers(loaded)["workflow_run"]["workflows"] == ["CI"]
    assert triggers(loaded)["workflow_run"]["branches"] == ["main"]
    assert jobs["deploy"]["needs"] == "build"
    assert jobs["deploy"]["environment"]["name"] == "github-pages"
    assert jobs["deploy"]["permissions"]["pages"] == "write"
    assert jobs["deploy"]["permissions"]["id-token"] == "write"
    uses = [step.get("uses", "") for job in jobs.values() for step in job.get("steps", [])]
    assert any(action.startswith("actions/upload-pages-artifact@") for action in uses)
    assert any(action.startswith("actions/deploy-pages@") for action in uses)
    assert not (ROOT / ".github/workflows/cibuild.yml").exists()


def test_privileged_jobs_are_guarded_by_the_canonical_repository() -> None:
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        for name, job in workflow(path.name)["jobs"].items():
            if any(value == "write" for value in job.get("permissions", {}).values()):
                assert UPSTREAM_GUARD in job["if"], f"{path.name}:{name}"
