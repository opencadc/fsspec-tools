"""Commands retain sources until an adapted filesystem's worker finishes."""

import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fsspec.implementations.asyn_wrapper import AsyncFileSystemWrapper
from fsspec.implementations.local import LocalFileSystem
from typer.testing import CliRunner

from fss_cli import App


@pytest.mark.parametrize(
    ("hook", "arguments"),
    [
        ("rm_file", ["unlink", "file"]),
        ("rm_file", ["rm", "file", "other"]),
        ("rmdir", ["rmdir", "empty"]),
        ("rmdir", ["rm", "-d", "empty"]),
        ("mkdir", ["mkdir", "new"]),
        ("makedirs", ["mkdir", "-p", "new"]),
        ("info", ["unlink", "file"]),
        ("info", ["info", "file"]),
        ("info", ["stat", "file"]),
        ("size", ["size", "file"]),
        ("sizes", ["size", "file", "other"]),
        ("exists", ["test", "-e", "file"]),
        ("isfile", ["test", "-f", "file"]),
        ("isdir", ["test", "-d", "empty"]),
        ("cat_file", ["head", "-c", "2", "file"]),
        ("cat_file", ["tail", "-c", "2", "file"]),
        ("get_file", ["cat", "file"]),
    ],
)
def test_cancelled_command_drains_worker_before_source_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook: str, arguments: list[str]
) -> None:
    (tmp_path / "file").write_bytes(b"payload")
    (tmp_path / "other").write_bytes(b"untouched")
    (tmp_path / "empty").mkdir()
    events = []

    @asynccontextmanager
    async def source():
        loop = asyncio.get_running_loop()
        owner = asyncio.current_task()
        assert owner is not None
        released = threading.Event()
        local = LocalFileSystem(skip_instance_cache=True)
        original = getattr(local, hook)

        def cancel_then_release() -> None:
            owner.cancel()
            loop.call_soon(released.set)

        def blocked(*args, **kwargs):
            loop.call_soon_threadsafe(cancel_then_release)
            assert released.wait(timeout=2)
            result = original(*args, **kwargs)
            events.append("worker finished")
            return result

        monkeypatch.setattr(local, hook, blocked)
        try:
            yield AsyncFileSystemWrapper(local, asynchronous=True)
        finally:
            events.append("source exited")

    operands = {"file", "other", "empty", "new"}
    command = [f"local:{tmp_path / value}" if value in operands else value for value in arguments]
    with pytest.raises(asyncio.CancelledError):
        CliRunner().invoke(App({"local": source}).typer_app, command)

    assert events == ["worker finished", "source exited"]
    assert (tmp_path / "other").read_bytes() == b"untouched"
