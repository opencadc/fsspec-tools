"""First-release notes keep the source projects' identities without fake tags."""

import base64

import pytest

from tools import migration_notes

PREFIX = "https://github.com/opencadc/fsspec-tools"
SHA = "a" * 40
ORIGINS = {SHA: "shinybrar/vostools"}
ENTRY = f"* fix ([#27]({PREFIX}/issues/27)) ([aaaaaaa]({PREFIX}/commit/{SHA}))\n"


def test_migrated_and_new_commit_issue_links_are_distinguished() -> None:
    new_entry = ENTRY.replace(SHA, "b" * 40)
    fixed = migration_notes.repair_links(ENTRY + new_entry, ORIGINS)
    assert "https://github.com/shinybrar/vostools/issues/27" in fixed
    assert new_entry in fixed
    assert f"{PREFIX}/commit/{SHA}" in fixed
    assert migration_notes.repair_links(fixed, ORIGINS) == fixed


def test_only_the_new_changelog_section_is_repaired() -> None:
    header = f"## [0.12.0]({PREFIX}/compare/vosfs-v0.11.0...vosfs-v0.12.0)\n"
    old = "## Older release\n" + ENTRY
    fixed = migration_notes.repair_changelog("# Changelog\n\n" + header + ENTRY + old, ORIGINS)
    assert f"{PREFIX}/compare/v0.11.0...vosfs-v0.12.0" in fixed
    assert fixed.endswith(old)
    cli = f"{PREFIX}/compare/fss-cli-v0.10.0...fss-cli-v0.11.0"
    assert migration_notes.repair_links(cli, ORIGINS) == f"{PREFIX}/compare/fsspec-cli-v0.10.0...fss-cli-v0.11.0"


def test_initial_pr_updates_both_notes_locations_with_a_blob_guard(monkeypatch) -> None:
    calls = []
    text = "# Changelog\n\n## 0.12.0\n" + ENTRY

    def github(endpoint, **kwargs):
        calls.append((endpoint, kwargs))
        return {"sha": "original-blob", "content": base64.b64encode(text.encode()).decode()}

    monkeypatch.setattr(migration_notes, "github", github)
    pull = {
        "number": 10,
        "title": "chore(repo): release vosfs 0.12.0",
        "headBranchName": "release-branch",
        "body": ENTRY,
    }
    migration_notes.update_pull_requests([pull], {"libs/vosfs": "0.11.0"}, ORIGINS)
    assert calls[1][0] == "contents/libs/vosfs/CHANGELOG.md"
    assert calls[1][1]["payload"]["sha"] == "original-blob"
    assert calls[1][1]["payload"]["branch"] == "release-branch"
    assert calls[2] == (
        "pulls/10",
        {"method": "PATCH", "payload": {"body": migration_notes.repair_links(ENTRY, ORIGINS)}},
    )
    calls.clear()
    migration_notes.update_pull_requests([pull], {"libs/vosfs": "0.12.0"}, ORIGINS)
    assert not calls


def test_retry_finishes_a_body_correction_after_the_changelog_was_saved(monkeypatch) -> None:
    text = "# Changelog\n\n## 0.12.0\n" + ENTRY
    state = {"text": text, "body_attempts": 0, "file_updates": 0}

    def github(_endpoint, **kwargs):
        if kwargs.get("method") == "PUT":
            state["text"] = base64.b64decode(kwargs["payload"]["content"]).decode()
            state["file_updates"] += 1
        elif kwargs.get("method") == "PATCH":
            state["body_attempts"] += 1
            if state["body_attempts"] == 1:
                msg = "temporary GitHub failure"
                raise RuntimeError(msg)
        return {"sha": "blob", "content": base64.b64encode(state["text"].encode()).decode()}

    monkeypatch.setattr(migration_notes, "github", github)
    pull = {
        "number": 10,
        "title": "chore(repo): release vosfs 0.12.0",
        "headBranchName": "release-branch",
        "body": ENTRY,
    }
    with pytest.raises(RuntimeError, match="temporary GitHub failure"):
        migration_notes.update_pull_requests([pull], {"libs/vosfs": "0.11.0"}, ORIGINS)
    migration_notes.update_pull_requests([pull], {"libs/vosfs": "0.11.0"}, ORIGINS)
    assert state["file_updates"] == 1
    assert state["body_attempts"] == 2
