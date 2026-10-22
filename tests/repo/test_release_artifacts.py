"""Release checks reject wrong distributions and conflicting retry artifacts."""

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from tools.release import inspect_distributions, verify_existing


def artifacts(
    directory: Path, *, name: str = "fss-cli", version: str = "0.11.0", requirement: str = "fsspec>=2026.6.0"
) -> None:
    metadata = f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\nRequires-Dist: {requirement}\n".encode()
    with zipfile.ZipFile(directory / "fss_cli-0.11.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr("fss_cli-0.11.0.dist-info/METADATA", metadata)
    with tarfile.open(directory / "fss_cli-0.11.0.tar.gz", "w:gz") as sdist:
        member = tarfile.TarInfo("fss_cli-0.11.0/PKG-INFO")
        member.size = len(metadata)
        sdist.addfile(member, io.BytesIO(metadata))


def test_distribution_pair_is_validated_and_hashed(tmp_path: Path) -> None:
    artifacts(tmp_path)
    hashes = inspect_distributions(tmp_path, "fss-cli", "0.11.0")
    assert len(hashes) == 2
    assert all(len(value) == 64 for value in hashes.values())
    verify_existing(hashes, dict(list(hashes.items())[:1]))


@pytest.mark.parametrize(
    "change",
    [{"name": "vos"}, {"version": "0.10.0"}, {"requirement": "vos>=3"}, {"requirement": "fsspec @ file:///tmp/source"}],
)
def test_wrong_metadata_is_rejected(tmp_path: Path, change: dict[str, str]) -> None:
    artifacts(tmp_path, **change)
    with pytest.raises(ValueError, match=r"artifact metadata|runtime dependency"):
        inspect_distributions(tmp_path, "fss-cli", "0.11.0")


def test_extra_artifacts_are_rejected(tmp_path: Path) -> None:
    artifacts(tmp_path)
    (tmp_path / "unexpected.whl").touch()
    with pytest.raises(ValueError, match="exactly one wheel"):
        inspect_distributions(tmp_path, "fss-cli", "0.11.0")


@pytest.mark.parametrize("remote", [{"package.whl": "different"}, {"other.whl": "same"}])
def test_retry_rejects_different_or_unexpected_published_files(remote: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="does not match"):
        verify_existing({"package.whl": "same"}, remote)


def test_final_verification_requires_the_complete_published_pair() -> None:
    local = {"package.whl": "wheel-hash", "package.tar.gz": "sdist-hash"}
    with pytest.raises(ValueError, match="every release artifact"):
        verify_existing(local, {"package.whl": "wheel-hash"}, require_complete=True)
    verify_existing(local, local, require_complete=True)
