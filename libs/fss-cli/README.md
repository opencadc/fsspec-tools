# fss-cli

[![CI](https://github.com/opencadc/fsspec-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/opencadc/fsspec-tools/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/license-AGPL--3.0--or--later-blue)](LICENSE)

`fss-cli` provides POSIX-shaped [Typer](https://typer.tiangolo.com/) commands
for async [`fsspec`](https://github.com/fsspec/filesystem_spec) filesystems.
Your application configures the filesystems and embeds the commands in its CLI.
The package installs no executable or module entry point.

Releases up to 0.10.0 were named `fsspec-cli`, imported as `fsspec_cli`. See
[ADR 0010](../../docs/adr/0010-rename-fsspec-cli-to-fss-cli.md).

## Install

```bash
uv add "git+https://github.com/opencadc/fsspec-tools@main#subdirectory=libs/fss-cli"
```

## Quick start

```python
from contextlib import asynccontextmanager

import fsspec
import typer
from fsspec.implementations.asyn_wrapper import AsyncFileSystemWrapper
from fss_cli import App


@asynccontextmanager
async def data_source():
    # One fresh async-capable filesystem per command invocation.
    yield AsyncFileSystemWrapper(fsspec.filesystem("memory"))


app = typer.Typer()
app.add_typer(App({"data": data_source}).typer_app, name="fs")

if __name__ == "__main__":
    app()
```

Operands use `name:/path` to select a configured source:

```bash
python app.py fs ls data:/
```

The example uses an in-memory filesystem. The
[overview](https://opencadc.github.io/fsspec-tools/cli/) shows how to configure
local disk and a remote VOSpace archive. With sources named `local` and `archive`,
copy a file between them with:

```bash
python app.py fs cp local:/results.csv archive:/2026/results.csv
```

## Commands

`ls` · `du` · `find` · `tree` · `size` · `test` · `info` · `stat` ·
`head` · `tail` · `cat` · `cp` · `mv` · `mkdir` · `rmdir` · `unlink` · `rm`.

Recursive `cp -R` is available by default. Enable recursive `rm -R` explicitly:

```python
App({"data": data_source}, capabilities={"recursion": {"remove": True}})
```

## Public API

`App`, `AppCapabilities`, `RecursionCapabilities`, `AsyncFilesystemSource`,
`CommandCallback`, and `CommandContext`.

## Documentation

| For | Read |
| --- | --- |
| Embedding it: sources, lifecycle, capabilities, exit statuses | [Integration guide](https://opencadc.github.io/fsspec-tools/cli/integration/) |
| What each command does | [Command reference](https://opencadc.github.io/fsspec-tools/cli/commands/) |
| The public API | [API reference](https://opencadc.github.io/fsspec-tools/cli/api-reference/) |
| The command contract and its rationale | [`docs/design/`](docs/design/) |
| Architecture decisions | [`docs/adr/`](../../docs/adr/) |

## Scope

`fss-cli` uses familiar shell layouts for backend metadata and marks missing
values as unknown. It does not claim POSIX, GNU, BSD/macOS, or all-fsspec
compatibility. Supported host platforms are Linux and macOS.

## License

Copyright (c) 2026 National Research Council of Canada / Government of Canada.

`fss-cli` is distributed under the terms of the
[GNU Affero General Public License v3.0 or later](LICENSE) (AGPL-3.0-or-later).
`fss-cli` 0.10.0 and earlier releases were published under the BSD 3-Clause
License.

## Long listings and repeated copies

`ls -l` keeps shell column order even when metadata is sparse. Unknown scalar
fields show `-`, unknown permission bits show `?`, and old dates show the year.
VOSpace access groups share one field (`r=OSSOS,w=NONE`) rather than implying
POSIX group ownership; raw access and lock metadata remain available in `info`.

Recursive `cp -R` skips files only after compatible MD5 metadata or staged
SHA-256 comparison establishes equality. Equal size alone is insufficient.
Without content checksums, comparison downloads both files. If their contents
differ, the upload reuses the staged source bytes.
