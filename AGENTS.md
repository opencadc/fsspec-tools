# Working in fsspec-tools

This is a uv workspace containing `vosfs` (`libs/vosfs`) and `fss-cli`
(`libs/fss-cli`). Both are Python libraries. The root is not published.

- Work on a branch and use conventional commit messages.
- Use `uv sync --locked --all-packages` to install the workspace and tools.
  CI runs hooks with `uv run --locked --all-packages`.
- Run the complete local validation gate in `CONTRIBUTING.md` before opening
  or updating a PR. Never bypass hooks with `--no-verify`.
- Tests are deterministic and offline. Do not supply CADC credentials to CI.
- Shared user documentation is in `docs/user/`; build it with
  `uv run --locked --all-packages zensical build --strict --clean`.
- Do not commit generated `site/`, `dist/`, or environment files.
- Preserve the original historical tags and the `archive/history` branch. The migration PR
  must be merged with a merge commit to retain its imported ancestry.

Read `libs/vosfs/docs/CONTEXT.md` for domain terminology and relevant decisions
under `docs/adr/`. Issue handling is documented in `docs/agents/issue-tracker.md`
and `docs/agents/triage-labels.md`.
