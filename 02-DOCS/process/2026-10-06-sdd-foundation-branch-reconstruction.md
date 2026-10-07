# Process report — SDD foundation branch reconstruction

This is a process report for human and external review. It is not an authoritative
requirements document and does not replace project requirements, the constitution,
the SDD decision log, or later SDD artifacts.

## Date, branch, and objective

- Date: 2026-10-06 (UTC-6)
- Active branch: `chore/sdd-foundation`
- Base commit: `c476d82787976b015a66fbb2a1454084d8e478de`
- Former automatic-history HEAD: `dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea`
- Backup branch: `chore/sdd-foundation-auto-backup`
- Objective: preserve the automatic commit chain for audit, rebuild the active
  branch from the base commit, and leave the approved SDD foundation uncommitted

No SDD phase was run. No commit, push, PR, merge, rebase, tag, release, remote
branch deletion, or modification to `origin/rsc/knowledge` was performed.

## Why reconstruction was performed

rsc-harness knowledge sync automatically committed changes under
`02-DOCS/wiki/` after agent turns, despite the human instruction to leave changes
uncommitted for review.

Knowledge sync was disabled and verified `opted-out` first. The human then
explicitly authorized local branch reconstruction so the approved SDD foundation
would appear only as working-tree and untracked changes.

## Preflight

### Initial status

```text
## chore/sdd-foundation
 M .rsc.json
?? 02-DOCS/process/
?? CLAUDE.md
```

### Initial history

```text
* dfaf562 (HEAD -> chore/sdd-foundation) 📝 docs(auto): constitution, decisions, index [skip ci]
* 183f612 📝 docs(auto): constitution, decisions [skip ci]
* ed75d34 📝 docs(auto): config, constitution, decisions y 1 más [skip ci]
*   c476d82 (origin/main, main) Merge pull request #1 from Helysalgado/chore/rsc-harness-setup
|\
| * 37ba01c (origin/chore/rsc-harness-setup) chore: initialize rsc harness
|/
* e23a6f2 docs: establish promoter extraction requirements
```

### Knowledge-sync check

```json
{
  "active": false,
  "reason": "opted-out",
  "branch": "chore/sdd-foundation",
  "defaultBranch": "main",
  "exchangeBranch": "rsc/knowledge",
  "queued": 0,
  "pendingNotices": 0,
  "lastFetch": "2026-10-07T01:04:32.522Z",
  "paths": [
    "01-TOOLS/",
    "02-DOCS/wiki/",
    "02-DOCS/attachments/"
  ],
  "neverSynced": [
    "02-DOCS/wiki/harness/user-profile.md"
  ]
}
```

Reconstruction proceeded because status was inactive with reason `opted-out`.

## Automatic history preserved

The local backup branch was created before changing the active branch:

```text
chore/sdd-foundation-auto-backup
  -> dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea
```

It was not pushed.

The backup branch retains:

```text
dfaf562  📝 docs(auto): constitution, decisions, index [skip ci]
183f612  📝 docs(auto): constitution, decisions [skip ci]
ed75d34  📝 docs(auto): config, constitution, decisions y 1 más [skip ci]
```

## Protection mechanism for working-tree and untracked files

A named local stash including untracked files was used:

```sh
git stash push --include-untracked \
  --message 'pre-sdd-foundation-reconstruction-2026-10-06'
```

This protected:

- tracked `.rsc.json` knowledge-sync opt-out;
- all Markdown reports under `02-DOCS/process/`;
- untracked `CLAUDE.md`.

The ignored `.rsc/.no-knowledge-sync` sentinel was not included by `-u`; it
remained in place throughout reconstruction.

After the approved files were restored, the stash was applied:

```sh
git stash pop stash@{0}
```

It applied cleanly and was dropped:

```text
Dropped stash@{0} (6db20c1178621347e01a566aac9c8cf2720366e7)
```

No protected file was lost or overwritten.

## Active branch reconstruction

After the backup branch and stash existed, the active branch was moved to the
approved base:

```sh
git reset --hard c476d82787976b015a66fbb2a1454084d8e478de
```

Output:

```text
HEAD is now at c476d82 Merge pull request #1 from Helysalgado/chore/rsc-harness-setup
```

This reset was the explicitly authorized local history reconstruction. It did not
delete the old commits because the backup branch already referenced `dfaf562`.

## Approved artifacts restored

Only the final approved versions were restored from `dfaf562` into the working
tree, without staging or committing:

```sh
git restore \
  --source=dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea \
  --worktree -- \
  02-DOCS/wiki/sdd/config.yaml \
  02-DOCS/wiki/sdd/constitution.md \
  02-DOCS/wiki/sdd/decisions.md \
  02-DOCS/wiki/index.md
```

Blob identity proves the restored files exactly match the final approved state:

```text
config current=cbd5ff45a9a59beb4476931c09c546199de8e513
config source=cbd5ff45a9a59beb4476931c09c546199de8e513

constitution current=d04d57e1bf5063ba460b0b5340c9a900bdab6671
constitution source=d04d57e1bf5063ba460b0b5340c9a900bdab6671

decisions current=526d849005905a52d131188b8d835208a5be50a8
decisions source=526d849005905a52d131188b8d835208a5be50a8

index current=a248d93dd793fc63199162dc4204a482f90264a3
index source=a248d93dd793fc63199162dc4204a482f90264a3
```

The prior `.rsc.json` opt-out and all existing process reports and `CLAUDE.md`
were restored by the stash.

## Final branch references

```text
chore/sdd-foundation
  -> c476d82787976b015a66fbb2a1454084d8e478de

chore/sdd-foundation-auto-backup
  -> dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea

main
  -> c476d82787976b015a66fbb2a1454084d8e478de

origin/rsc/knowledge
  -> 11afb35da8cab0ff5e0c84fb65aeba85e9e5f14a
```

## Review bundle

### A. `git status --short --branch`

```text
## chore/sdd-foundation
 M .rsc.json
?? 02-DOCS/process/
?? 02-DOCS/wiki/index.md
?? 02-DOCS/wiki/sdd/
?? CLAUDE.md
```

This report adds another untracked file under `02-DOCS/process/`.

### B. `git log --oneline --decorate --graph -10`

```text
*   c476d82 (HEAD -> chore/sdd-foundation, origin/main, main) Merge pull request #1 from Helysalgado/chore/rsc-harness-setup
|\
| * 37ba01c (origin/chore/rsc-harness-setup) chore: initialize rsc harness
|/
* e23a6f2 docs: establish promoter extraction requirements
```

The active branch contains no `docs(auto)` commit and no new commit.

### C. `git branch --contains dfaf562`

```text
  chore/sdd-foundation-auto-backup
```

Only the backup branch contains `dfaf562`.

### D. `git diff --stat`

```text
 .rsc.json | 1 +
 1 file changed, 1 insertion(+)
```

`git diff --stat` does not include untracked SDD artifacts. They are listed in
section F.

### E. `git diff`

```diff
diff --git a/.rsc.json b/.rsc.json
index 6de0965..a8152c3 100644
--- a/.rsc.json
+++ b/.rsc.json
@@ -46,6 +46,7 @@
   "catalogVersion": "3.0.7",
   "tier": null,
   "optOuts": [
+    "knowledge-sync",
     "trunk-open"
   ],
   "gitPermissions": true,
```

### F. Untracked files

```text
02-DOCS/process/2026-10-06-git-autocommit-investigation.md
02-DOCS/process/2026-10-06-knowledge-sync-disable.md
02-DOCS/process/2026-10-06-sdd-foundation-branch-reconstruction.md
02-DOCS/process/2026-10-06-sdd-foundation-ratification.md
02-DOCS/wiki/index.md
02-DOCS/wiki/sdd/config.yaml
02-DOCS/wiki/sdd/constitution.md
02-DOCS/wiki/sdd/decisions.md
CLAUDE.md
```

The branch-reconstruction report was created after the initial untracked listing.

### G. Authoritative root files

These files have no diff:

```text
project-overview.md
project-requirements.md
extraction-contract.md
gold-set-contract.md
evaluation-contract.md
ux-requirements.md
```

The verification command returned:

```text
root documents: no diff
```

### H. Final knowledge-sync status

```json
{
  "active": false,
  "reason": "opted-out",
  "branch": "chore/sdd-foundation",
  "defaultBranch": "main",
  "exchangeBranch": "rsc/knowledge",
  "queued": 0,
  "pendingNotices": 0,
  "lastFetch": "2026-10-07T01:04:32.522Z",
  "paths": [
    "01-TOOLS/",
    "02-DOCS/wiki/",
    "02-DOCS/attachments/"
  ],
  "neverSynced": [
    "02-DOCS/wiki/harness/user-profile.md"
  ]
}
```

### I. Remote exchange branch

Before reconstruction:

```text
origin/rsc/knowledge
  -> 11afb35da8cab0ff5e0c84fb65aeba85e9e5f14a
```

After reconstruction:

```text
origin/rsc/knowledge
  -> 11afb35da8cab0ff5e0c84fb65aeba85e9e5f14a
```

Latest remote-tracking reflog entry remains:

```text
11afb35 refs/remotes/origin/rsc/knowledge@{2026-10-06T18:50:53-06:00}: update by push
```

No push or modification to `origin/rsc/knowledge` occurred.

## Commit and push verification

The active branch reflog records the authorized pointer move:

```text
c476d82 chore/sdd-foundation@{2026-10-06T20:33:27-06:00}: reset: moving to c476d82787976b015a66fbb2a1454084d8e478de
```

There is no later `commit:` entry. The active branch log ends at `c476d82`.

There is no new remote exchange-branch reflog entry. The active branch has no
upstream. No commit or push occurred during reconstruction.

## Warnings and ambiguities

1. `git diff` reports only `.rsc.json` because all restored SDD files are
   untracked at the base commit. Review must include the explicit untracked list.
2. The ignored `.rsc/.no-knowledge-sync` sentinel remained present; the supported
   status command confirms `opted-out`.
3. npm printed its existing warning about unknown env config `devdir`; it did not
   affect verification.
4. The automatic commits remain reachable by the local backup branch and by
   reflog. The corresponding exchange commits remain on `origin/rsc/knowledge`.
5. The report itself is untracked and was not committed.

## Result

The requested state is established:

- automatic history is preserved locally;
- active branch is directly based on `c476d82`;
- approved final SDD artifacts match `dfaf562` exactly;
- the SDD artifacts are untracked and uncommitted;
- `.rsc.json` opt-out remains an unstaged tracked modification;
- prior process reports and `CLAUDE.md` remain untracked;
- root requirements are unchanged;
- knowledge sync remains disabled;
- no commit or remote push occurred.

SDD remains stopped. `specify` was not started.
