# Releasing vosfs and fss-cli

Each library has its own release-please PR, version, changelog, and PyPI project.
Tags are `vosfs-vX.Y.Z` and `fss-cli-vX.Y.Z`; GitHub release titles are
`vosfs: vX.Y.Z` and `fss-cli: vX.Y.Z`. Historical tags remain unchanged.

## Setup

Release-please uses GitHub's built-in `GITHUB_TOKEN` with Contents, Issues, and
Pull requests write permissions. Enable **Allow GitHub Actions to create and
approve pull requests** in the repository's Actions settings. No separate release
token is required.

Register these PyPI Trusted Publishers. Both use owner `opencadc`, repository
`fsspec-tools`, and workflow filename `pypi.yml`:

| PyPI project | GitHub environment |
| --- | --- |
| vosfs | `pypi-vosfs` |
| fss-cli | `pypi-fss-cli` |

For a new PyPI project, create a pending publisher in the maintaining account.
For an existing project, configure it in the project's Publishing settings.
Publishing uses OIDC; no PyPI API token is stored in GitHub.

## Automatic releases

1. Every push to `main`, including a PR merge, runs release-please.
2. Release-please opens or updates a release PR for each changed library.
3. Review and merge a release PR. Release-please creates its tag and draft release.
4. A repository dispatch starts `pypi.yml` with `package`, `tag_name`, and `sha`.
5. The publisher validates the tag, builds the package, and retains its wheel
   and sdist. It then waits **five minutes** before uploading to PyPI.
6. Published files are verified, attached to the GitHub release, and the draft
   is published.

The delay is a fixed `sleep 300`; the publisher does not poll other CI runs.
Review all applicable checks before merging a release PR. GitHub may require
approval to start CI on PRs created or updated using `GITHUB_TOKEN`; that is
separate from permission to create release PRs or run release-please on main.

Publication runs in one job, following CANFAR's dispatch-and-publish pattern.
The package source comes from the release tag. Publishing tools come from the
workflow's main revision, so an existing tag can use a corrected validator.
The package name, tag, commit ancestry, source version, manifest version,
lockfile, distribution metadata, and existing PyPI file hashes are checked.

The temporary first-release note correction preserves historical comparison
and source issue links. Remove its workflow steps, `tools/release_notes.py`,
`tools/release-origins.json`, `bootstrap-sha`, and `always-update` after both
libraries have completed their first releases from this repository.

## Recovery

Use **Publish to PyPI → Run workflow** on `main`. Select the package and its
original tag. If the previous run retained distributions, provide its
`artifact_run_id` to reuse those exact files:

```bash
gh workflow run pypi.yml --repo opencadc/fsspec-tools --ref main \
  -f package=fss-cli -f tag=fss-cli-v0.11.1 -f artifact_run_id=RUN_ID
```

Leave the run ID empty only when nothing was published or retained. Retained
artifacts are available for 90 days. Existing PyPI and GitHub files must match
the retained bytes; conflicting files are never overwritten. If artifacts have
expired, retrieve and verify the original distributions before recovery.

After a workflow fix, start a new run on main. Rerunning an old run uses its old
workflow definition. Recovery also waits five minutes before the publish step.

## Documentation

The documentation workflow deploys the commit that passed **Quality** on main.
Documentation deployment is independent of package releases.
