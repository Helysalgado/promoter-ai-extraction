# Process report — disable rsc knowledge sync

This is a process report for human and external review. It is not an authoritative
requirements document and does not replace project requirements, the constitution,
the SDD decision log, or future SDD artifacts.

## Date, branch, and objective

- Date: 2026-10-06 (UTC-6)
- Branch: `chore/sdd-foundation`
- Objective: disable rsc-harness project knowledge sync so future edits remain
  uncommitted until explicit human authorization
- Branch reconstruction: not performed
- SDD phases: not run
- Commit, push, reset, rebase, revert, cherry-pick, merge, tag, branch deletion,
  and remote deletion: not run

## Before status

Command:

```sh
npx @ericrisco/rsc@3.0.7 knowledge-sync status
```

Output:

```json
{
  "active": true,
  "reason": null,
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

Before the command:

- `.rsc.json` contained only `"trunk-open"` in `optOuts`.
- `.rsc/.no-knowledge-sync` did not exist.
- `.cursor/rules/.rsc-state.json` contained `"explicitAgents": []`.
- `.rsc/knowledge-sync.json` had an empty queue and HEAD `dfaf562`.

## Command executed

The first attempt used the exact documented command:

```sh
npx @ericrisco/rsc@3.0.7 knowledge-sync off
```

It failed inside the sandbox before completion:

```text
rsc error: EPERM: operation not permitted, mkdir
'.../.rsc/backups/20261007-010448-sync-cursor/files/.cursor/rules'
```

The command was retried unchanged outside the sandbox because the failure was a
filesystem permission restriction:

```sh
npx @ericrisco/rsc@3.0.7 knowledge-sync off
```

Successful output:

```text
rsc knowledge-sync off: 01-TOOLS/ and 02-DOCS/ no longer sync on their own in this project. Commit .rsc.json so the team gets the same decision.
```

No commit was made despite the CLI's informational recommendation.

## After status

Command:

```sh
npx @ericrisco/rsc@3.0.7 knowledge-sync status
```

Output:

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

Expected result is satisfied: knowledge sync is inactive with reason
`opted-out`.

## Exact tracked configuration change

The only tracked change produced by the command is one added opt-out in
`.rsc.json`:

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

Current relevant contents:

```json
{
  "catalogVersion": "3.0.7",
  "tier": null,
  "optOuts": [
    "knowledge-sync",
    "trunk-open"
  ],
  "gitPermissions": true
}
```

The excerpt above preserves the relevant key order and values. Unrelated
`.rsc.json` content is unchanged by the tracked diff.

## Tracked versus local/ignored effects

### Tracked

| File | State |
|---|---|
| `.rsc.json` | Modified; one insertion: `"knowledge-sync"` in `optOuts` |

### Local or ignored

| File | Before | After | Finding |
|---|---|---|---|
| `.rsc/.no-knowledge-sync` | Missing | Present, empty | Created; this is the runtime opt-out sentinel |
| `.cursor/hooks.json` | Existing | Existing | Rewritten by sync operation, but content is byte-identical |
| `.cursor/rules/.rsc-state.json` | `"explicitAgents": []` | Five explicit agent ids | Changed by the rsc sync refresh |
| `.rsc/knowledge-sync.json` | Existing state | Same state | Content unchanged |

Ignore sources:

```text
.cursor/hooks.json                 ignored by .git/info/exclude
.cursor/rules/.rsc-state.json      ignored by .gitignore
.rsc/.no-knowledge-sync            ignored by .gitignore via .rsc/
.rsc/knowledge-sync.json           ignored by .gitignore via .rsc/
```

### `.cursor/hooks.json`

The hook file remains wired:

```json
{
  "command": "node \".rsc/knowledge-sync.mjs\" hook cursor turn"
}
```

This is expected. The hook now exits inactive because `.rsc/.no-knowledge-sync`
exists and `.rsc.json` records the opt-out.

The pre-operation backup and current hook file have no content diff. Its current
SHA-256 is:

```text
5a00f1190be75679f3f221cad800e43372ca2a4e78a3c0b77c8bdf4a62552af5
```

### `.cursor/rules/.rsc-state.json`

The relevant local change is:

```diff
-  "explicitAgents": [],
+  "explicitAgents": [
+    "developer",
+    "python-reviewer",
+    "refuter-correctness",
+    "refuter-security",
+    "refuter-tests"
+  ],
```

Its knowledge wiring metadata still says:

```json
{
  "knowledge": {
    "mode": "wired",
    "reason": null
  }
}
```

This generated state describes installed wiring. Runtime status is controlled by
the opt-out and correctly reports inactive.

### `.rsc/.no-knowledge-sync`

The file now exists and is empty:

```text
size=0
SHA-256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

### `.rsc/knowledge-sync.json`

The content is unchanged from before the disable operation:

```json
{
  "announced": true,
  "seenBy": {
    "chore/sdd-foundation": "11afb35da8cab0ff5e0c84fb65aeba85e9e5f14a"
  },
  "queue": [],
  "ours": [
    "f2b0c9575b75230445ee05a8a2680e6e8278bec0",
    "308ce6e93a34a05f64170bfc9796d14367aa734a",
    "11afb35da8cab0ff5e0c84fb65aeba85e9e5f14a"
  ],
  "notices": [],
  "lastFetch": 1791335072522,
  "snap": null,
  "head": "dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea"
}
```

### Backup artifacts

The failed sandbox attempt left this ignored local backup directory:

```text
.rsc/backups/20261007-010448-sync-cursor/
```

It has no manifest.

The successful operation created:

```text
.rsc/backups/20261007-010455-sync-cursor/
```

Its manifest records a harness sync backup. These backup artifacts are ignored
under `.rsc/` and are not in Git diff.

## Git status

Immediately after disabling, before this report was created:

```text
## chore/sdd-foundation
 M .rsc.json
?? 02-DOCS/process/
?? CLAUDE.md
```

After this report is created, the process directory also contains this untracked
file:

```text
02-DOCS/process/2026-10-06-knowledge-sync-disable.md
```

## Git diff stat

```text
 .rsc.json | 1 +
 1 file changed, 1 insertion(+)
```

## Git diff

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

## Commit and remote-push verification

Before disabling:

```text
HEAD = dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea
origin/rsc/knowledge = 11afb35da8cab0ff5e0c84fb65aeba85e9e5f14a
```

After disabling:

```text
HEAD = dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea
origin/rsc/knowledge = 11afb35da8cab0ff5e0c84fb65aeba85e9e5f14a
```

Latest reflog entries remain:

```text
dfaf562 HEAD@{2026-10-06T18:50:49-06:00}: commit: 📝 docs(auto): constitution, decisions, index [skip ci]
11afb35 refs/remotes/origin/rsc/knowledge@{2026-10-06T18:50:53-06:00}: update by push
```

No new commit or remote knowledge-sync push occurred.

The disabled turn hook was invoked manually for verification:

```sh
printf '{}\n' | node .rsc/knowledge-sync.mjs hook cursor turn
```

It returned:

```json
{}
```

HEAD and the remote exchange ref remained unchanged afterward.

## Authoritative files

The six authoritative root requirement documents were not modified:

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`

## Warnings and ambiguities

1. The first command attempt failed because the sandbox blocked an rsc backup
   directory write. The retry succeeded outside the sandbox.
2. The failed attempt left an ignored local backup directory without a manifest.
   It was not deleted.
3. The successful command performs an rsc harness sync, not only a one-line
   manifest edit. It refreshed generated local state and backups.
4. `.cursor/rules/.rsc-state.json` still says knowledge mode is `wired`.
   This is not the runtime status. The supported status command reports
   `active: false`, `reason: opted-out`.
5. `.cursor/hooks.json` still includes the knowledge-sync lifecycle calls.
   They now return without committing because the opt-out sentinel exists.
6. The npm warning about unknown env config `devdir` appeared on each npx call.
   It did not prevent success.
7. Existing local commits and the remote `rsc/knowledge` branch were not changed.

## Result

Knowledge sync is disabled for this project.

The tracked decision remains uncommitted in `.rsc.json`. The local sentinel and
generated-state changes remain local and ignored. This report is untracked.

Branch reconstruction remains pending human review.
