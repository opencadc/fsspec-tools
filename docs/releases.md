# Releasing vosfs and fss-cli

Each package has its own release-please PR, version, changelog, and PyPI project.
Future tags are `vosfs-vX.Y.Z` and `fss-cli-vX.Y.Z`. Historical `v*` and
`fsspec-cli-v*` tags remain unchanged and never trigger the new publisher.
GitHub release titles are `vosfs: vX.Y.Z` and `fss-cli: vX.Y.Z`, including
historical releases. Spaces and colons belong to the title, not the Git tag.

## Publishing setup

Register a GitHub Trusted Publisher for each package on PyPI. For a new project,
use a pending publisher in the maintaining account; for an existing project,
configure its publisher under the project's Publishing settings. Pending
publishers do not reserve a project name.

Every publisher uses owner `opencadc`, repository `fsspec-tools`, and workflow
filename `pypi.yml`. The environment must match its package and index:

| Package | Production environment | Optional test environment |
| --- | --- | --- |
| vosfs | `pypi-vosfs` | `testpypi-vosfs` |
| fss-cli | `pypi-fss-cli` | `testpypi-fss-cli` |

Set `RELEASE_ENABLED=true` to enable release-please and `PYPI_ENABLED=true` to
allow production uploads. Missing or false variables leave the corresponding
automation disabled. TestPyPI registration is needed only for a TestPyPI run.

Configure `RELEASE_PLEASE_TOKEN` before enabling release-please, as described
below. Review the independent release PRs after their CI checks pass.
Merging a release PR creates its tag and draft release, then
starts publishing automatically. Production publication waits for successful
main CI on the exact tagged commit. No PyPI API token is required.

For an optional rehearsal, keep `PYPI_ENABLED=false`, merge a release PR, and
run **Publish to PyPI** on `main` with its tag and index `testpypi`. After checking
the install, enable production and dispatch the same tag to `pypi`, supplying
the successful TestPyPI run's `artifact_run_id` to reuse the tested files.

## Automatic CI for release PRs

Release-please and the initial release-note correction both use the repository
secret `RELEASE_PLEASE_TOKEN`. GitHub requires approval for PR workflows triggered
by its built-in `GITHUB_TOKEN`; a separate release token lets those workflows
start automatically. The release workflow fails with a setup error when this
secret is missing rather than silently falling back to `GITHUB_TOKEN`.

Create a fine-grained personal access token with resource owner `opencadc`,
access only to `fsspec-tools`, and these repository permissions:

- Contents: read and write, for release branches, changelogs, tags, and releases.
- Pull requests: read and write, for release PRs and their descriptions.
- Issues: read and write, for release-please labels.

Add it as `RELEASE_PLEASE_TOKEN` in the repository's Actions secrets. If the
organization requires token approval, an organization owner must approve it.
Record its expiration and rotate the secret before it expires. Do not place the
token in repository files or share it in an issue, PR, or chat.

Use the same secret for both steps that change release PRs; leaving the
note-correction step on `GITHUB_TOKEN` would trigger another approval-required
CI run. Publication dispatch continues to use `GITHUB_TOKEN`, since explicit
repository-dispatch events run automatically. PyPI authentication still uses OIDC.

The one-time `bootstrap-sha` maps the last pre-relicensing formatting commit into
the reconstructed history. Release-please must include the unreleased license,
rename, and transfer changes. Once both components have a successful release,
remove the bootstrap entry, temporary `always-update` option, release-note workflow
steps, `tools/release_notes.py`, and `tools/release-origins.json`. Do not replace the
bootstrap with `last-release-sha`, which would keep overriding future release boundaries.

The temporary release-note correction runs after each initial release PR is
created or updated. It uses actual historical comparison tags and the commit
origins in `tools/release-origins.json` to preserve source issue/PR links. It corrects
both the generated PR body and its new changelog section. It leaves later releases and older
changelog sections untouched. The temporary `always-update` option makes the
action return initial PRs on retries even if a previous correction failed before
changing the generated body.

## Normal releases

Release-please runs automatically on every push to `main`, including PR merges.
PR creation and synchronization do not trigger it; it has no manual trigger.
It opens one PR per changed component. Its Python
strategy updates the package metadata and changelog; configured extra files
update that package's lockfile version. CI checks the lock remains consistent.

After a release PR merges, release-please tags a draft release and dispatches
`pypi-release` to `pypi.yml`, following CANFAR's repository-dispatch pattern.
Each component sends its own payload containing only `tag_name` and `sha`.
The publisher derives the package and version from the tag and checks that the
payload SHA matches its commit. It also checks main ancestry, source and manifest
versions, and successful main CI for that commit before building.

The workflow has three jobs: prepare the distributions, upload through OIDC,
then verify the published files and finalize the GitHub release. Only the upload
job receives an OIDC token. Package source is checked out in `release-source/`
at the tagged commit; publishing tools come from the workflow's main revision,
so an older release can use a corrected validator without changing its tag.

The build retains exactly one wheel and one sdist for 90 days. Their metadata and
hashes are checked before upload. Finalization verifies that every index file
matches the retained bytes.
Production success then attaches those same files to the GitHub release and
publishes the draft. TestPyPI never finalizes a GitHub
release. The libraries have no runtime dependency on each other, so they release
independently.

## Recover an interrupted release

Run **Publish to PyPI** on `main` with the original tag and index. The tag
identifies the package, version, and commit; there is no separate package or SHA
input. For example:

```bash
gh workflow run pypi.yml --repo opencadc/fsspec-tools --ref main \
  -f tag=fss-cli-v0.11.0 -f index=pypi
```

If the failed run retained distributions, supply its `artifact_run_id` so recovery
uses the exact files. If no files were uploaded or retained, leave that input
empty to build from the unchanged tag. When fixing the workflow or its tools,
start a new run on main: rerunning an old run uses its old workflow revision.

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
must establish the production Trusted Publishers in the intended PyPI account
before enabling production uploads. TestPyPI publishers are configured separately
when a rehearsal is wanted.
