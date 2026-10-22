"""Validate release distributions and reject conflicting existing index files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
import urllib.error
import urllib.request
import zipfile
from email.parser import BytesParser
from http import HTTPStatus
from pathlib import Path

INDEX_HOSTS = {"pypi": "pypi.org", "testpypi": "test.pypi.org"}
PACKAGES = ("vosfs", "fss-cli")


def inspect_distributions(directory: Path, package: str, version: str) -> dict[str, str]:
    """Check the package/version metadata and return each artifact's SHA-256."""
    if package not in PACKAGES or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        msg = "expected a supported package and a stable X.Y.Z version"
        raise ValueError(msg)
    files = list(directory.iterdir())
    wheels = [path for path in files if path.suffix == ".whl"]
    sdists = [path for path in files if path.name.endswith(".tar.gz")]
    if len(wheels) != 1 or len(sdists) != 1 or len(files) != len(wheels) + len(sdists):
        msg = "expected exactly one wheel and one sdist"
        raise ValueError(msg)
    with zipfile.ZipFile(wheels[0]) as wheel:
        metadata = [name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            msg = "wheel must contain exactly one distribution metadata record"
            raise ValueError(msg)
        wheel_metadata = wheel.read(metadata[0])
    with tarfile.open(sdists[0]) as sdist:
        metadata = [
            member for member in sdist.getmembers() if member.name.count("/") == 1 and member.name.endswith("/PKG-INFO")
        ]
        if len(metadata) != 1 or not metadata[0].isfile():
            msg = "sdist must contain one top-level PKG-INFO file"
            raise ValueError(msg)
        stream = sdist.extractfile(metadata[0])
        if stream is None:
            msg = "sdist metadata is unreadable"
            raise ValueError(msg)
        with stream:
            sdist_metadata = stream.read()
    for raw in (wheel_metadata, sdist_metadata):
        parsed = BytesParser().parsebytes(raw)
        name = re.sub(r"[-_.]+", "-", parsed.get("Name", "").lower())
        if name != package or parsed.get("Version") != version:
            msg = f"artifact metadata does not match {package} {version}"
            raise ValueError(msg)
        for requirement in parsed.get_all("Requires-Dist", []):
            dependency = re.split(r"[\s(<>=!~;\[]", requirement, maxsplit=1)[0].lower()
            if "@" in requirement or dependency == "vos":
                msg = f"unexpected runtime dependency: {requirement}"
                raise ValueError(msg)
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}


def verify_existing(local: dict[str, str], remote: dict[str, str], *, require_complete: bool = False) -> None:
    """Allow partial retries only when every existing file matches exactly."""
    for name, digest in remote.items():
        if local.get(name) != digest:
            msg = f"existing index file does not match the release artifacts: {name}"
            raise ValueError(msg)
    if require_complete and local.keys() != remote.keys():
        msg = "the index does not yet contain every release artifact"
        raise ValueError(msg)


def check_index(
    package: str, version: str, index: str, local: dict[str, str], *, require_complete: bool = False
) -> None:
    """Compare any published files with the validated local distributions."""
    url = f"https://{INDEX_HOSTS[index]}/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            release = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            if require_complete:
                msg = "the index does not yet contain this release"
                raise ValueError(msg) from error
            return
        raise
    verify_existing(
        local,
        {file["filename"]: file["digests"]["sha256"] for file in release["urls"]},
        require_complete=require_complete,
    )


def main() -> None:
    """Validate a release before its upload, optionally checking the target index."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--package", choices=PACKAGES, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--index", choices=INDEX_HOSTS)
    parser.add_argument("--require-published", action="store_true")
    args = parser.parse_args()
    if args.require_published and not args.index:
        parser.error("--require-published requires --index")
    hashes = inspect_distributions(args.dist, args.package, args.version)
    if args.index:
        check_index(args.package, args.version, args.index, hashes, require_complete=args.require_published)
    print(json.dumps(hashes, sort_keys=True))  # noqa: T201 - this command emits the verified artifact hashes.


if __name__ == "__main__":
    main()
