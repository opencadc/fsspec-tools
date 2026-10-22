# Transition vosfs and fss-cli to opencadc/fsspec-tools

This is the approved migration plan. The [implementation record](migration/README.md)
contains the completed history audit and transfer evidence; publishing activation
remains a post-merge step.
The repository remains **`opencadc/fsspec-tools`**. It will contain exactly two
Python distributions: **`vosfs`** and **`fss-cli`**.

The agreed history boundary excludes the legacy Python `vos` package's commits,
source files, and release tags. Relevant shared tooling and documentation history
is retained, including historical references to `vos`. The `vos` fsspec entry
point, `vos://` URLs, and references to the VOSpace server are valid parts of
`vosfs` and must remain.

## Recommendation

Use the original `shinybrar/vosfs` repository as the historical foundation, then
replay the relevant subsequent history from `shinybrar/vostools` onto it. Keep the
existing `libs/` workspace, uv tooling, Zensical documentation, and independent
release-please configuration, adapted for two packages.

This preserves the original package commits and historical tag objects exactly.
Only the subsequent commits that inherited `vos` ancestry need new commit IDs.
Their authors, timestamps, messages, retained file contents, and meaningful
parent relationships can be preserved. Signatures on rewritten commits cannot
remain valid; record provenance through a commit map instead.

Import the result into the existing destination through a genuine merge commit.
The destination's initial README/license commit can remain; no force-push or
replacement of its `main` is necessary. Do not squash or rebase the migration PR.

## Verified starting state

| Area | Current evidence | Consequence |
| --- | --- | --- |
| Destination | `opencadc/fsspec-tools`, `main` at `c59ea79`; README and AGPL license only | Preserve this initial commit when importing history. |
| Working source | `shinybrar/vostools`, `main` at `a172df16dfb51d311feb0088904668c677ac148d` | Freeze and recheck this SHA before execution. |
| Original source | `shinybrar/vosfs`, `main` at `054cfd9e1cd68081d23578595a9c5c16f70dee60` | Contains the original 155 commits and 25 historical tags. |
| Import boundary | `4a742888fff140e54be159933d5ed559275194ba` | Parents are legacy `ef9bf236…` and imported package tip `2596e0fc…`. |
| Source ancestry | 3,352 legacy commits, 155 imported commits, 16 subsequent commits on `main` | Exclude the entire legacy ancestor set, not just `libs/vos`. |
| Package versions | `vosfs` 0.11.0; `fss-cli` 0.10.0 | Preserve version continuity; neither value implies an existing PyPI publication. |
| Pending releases | [PR 28: vosfs 0.12.0](https://github.com/shinybrar/vostools/pull/28), [PR 29: fss-cli 0.11.0](https://github.com/shinybrar/vostools/pull/29) | Recreate release PRs in the destination after migration; these are not completed releases. |
| Historical releases | Original repository has 25 release records: 24 published, one draft (`v0.3.1`), 46 uploaded assets | Git tags alone do not transfer release notes or assets. |
| Source tags | No tags advertised by `shinybrar/vostools`; the local checkout has legacy `vos`/`vofs` tags | Fetch historical package tags from `shinybrar/vosfs`; never push the local tag collection wholesale. |
| PyPI | Public JSON endpoints for `vosfs` and `fss-cli` return 404; `fsspec-cli` is an unrelated 0.0.1 project | Plan first PyPI publications for both requested names. A 404 does not guarantee name availability. |
| CI | Linux Python 3.10–3.14 and macOS Python 3.12; shared quality checks and reusable package matrix exist | Reuse them, but fix the required-check dependency graph. |
| Required check | `quality.yml`'s `Required` job waits only for quality and PR-title jobs | Package-test failures currently do not fail this aggregator. |
| Documentation | Strict Zensical build exists; `docs.yml` does not upload or deploy a Pages artifact | Add deployment; changing the URL alone is insufficient. |
| Destination settings | One required approving review, no required status contexts, force pushes disabled, merge commits allowed | Add the final `Required` context after it has run successfully. |
| Destination hosting | No environments; Pages API returns 404; Actions enabled, default workflow token permission is write | Configure Pages and package publishing environments explicitly; use read-only defaults with scoped job permissions. |

Source configuration:
[workspace](https://github.com/shinybrar/vostools/blob/a172df16dfb51d311feb0088904668c677ac148d/pyproject.toml),
[release configuration](https://github.com/shinybrar/vostools/blob/a172df16dfb51d311feb0088904668c677ac148d/release-please-config.json),
[quality workflow](https://github.com/shinybrar/vostools/blob/a172df16dfb51d311feb0088904668c677ac148d/.github/workflows/quality.yml),
[publishing workflow](https://github.com/shinybrar/vostools/blob/a172df16dfb51d311feb0088904668c677ac148d/.github/workflows/pypi.yml),
[documentation workflow](https://github.com/shinybrar/vostools/blob/a172df16dfb51d311feb0088904668c677ac148d/.github/workflows/docs.yml).

## History strategy and local evidence

Three approaches were evaluated:

| Approach | Assessment |
| --- | --- |
| Copy the current files or squash-import the packages | Loses the requested development history. |
| Clone vostools and delete `libs/vos` | Retains all legacy ancestors and tags. Filtering only current package paths also risks losing earlier paths and shared history. |
| Preserve original vosfs history, then project subsequent vostools commits | Recommended. Preserves original commit/tag identity and isolates the relatively small mixed-history tail. |

An isolated local rehearsal used Git tree/object operations to reconstruct that
tail. Neither working checkout nor any remote was rewritten. For each retained
commit, it projected the complete source tree, rather than applying patches
whose context might depend on excluded files. It then exported only the candidate
branch and the original package tags into a fresh bare repository.

| Rehearsal assertion | Result |
| --- | --- |
| Original/imported histories correspond in author, committer, timestamps, parent graph, and blob inventory | All 155 commits matched. |
| Original commits retain their original IDs in the exported history | 155/155 preserved. |
| Subsequent `main` commits retain their selected file snapshots | 16/16 matched exactly. |
| Original tag references and tag-object IDs remain identical | 25/25 preserved, including the two annotated tags. |
| Exported `main` history before destination merge/cleanup | 171 commits. |
| Intersection with the 3,352-commit legacy ancestor set | Zero. |
| Historical `libs/vos`, `src/vos`, `vos`, `vofs` trees or legacy vos-only workflows | None found in retained snapshots. |
| Legacy boundary commit available as an object in the clean export | Absent. |
| `git fsck --full --no-reflogs` | Passed. |

The rehearsal tip was `da22a600bac8bcaf86703cc370a75912cc07c287`. It is evidence
of history separation, not a ready-to-publish tree: historical/current shared
configuration still needs the two-package cleanup described below.

The rehearsal covered `main` and historical release tags. It did **not** certify
every side branch. Several package branches contain commits that were squashed
before reaching `main`; for example, workspace integration has nine such commits
and transfer-fallback work has three. Preserve those histories through the branch
inventory and projection step below. Do not mistake 171 commits for the final
count across every retained ref.

## Execution sequence

### 1. Freeze, inventory, and back up

1. Record current remote SHAs, all heads/tags, open PRs, release metadata, and asset
   checksums for both sources and the destination. Recheck the audited SHAs.
2. Take complete, offline source backups and a destination backup. Backups may
   contain legacy history; they must never be pushed into the destination.
3. Build a ref-disposition table covering every source branch/tag: canonical
   `main`, preserved package/shared branch, archived generated branch, or excluded
   vos-only ref. Preserve relevant side branches under names such as
   `archive/vostools/fix/transfer-fallbacks`; never carry their unfiltered parents.
4. Preserve original vosfs development history as well as its release-tag history.
   Inventory its old `gh-pages` branch separately as generated documentation,
   without making it the new site's deployment branch.
5. Hold the two pending package release PRs during the cutover so source versions
   cannot change halfway through. Keep unrelated `vos` development outside this
   migration.

**Gate:** Every ref and outstanding package change has an explicit disposition;
there is no implicit loss of branch-only history.

### 2. Produce and audit the clean history

1. Start from the untouched original vosfs history and original tags.
2. Verify the original-to-imported mapping. For this snapshot, the original tip
   `054cfd9e…` maps to imported tip `2596e0fc…`.
3. Project the mixed-history tail and retained side branches. Keep both package
   trees, their earlier names, package docs, ADRs, tests, and relevant shared
   configuration. Remove legacy ancestors, vos source, vos-only README content,
   `ci-vos.yml`, and `cibuild.yml`.
4. Seed shared files from complete snapshots at the boundary. A simple path
   filter over commit deltas can omit shared files inherited from a removed
   parent; the local rehearsal deliberately avoided that failure mode.
5. Map retained parents to their reconstructed equivalents. Preserve meaningful
   package merges and integration commits. Do not import duplicate copies of the
   155-commit original lineage alongside its rewritten vostools copy.
6. Save `original → imported → destination` commit mappings and the ref manifest
   as migration provenance. Keep old issue/PR links pointing to their source
   repositories; original commit messages remain immutable.
7. Export only audited refs to a completely fresh repository. Do not carry
   staging remotes, replacement refs, backup refs, or unfiltered source branches.

Use Git's tree/commit plumbing or an equivalently verified `git-filter-repo`
transformation. The important contract is the resulting graph and every retained
snapshot, not a particular filtering one-liner. Rewrites change descendant IDs,
and partial ref filtering can mix old and new history; these behaviors require
explicit validation. See the
[git-filter-repo manual](https://github.com/newren/git-filter-repo/blob/main/Documentation/git-filter-repo.txt).

**Gate:** Repeat the rehearsal assertions across **all retained refs**, including
side branches and tags. Check full trees and known legacy commit identities;
searching commit subjects for the word `vos` is not an ancestry audit.

### 3. Finish the two-package workspace

Keep the existing layout and build backend:

```text
fsspec-tools/
  pyproject.toml                 # non-published workspace and shared tooling
  uv.lock
  release-please-config.json
  .release-please-manifest.json
  .github/workflows/
  docs/                         # site, ADRs, contributor/agent guidance
  tests/repo/                   # workspace and automation contracts
  libs/
    vosfs/
      pyproject.toml
      src/vosfs/
      tests/
      docs/                     # package design/research history
      README.md
      CHANGELOG.md
      LICENSE
    fss-cli/
      pyproject.toml
      src/fss_cli/
      tests/
      README.md
      CHANGELOG.md
      LICENSE
```

- Rename the unpublished root to `fsspec-tools-workspace`; retain
  `tool.uv.package = false` and explicitly list only `libs/vosfs` and
  `libs/fss-cli` as members.
- Preserve independent versions, changelogs, source layouts, and `uv_build`.
  Preserve `fss-cli` as a library without adding a new console command.
- Preserve `fss-cli`'s development dependency on the local `vosfs` workspace
  member. Neither distribution should acquire a runtime dependency on `vos`.
- Remove the vos type-checking exceptions, commit scopes, package CI, publishing
  entries, package contract expectations, and obsolete setup instructions.
- Regenerate `uv.lock` to remove the absent member and unused dependencies without
  turning the migration into an unrelated dependency-upgrade exercise.
- Update current project URLs, badges, instructions, repo guards, and tests to
  `opencadc/fsspec-tools`. Preserve historical changelog/research source links.
- Preserve current AGPL-3.0-or-later metadata and package licenses. Leave original
  release trees and their older licenses untouched.

Make these ordinary commits after the history import, so the historical record
continues to explain the layout and license transitions.

**Gate:** Exactly two buildable distributions; package implementation/tests match
the frozen source except for explicitly reviewed migration fixes.

### 4. Complete CI and artifact validation

Reuse the existing Python/platform matrix and reusable package-test workflow.
With only two packages, run both package suites on every PR and main push; this
avoids complicated path-dependent required checks. Run the existing scheduled
checks through the same orchestration.

Use one always-triggered CI workflow with quality, title validation, both package
jobs, artifact checks, and a final `Required` job. That final job must wait for
every applicable job and fail on a failure or cancellation. Only the PR-title
check may be intentionally skipped off PRs. Require this exact status context
in branch protection.

Retain lock validation, Ruff, formatting, ty, repository contract tests, strict
docs, and distribution metadata validation. Keep credentialed live VOSpace tests
separate from deterministic offline CI.

Add or restore the installed-artifact gate:

- Build one wheel and sdist per package using `uv build --no-sources`.
- Rebuild wheels from the sdists outside the checkout.
- Install each package in a clean environment with its declared dependencies;
  verify imports, versions, licenses, `vosfs`'s `vos` entry point, and absence of
  workspace/path dependencies in distribution metadata.
- Exercise the CLI library both without vosfs and with a separately installed
  vosfs wheel, using the existing offline adapter tests.
- Repair and wire in `libs/fss-cli/tests/_installed_wheel_gate.py`. Its distribution
  tests are skipped in ordinary pytest runs, and their current expected runtime
  dependency set omits `rich`, which the package now declares. Do not treat the
  existing green source-tree tests as proof that this gate is current.

The adapted local gate will include:

```bash
rtk proxy uv lock --check
rtk proxy uv run --locked --all-packages pre-commit run --all-files
rtk proxy uv run --locked pytest tests/repo
rtk proxy uv run --locked --package vosfs pytest libs/vosfs/tests
rtk proxy uv run --locked --package fss-cli pytest libs/fss-cli/tests
rtk proxy uv run --locked --all-packages zensical build --strict --clean
rtk proxy uv build --no-sources --all-packages
```

**Gate:** Both package matrices and clean-artifact checks feed the protected
`Required` result. Test the negative case: a package-test failure must prevent
merge even when quality passes.

### 5. Publish one documentation site

Keep Zensical and mkdocstrings. Move the public site from
`libs/vosfs/docs/user/` to a shared `docs/user/` directory in a normal move commit,
retaining the package research/design docs and ADRs. This gives both libraries a
shared documentation home and prevents CLI user-doc changes from being treated
as changes to the vosfs release component.

Move the current CLI-specific design docs from `libs/vosfs/docs/design/fss-cli/`
to `libs/fss-cli/docs/design/` as well. Fix relative links in the same commit;
historical research references can retain their recorded names and locations.

Set the site title to `fsspec-tools`, with clear vosfs and fss-cli navigation, and
the canonical URL to `https://opencadc.github.io/fsspec-tools/`. Keep strict builds
on PRs. Deploy successful main builds through GitHub Pages Actions, with a
`github-pages` environment and deployment concurrency that prevents an older
build from replacing a newer site. Do not couple documentation deployment to a
successful package release. Remove the unused mike version-provider setting
unless a real versioned-docs policy is implemented.

Pages deployment needs an uploaded Pages artifact and a deployment job with
`pages: write` and `id-token: write`; the current source workflow has neither.
See [GitHub's Pages workflow requirements](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

**Gate:** The deployed site serves both API references and user guides; navigation,
relative links, repository links, and the project subpath work in a browser.

### 6. Bootstrap independent release-please releases

Keep separate release PRs and only these components:

| Package path | Distribution | Future tag format | Initial manifest baseline |
| --- | --- | --- | --- |
| `libs/vosfs` | `vosfs` | `vosfs-vX.Y.Z` | `0.11.0` |
| `libs/fss-cli` | `fss-cli` | `fss-cli-vX.Y.Z` | `0.10.0`, inherited from its previous distribution name |

Remove `libs/vos` from configuration, manifests, workflow dispatch allowlists,
and tests. Keep the pre-1.0 breaking-change policy and per-package lock-version
updates, then validate each generated release PR with `uv lock --check`.

Replace the existing persistent `last-release-sha` with a one-time
`bootstrap-sha` pointing to the **mapped** equivalent of `e96b7630…`, immediately
before the unreleased relicensing and package-rename changes. Do not point it at
the migration tip: that would hide the unreleased changes. The old SHA is not a
valid release boundary in the reconstructed tail.

The distinction matters: `last-release-sha` remains active until removed, whereas
`bootstrap-sha` is ignored after release-please establishes its first release.
See the [release-please manifest documentation](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md).

The current expected first versions are **vosfs 0.12.0** and **fss-cli 0.11.0**,
matching the existing unmerged release PRs. Confirm them with a release-please
preview against the final configuration. Test a subsequent CLI-only change, a
vosfs-only change, and a change to both to verify independent version behavior.
Shared docs and repository maintenance should not accidentally release both.

Preserve the original historical tag names exactly: 13 `v*` tags and 12
`fsspec-cli-v*` tags. New component tag formats start with new releases. Do not
invent historical `fss-cli-v0.10.0` or retroactively rename older releases; repair
first-release comparison links to use the actual historical tags where needed.

Retain the built-in `GITHUB_TOKEN` initially. Current GitHub behavior creates
approval-required CI runs for PRs opened/updated by that token; document the
maintainer's **Approve workflows to run** action. If unattended release-PR CI
becomes a requirement, use a restricted GitHub App installation token. Explicit
`repository_dispatch` events work with the built-in token and can retain the
existing release-to-publish handoff. See
[GitHub's workflow-trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

**Gate:** Two correctly scoped release PRs, passing protected CI, correct versions,
fresh lock entries, accurate changelog links, and no historical-release replay.

### 7. Configure first PyPI publications and release recovery

Both project names currently lack public PyPI project records. Configure pending
Trusted Publishers, subject to checking project-name eligibility and the intended
maintaining account at cutover:

| PyPI project | GitHub owner/repository | Workflow | Environment |
| --- | --- | --- | --- |
| `vosfs` | `opencadc/fsspec-tools` | `pypi.yml` | `pypi-vosfs` |
| `fss-cli` | `opencadc/fsspec-tools` | `pypi.yml` | `pypi-fss-cli` |

If a project has appeared by execution time, configure its existing-project
publisher instead. Pending publishers create projects on first use; they do not
reserve names. See [PyPI's pending-publisher documentation](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

Keep the existing separation between unprivileged build, OIDC upload, and GitHub
release finalization. Adapt guards to the destination and allow only the two
package paths. Before publication, verify the tag resolves to the dispatched SHA,
the SHA belongs to approved main history, the package/manifest/artifact versions
match the tag, and CI has succeeded for that released commit. Build and validate
the immutable wheel/sdist pair once; retain those exact bytes for upload and
GitHub release assets. Only the upload job needs `id-token: write`.

Add a controlled retry entry point for an existing package/tag/SHA and retained
artifact. A failed upload, lost dispatch, or failed GitHub finalization must not
require another release version. After a partial upload, compare existing file
hashes before continuing; a name collision is not proof that the right bytes are
already present. Never overwrite or silently substitute a published artifact.

Configure a separate TestPyPI publisher/environment for the first end-to-end
rehearsal. TestPyPI success does not establish production PyPI authorization.
Verify the first production uploads through clean index installs, metadata, and
provenance. Finalize the GitHub release only after the intended artifacts are
confirmed on PyPI.

The packages have no runtime dependency on each other, so publication need not
be atomic or impose a provider-before-consumer order. Each must have its own
observable success and recovery state.

**Gate:** Both first production releases can be installed by their intended names;
their versions, imports, entry points, artifact hashes, and source provenance
match the approved release. Historical GitHub-only versions are not republished
as a side effect of importing their tags.

## Controlled cutover

1. Create the integration branch from the destination's existing `main`, merge
   the audited clean history with `--allow-unrelated-histories`, and resolve the
   README/license overlap deliberately. This gives the migration PR a common
   ancestor with the destination while preserving both histories. Append the
   ordinary workspace, CI, docs, and release-configuration commits. Keep release
   automation disabled with an explicit repository release-enable gate until
   setup is complete.
2. Temporarily disable destination Actions while importing historical tags and
   recreating archived release records/assets. Historical workflow files can be
   present at old refs; do not rely only on new workflow guards to suppress them.
3. Push only the audited migration branch, retained archive branches, and explicit
   tag allowlist. Do not use `git push --mirror` or unreviewed `--tags`.
4. Recreate the 24 published release records and the one draft with their original
   names, bodies, asset bytes, and draft/prerelease status. Preserve original dates
   and source URLs in the provenance record; new GitHub release IDs, API creation
   timestamps, and URLs cannot be identical to the old repository's. Verify all
   46 asset checksums. Do not rebuild historical artifacts.
5. Re-enable Actions with release publication still gated off. Run CI on the
   migration PR, establish the required status context, and obtain the repository's
   normal review. Merge with a real merge commit, retaining the imported graph.
6. Configure Pages, the two PyPI environments, pending publishers, and protected
   deployment/release permissions. Deploy and verify the docs, then enable
   release-please and package publishing after the TestPyPI rehearsal.
7. Complete and verify the two first releases. Replace superseded source release
   PRs with the destination release flow and update source repository guidance
   to point users at the canonical destination. Keep original repositories and
   their history available during the transition; do not rewrite them.

GitHub issues, PR discussions, approvals, Actions logs, repository settings,
secrets, and Pages configuration do not travel with Git commits or tags. Preserve
their source links and any required metadata exports. Do not promise to retain
their numeric identities or copy approvals to reconstructed PRs.

Before publication, rollback is to stop the new workflows and keep the old
repositories authoritative. After a successful PyPI upload, recovery uses the
existing immutable version/artifacts or a subsequent corrective release; it does
not reuse a version number with different contents.

## Work breakdown and completion criteria

Use one history-preserving migration PR containing small conventional commits:
history integration; two-package workspace cleanup; CI/artifact repair;
documentation; release/publishing adaptation; migration provenance. Keep service
configuration and the final release-enable action as explicit cutover steps.

The transition is complete when:

- All retained source refs are accounted for; original package history/tags and
  relevant side-branch histories survive; no legacy vos ancestors or source trees
  are reachable from any destination ref.
- Exactly two packages build and pass clean-install and supported-platform checks.
- The required CI result covers quality, both packages, docs, and artifacts.
- The new documentation site is deployed and verified.
- Historical tags, release records, and assets have been reconciled.
- Independent release-please PRs work from the correct historical baseline.
- Both new PyPI projects publish and install successfully under Trusted Publishing.

Only source inspection, live read-only repository/PyPI checks, and the disposable
main-history/tag rehearsal were performed for this plan. Side-branch migration,
the application test matrix, release-please previews against the new repository,
Pages deployment, authenticated PyPI ownership/name eligibility, and live
publication remain implementation and cutover gates.
