"""Recursive commands accept backend names without a leading slash."""

from contextlib import asynccontextmanager

import pytest
from fsspec.implementations.asyn_wrapper import AsyncFileSystemWrapper
from fsspec.implementations.memory import MemoryFileSystem
from typer.testing import CliRunner

from fss_cli import App


@pytest.mark.parametrize("command", ["cp", "rm"])
@pytest.mark.parametrize(("root_slashless", "children_slashless"), [(True, True), (True, False), (False, True)])
def test_recursive_commands_accept_slashless_metadata(
    monkeypatch: pytest.MonkeyPatch, command: str, root_slashless: bool, children_slashless: bool
) -> None:
    monkeypatch.setattr(MemoryFileSystem, "store", {})
    monkeypatch.setattr(MemoryFileSystem, "pseudo_dirs", [""])

    class SlashlessMemory(MemoryFileSystem):
        def info(self, path, **kwargs):
            info = super().info(path, **kwargs)
            return {**info, "name": info["name"].lstrip("/") if root_slashless else info["name"]}

        def ls(self, path, detail=True, **kwargs):  # noqa: FBT002 - fsspec signature
            rows = super().ls(path, detail=True, **kwargs)
            rows = [{**row, "name": row["name"].lstrip("/") if children_slashless else row["name"]} for row in rows]
            return rows if detail else [row["name"] for row in rows]

    backend = SlashlessMemory(skip_instance_cache=True)
    backend.makedirs("/bucket/docs/nested")
    backend.makedirs("/bucket/docs/empty")
    backend.makedirs("/out")
    backend.pipe_file("/bucket/docs/nested/file", b"payload")

    @asynccontextmanager
    async def source():
        yield AsyncFileSystemWrapper(backend, asynchronous=True)

    arguments = [command, "-R", "store:/bucket/docs"]
    if command == "cp":
        arguments.append("store:/out")
    result = CliRunner().invoke(
        App({"store": source}, capabilities={"recursion": {"remove": True}}).typer_app, arguments
    )
    assert result.exit_code == 0, result.stderr
    if command == "cp":
        assert backend.cat_file("/out/docs/nested/file") == b"payload"
        assert backend.isdir("/out/docs/empty")
        assert backend.cat_file("/bucket/docs/nested/file") == b"payload"
    else:
        assert not backend.exists("/bucket/docs")
        assert backend.isdir("/out")
