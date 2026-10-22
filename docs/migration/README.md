# Package history migration

The migration preserves vosfs and fss-cli development history while removing the
legacy Python vos package's ancestry. Shared tooling and documentation may still
mention vos historically; the `vos` protocol entry point remains part of vosfs.

## Frozen sources

| Source | Main commit |
| --- | --- |
| `shinybrar/vosfs` | `054cfd9e1cd68081d23578595a9c5c16f70dee60` |
| `shinybrar/vostools` | `a172df16dfb51d311feb0088904668c677ac148d` |
| Initial `opencadc/fsspec-tools` | `c59ea79d98b725b2c0350901916e9f106d0c7912` |

Original repository commits and tags retain their object IDs. The mixed-history
vostools tail is reconstructed from complete file snapshots, preserving authors,
timestamps, messages, retained file modes/content, and applicable parents.
Rewritten commits have new IDs and cannot retain their former signatures.

The destination's initial commit and the reconstructed package history are joined
by a merge commit. **Merge this migration PR using a merge commit.** Squashing or
rebasing would disconnect the imported history from main.

## Audit results

| Check | Result |
| --- | --- |
| Original commits preserved exactly across branches, tags, and PR refs | 706 |
| Original main commits within that history | 155 |
| Subsequent relevant vostools commits reconstructed | 45 |
| Distinct commits in the clean package export | 751 |
| Excluded legacy vos commits, including its side branches | 3,377 |
| Intersection with excluded commit identities | 0 |
| Original release tags preserved exactly | 25 |
| Original refs preserved | 211 |
| Relevant vostools refs preserved | 31 |
| Vos-only vostools refs excluded | 23 |
| Retained full-tree projections compared against source | All matched |
| Historical vos source trees and legacy publishing workflows | None retained |
| Git object/connectivity check | Passed |

The single `archive/history` branch retains original development branches and
GitHub PR refs through an archival merge commit, including work that was squashed
before reaching main. The original ref names and their retained commit IDs are
recorded in the manifest. The generated gh-pages history is retained there too;
the current documentation site deploys through Actions from main instead.

The 217 temporary archive branches were consolidated at the user's request only
after verifying every historical tip remained reachable. The 25 release tags
were not changed.

The 751-commit count describes the clean export, before the destination's initial
commit, integration merge, and implementation commits are added.

## Provenance files

- [history-audit.json](history-audit.json) records the frozen inputs and checks.
- [history-refs.json](history-refs.json) records every source ref's disposition,
  source SHA, retained object SHA, and destination ref. For archive entries,
  `retained_sha` is the historical tip reachable through `archive/history`, not
  the current tip of that shared archival branch.
- [history-commits.json](history-commits.json) maps original vosfs commits to the
  earlier imported copies, and those imported/later vostools commits to their
  destination IDs.
- [releases.json](releases.json) records original and destination release URLs,
  original timestamps, and the 46 byte-verified asset hashes. All 24 published
  records and the one draft were transferred without rebuilding their assets.

Old issue/PR numbers in immutable commit messages refer to their original
repositories. GitHub discussions, reviews, and Actions logs remain at those
source URLs; they are not Git objects and are not represented as new approvals.

All source refs were backed up before reconstruction. Only the audited export
was fetched into this repository; staging repositories, legacy refs, and
replacement refs were not imported.

The original [migration plan](../migration-plan.md) records the investigation and
cutover gates. The [release guide](../releases.md) describes the post-merge
publishing setup. Preserve the historical tags and archived refs unchanged.
