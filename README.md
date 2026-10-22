# fsspec-tools

Two Python libraries for working with [fsspec](https://filesystem-spec.readthedocs.io/)
filesystems, maintained in one [uv](https://docs.astral.sh/uv/) workspace.

| Package | Purpose | Documentation |
| --- | --- | --- |
| [`vosfs`](libs/vosfs/) | An asynchronous fsspec filesystem for OpenCADC VOSpace | [User guide](https://opencadc.github.io/fsspec-tools/guide/) |
| [`fss-cli`](libs/fss-cli/) | POSIX-shaped commands you embed in a Typer application, using your own filesystem instances | [Integration guide](https://opencadc.github.io/fsspec-tools/cli/integration/) |

The distributions are `vosfs` and `fss-cli`; their Python imports are `vosfs`
and `fss_cli`. Each package has its own version, changelog, and releases.
The workspace root is not a distribution, and fss-cli does not install a
standalone command.

## Develop

```bash
uv sync --locked --all-packages
uv run --all-packages pre-commit install --install-hooks --hook-type pre-commit --hook-type commit-msg
uv run --locked --package vosfs pytest libs/vosfs/tests
uv run --locked --package fss-cli pytest libs/fss-cli/tests
uv run --locked --all-packages zensical build --strict --clean
```

[CONTRIBUTING.md](CONTRIBUTING.md) documents the complete local validation gate.
CI tests Python 3.10–3.14 on Linux and Python 3.12 on macOS. The protected
`Required` check includes quality, both package suites, and isolated distribution
tests. Live VOSpace integration tests require separate credentials and are not
part of the offline CI gate.

## Project history

The packages originated in `shinybrar/vosfs`, then joined the `shinybrar/vostools`
workspace before moving here. Their original history and release tags are
preserved, along with relevant side branches and PR head refs under `archive/`.
The legacy Python vos package and its ancestry are excluded.

See the [migration record](docs/migration/README.md) for the verified commit/ref
maps and the [release guide](docs/releases.md) for publishing and recovery.
Architecture decisions are recorded in [docs/adr/](docs/adr/).
