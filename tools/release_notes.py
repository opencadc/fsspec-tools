"""Preserve source references in the first generated release PRs."""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "opencadc/fsspec-tools"
PREFIX = f"https://github.com/{REPOSITORY}"
BASELINES = {"vosfs": "0.11.0", "fss-cli": "0.10.0"}
LEGACY_TAGS = {"vosfs-v0.11.0": "v0.11.0", "fss-cli-v0.10.0": "fsspec-cli-v0.10.0"}


def repair_links(text: str, origins: dict[str, str]) -> str:
    """Correct legacy comparisons and issue links with proven commit origins."""
    for old, historical in LEGACY_TAGS.items():
        text = text.replace(f"{PREFIX}/compare/{old}...", f"{PREFIX}/compare/{historical}...")
    lines = []
    for original_line in text.splitlines(keepends=True):
        line = original_line
        commits = re.findall(rf"{re.escape(PREFIX)}/commit/([0-9a-f]{{7,40}})", line)
        repositories = [{repo for sha, repo in origins.items() if sha.startswith(commit)} for commit in commits]
        if repositories and all(len(matches) == 1 for matches in repositories):
            sources = set.union(*repositories)
            if len(sources) == 1:
                source = sources.pop()
                line = re.sub(rf"{re.escape(PREFIX)}/(issues|pull)/(\d+)", rf"https://github.com/{source}/\1/\2", line)
        lines.append(line)
    return "".join(lines)


def repair_changelog(text: str, origins: dict[str, str]) -> str:
    """Change only the newly generated version section, leaving older notes intact."""
    sections = re.split(r"(?m)(?=^## )", text, maxsplit=2)
    if len(sections) > 1:
        sections[1] = repair_links(sections[1], origins)
    return "".join(sections)


def github(endpoint: str, *, method: str = "GET", payload: dict | None = None, ref: str | None = None) -> dict:
    """Use the workflow token through gh without putting credentials in arguments."""
    executable = shutil.which("gh")
    if executable is None:
        msg = "the release workflow requires gh"
        raise RuntimeError(msg)
    command = [executable, "api", f"repos/{REPOSITORY}/{endpoint}", "--method", method]
    if ref is not None:
        command += ["--field", f"ref={ref}"]
    if payload is not None:
        command += ["--input", "-"]
    result = subprocess.run(  # noqa: S603 - fixed repository endpoints and structured arguments.
        command,
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def update_pull_requests(pulls: list[dict], manifest: dict[str, str], origins: dict[str, str]) -> None:
    """Repair initial release PRs after every release-please create or update."""
    for pull in pulls:
        title = re.fullmatch(r"chore\(repo\): release (vosfs|fss-cli) [0-9]+\.[0-9]+\.[0-9]+", pull["title"])
        if title is None:
            continue
        package = title[1]
        path = f"libs/{package}"
        if manifest[path] != BASELINES[package]:
            continue
        endpoint = f"contents/{path}/CHANGELOG.md"
        contents = github(endpoint, ref=pull["headBranchName"])
        old = base64.b64decode(contents["content"]).decode()
        corrected = repair_changelog(old, origins)
        if corrected != old:
            github(
                endpoint,
                method="PUT",
                payload={
                    "message": "docs(repo): preserve migrated release references",
                    "content": base64.b64encode(corrected.encode()).decode(),
                    "sha": contents["sha"],
                    "branch": pull["headBranchName"],
                },
            )
        body = repair_links(pull["body"], origins)
        if body != pull["body"]:
            github(f"pulls/{int(pull['number'])}", method="PATCH", payload={"body": body})


def main() -> None:
    """Load frozen provenance and process the pinned action's PR output."""
    if os.environ["GITHUB_REPOSITORY"] != REPOSITORY:
        msg = "release note correction runs only in the canonical repository"
        raise RuntimeError(msg)
    origins = json.loads((ROOT / "tools/release-origins.json").read_text())
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text())
    update_pull_requests(json.loads(os.environ["RELEASE_PRS"]), manifest, origins)


if __name__ == "__main__":
    main()
