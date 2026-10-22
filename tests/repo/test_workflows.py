"""Static contracts for the GitHub Actions workflows."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
QUALITY = ROOT / ".github" / "workflows" / "ci.yml"
UPSTREAM_GUARD = "github.repository == 'opencadc/fsspec-tools'"
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def triggers(workflow: dict) -> dict:
    # YAML 1.1 reads the bare key `on` as the boolean True.
    return workflow.get("on", workflow.get(True))


def steps(workflow: dict) -> list[dict]:
    return [step for job in workflow["jobs"].values() for step in job.get("steps", [])]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_third_party_actions_are_pinned_to_a_commit(path: Path) -> None:
    for step in steps(load(path)):
        if "uses" in step and not step["uses"].startswith("./"):
            assert PINNED.match(step["uses"]), step["uses"]


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_workflows_declare_expected_default_permissions(path: Path) -> None:
    assert load(path)["permissions"] == {"contents": "read"}


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_checkouts_do_not_persist_credentials(path: Path) -> None:
    for step in steps(load(path)):
        if step.get("uses", "").startswith("actions/checkout@"):
            assert step["with"]["persist-credentials"] is False, step


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_every_job_has_a_timeout(path: Path) -> None:
    for name, job in load(path)["jobs"].items():
        assert "uses" in job or "timeout-minutes" in job, name


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_publishing_runs_only_on_the_upstream_repository(path: Path) -> None:
    for name, job in load(path)["jobs"].items():
        publishes = job.get("permissions", {}).get("id-token") == "write" or any(
            step.get("uses", "").startswith("pypa/gh-action-pypi-publish@") for step in job.get("steps", [])
        )
        if publishes:
            assert UPSTREAM_GUARD in job.get("if", ""), name
            assert "shinybrar/vostools" not in job["if"]


def test_quality_always_runs_and_exposes_required() -> None:
    workflow = load(QUALITY)
    on = triggers(workflow)
    jobs = workflow["jobs"]

    assert "pull_request" in on
    assert on["push"]["branches"] == ["main", "migration/**"]
    assert on["schedule"]
    assert "workflow_dispatch" in on
    assert "paths" not in on.get("pull_request", {})
    assert jobs["required"]["if"] == "always()"
    assert set(jobs["required"]["needs"]) == {"quality", "pr-title", "vosfs", "fss-cli", "artifacts"}


def test_quality_runs_contract_tests_and_docs() -> None:
    text = QUALITY.read_text()

    assert "pytest tests/repo" in text
    assert "zensical build --strict" in text
    assert "uv build --no-sources --all-packages" in text


@pytest.mark.parametrize(
    ("job", "result", "event", "success"),
    [
        ("quality", "success", "pull_request", True),
        ("quality", "failure", "pull_request", False),
        ("vosfs", "failure", "pull_request", False),
        ("fss-cli", "failure", "pull_request", False),
        ("artifacts", "failure", "pull_request", False),
        ("vosfs", "cancelled", "pull_request", False),
        ("fss-cli", "skipped", "push", False),
        ("pr-title", "skipped", "pull_request", False),
        ("pr-title", "skipped", "push", True),
    ],
)
def test_required_fails_when_any_applicable_job_does_not_pass(job: str, result: str, event: str, success: bool) -> None:
    required = load(QUALITY)["jobs"]["required"]
    results = {name: {"result": "success"} for name in required["needs"]}
    results[job]["result"] = result
    bash = shutil.which("bash")
    assert bash is not None
    completed = subprocess.run(  # noqa: S603 - execute the repository workflow with synthetic job results.
        [bash, "-c", required["steps"][0]["run"]],
        env={**os.environ, "RESULTS": json.dumps(results), "EVENT": event},
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert (completed.returncode == 0) is success


def test_package_matrix_covers_supported_platforms() -> None:
    matrix = load(ROOT / ".github/workflows/reusable-package.yml")["jobs"]["test"]["strategy"]["matrix"]["include"]
    assert {(entry["os"], entry["python"]) for entry in matrix} == {
        *(("ubuntu-latest", f"3.{minor}") for minor in range(10, 15)),
        ("macos-latest", "3.12"),
    }
    assert "_installed_wheel_gate.py" in QUALITY.read_text()


def test_no_custom_github_scripts() -> None:
    scripts = ROOT / ".github" / "scripts"
    assert not scripts.exists()


def test_quality_has_no_live_test_or_credential_wiring() -> None:
    workflow = QUALITY.read_text()

    assert set(re.findall(r"secrets\.(\w+)", workflow)) <= {"CODECOV_TOKEN"}
    for forbidden in ("CADC_USERNAME", "CADC_PASSWORD", "VOSFS_TEST_", "VOSFS_CERT_FILE", "integration"):
        assert forbidden not in workflow
