# Releasing vosfs and fss-cli

Each package has its own release-please PR, version, changelog, and PyPI project.
Future tags are `vosfs-vX.Y.Z` and `fss-cli-vX.Y.Z`. Historical `v*` and
`fsspec-cli-v*` tags remain unchanged and never trigger the new publisher.

## Initial setup after the migration PR merges

The repository starts with both `RELEASE_ENABLED` and `PYPI_ENABLED` set to
`false`. Missing variables also leave automation disabled.

1. Verify the protected `Required` check passes on main and the documentation
   deploys to `https://opencadc.github.io/fsspec-tools/`.
2. Configure pending Trusted Publishers in the maintaining accounts on PyPI and
   TestPyPI. If a project already exists, configure its existing publisher instead.
   A pending publisher does not reserve a project name.
3. Bind each publisher to owner `opencadc`, repository `fsspec-tools`, workflow
   `pypi.yml`, and its exact environment from the table below.
4. Set `RELEASE_ENABLED=true` and run the Release workflow (or make the next
   normal main push). Review the two independent release PRs and approve their
   CI workflows if GitHub requests it. Keep `PYPI_ENABLED=false` during rehearsal.
5. Merge a reviewed release PR. Release-please creates its tag and draft GitHub
   release. The gated production publisher will not upload yet.
6. Run **Publish to PyPI** manually on `main`, selecting `testpypi`, the package,
   its existing release tag, and the tag's full commit SHA. Verify the TestPyPI
   install. Retain the successful run ID and distribution hashes.
7. Set `PYPI_ENABLED=true`. Run the same workflow with index `pypi` and
   `artifact_run_id` set to that TestPyPI run ID. This uploads the exact tested
   distributions. Verify the production install and provenance for each package.

| Package | Production environment | Test environment |
| --- | --- | --- |
| vosfs | `pypi-vosfs` | `testpypi-vosfs` |
| fss-cli | `pypi-fss-cli` | `testpypi-fss-cli` |

The first expected versions are vosfs 0.12.0 and fss-cli 0.11.0. The manifest's
fss-cli 0.10.0 is version continuity from the former fsspec-cli distribution; it
does not claim a previous fss-cli PyPI publication. Do not create a fictional
historical fss-cli 0.10.0 release to make a comparison link work.

The one-time `bootstrap-sha` maps the last pre-relicensing formatting commit into
the reconstructed history. Release-please must include the unreleased license,
rename, and transfer changes. Once both components have a successful release,
the bootstrap entry can be removed. Do not replace it with `last-release-sha`,
which would keep overriding future release boundaries.

## Normal releases

Release-please runs on main and opens one PR per changed component. Its Python
strategy updates the package metadata and changelog; configured extra files
update that package's lockfile version. CI checks the lock remains consistent.

After a release PR merges, release-please tags a draft release and dispatches
that package to `pypi.yml`. Publication checks the package allowlist, tag/commit
identity, ancestry on main, source and manifest versions, and successful CI for
that commit before building. Only the isolated upload job receives an OIDC token.

The build retains exactly one wheel and one sdist for 90 days. Their metadata and
hashes are checked before upload. A separate job verifies that every index file matches the retained bytes.
Production success then attaches those same files to the GitHub release and
publishes the draft. TestPyPI never finalizes a GitHub
release. The libraries have no runtime dependency on each other, so they release
independently.

## Recover an interrupted release

Use **Re-run failed jobs** when the original workflow run is available. To recover
through a new run, dispatch `pypi.yml` on main with the same package, tag, SHA,
and index, supplying the original build run's `artifact_run_id`.

Recovery downloads the retained artifact for that exact package/SHA instead of
rebuilding it. Existing index files must match its SHA-256 hashes; only matching
files may be skipped during a partial retry. Existing GitHub assets are also
compared byte-for-byte by hash, and are never overwritten. A conflicting artifact
fails the workflow and requires investigation.

If retained artifacts have expired, retrieve and verify the original release
files before attempting recovery. Do not upload a fresh rebuild over a partially
published version. A correction to released code requires a new version.

## Documentation

Documentation deploys separately after successful main CI. It uses the
`github-pages` environment and a single deployment concurrency group. It is not
held up by a package release or a publishing failure.

## External requirements

GitHub repository access does not configure a PyPI account. A project maintainer
must establish the Trusted Publishers in the intended PyPI/TestPyPI accounts
before enabling production uploads. The release-enable variables intentionally
remain false while the migration is under review.
