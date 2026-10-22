# vosfs

[![CI](https://github.com/opencadc/fsspec-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/opencadc/fsspec-tools/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/license-AGPL--3.0--or--later-blue)](LICENSE)

`vosfs` is an asynchronous [`fsspec`](https://filesystem-spec.readthedocs.io/)
filesystem for OpenCADC Cavern VOSpace. It registers the `vos` protocol so
fsspec-aware tools can read, write, inspect, and manage VOSpace files and
directories. Supported tools include pandas, NumPy, Dask, Zarr, and PyArrow.

Supported host platforms are Linux and macOS. Other platforms are untested and
unsupported.

## Install

```bash
uv add "git+https://github.com/opencadc/fsspec-tools@main#subdirectory=libs/vosfs"
```

## Quick start

The synchronous fsspec API uses async network I/O internally. To authenticate,
set `VOSFS_CERT_FILE` to a combined proxy-certificate and private-key PEM file:

```bash
export VOSFS_CERT_FILE=/absolute/path/to/cadcproxy.pem
```

```python
import fsspec

fs = fsspec.filesystem("vos", endpoint_url="https://staging.canfar.net/arc")
try:
    print(fs.ls("/home/<cadc-username>"))
finally:
    fs.close()
```

## Capabilities

| fsspec operation | Support |
| --- | --- |
| `ls`, `info`, `exists`, `walk`, `find`, `glob` | Listing and metadata |
| `cat_file`, `cat_ranges` | Response-validated HTTP ranges with whole-object fallback |
| `get`, `open("rb")` | Whole-object downloads; `open` stages to disk by default and uses ranges when `block_size` or `cache_type` is supplied |
| `pipe_file`, `put`, `open("wb")` | Whole-object staged writes |
| `mkdir`, `makedirs`, `rm`, `rmdir` | Namespace creation and deletion |
| `cp` | Client-side copy; an internal same-authority LinkNode materializes target bytes, while an external or non-VOS LinkNode raises `NotImplementedError` before mutation |
| `mv` | Same-service `moveNode` job when available; otherwise copy, verify, then delete. LinkNode moves raise `NotImplementedError` before mutation |
| Append/update modes, FUSE | Unsupported |

`vosfs` targets the OpenCADC VOSpace profile only; it does not claim generic
IVOA VOSpace 2.1 conformance. The full capability contract and fsspec support
matrix are in
[`docs/design/trd.md`](docs/design/trd.md).

## Documentation

The [vosfs documentation](https://opencadc.github.io/fsspec-tools/) contains the user
guide, [recipes](../../docs/user/recipes.md),
[troubleshooting](../../docs/user/troubleshooting.md), the public API reference, and
the [`fss-cli`](../../docs/user/cli/index.md) integration guide.

The design contract for `fss-cli` lives in
[`libs/fss-cli/docs/design/`](../fss-cli/docs/design/) and the architecture
decisions in [`docs/adr/`](../../docs/adr/).

See [CONTRIBUTING.md](../../CONTRIBUTING.md) to work on the project. Public
documentation source lives under `docs/user/`;
validate it locally from the repository root with:

```bash
uv run --all-packages zensical build --strict --clean
```

## License

Copyright (c) 2026 National Research Council of Canada / Government of Canada.

`vosfs` is distributed under the terms of the
[GNU Affero General Public License v3.0 or later](LICENSE) (AGPL-3.0-or-later).
`vosfs` 0.11.0 and earlier releases were published under the BSD 3-Clause
License.
