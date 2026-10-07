# Process report — SDD foundation final pre-commit review

This report records the final review candidate. It is not an authoritative
requirements document and does not authorize a commit, push, PR, merge, or later
SDD phase.

## Date, branch, and scope

- Date: 2026-10-06 (UTC-6)
- Branch: `chore/sdd-foundation`
- HEAD: `c476d82787976b015a66fbb2a1454084d8e478de`
- Task: final pre-commit review only
- SDD phases run: none
- Commit or remote mutation: none

## Consistency correction

One comment in `02-DOCS/wiki/sdd/config.yaml` changed:

```diff
-# strict_tdd stays false until a real runner is added by amendment.
+# strict_tdd stays false until a real runner is configured.
```

No config value changed. The correction keeps test tooling as runtime/project
configuration rather than a constitutional amendment.

## Intended versioned foundation set

The candidate set is exactly:

```text
.rsc.json
CLAUDE.md
02-DOCS/wiki/index.md
02-DOCS/wiki/sdd/config.yaml
02-DOCS/wiki/sdd/constitution.md
02-DOCS/wiki/sdd/decisions.md
02-DOCS/process/2026-10-06-git-autocommit-investigation.md
02-DOCS/process/2026-10-06-knowledge-sync-disable.md
02-DOCS/process/2026-10-06-sdd-foundation-branch-reconstruction.md
02-DOCS/process/2026-10-06-sdd-foundation-precommit-review.md
02-DOCS/process/2026-10-06-sdd-foundation-ratification.md
```

The process report itself is included as a candidate because the human requested
all existing `02-DOCS/process/*.md` reports in the foundation set. It remains
untracked and uncommitted.

## Explicitly excluded local/generated files

These are ignored/local state and are not commit candidates:

```text
.rsc/.no-knowledge-sync
.rsc/knowledge-sync.json
.rsc/backups/
.cursor/rules/.rsc-state.json
```

`git check-ignore -v` confirms all four exclusions.

## Git status

```text
## chore/sdd-foundation
 M .rsc.json
?? 02-DOCS/process/
?? 02-DOCS/wiki/index.md
?? 02-DOCS/wiki/sdd/
?? CLAUDE.md
```

## Git diff stat

```text
 .rsc.json | 1 +
 1 file changed, 1 insertion(+)
```

Untracked files are not included in ordinary `git diff --stat`.

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

The config comment correction is inside an untracked file, so ordinary
`git diff` does not show it.

## Untracked candidates

```text
02-DOCS/process/2026-10-06-git-autocommit-investigation.md
02-DOCS/process/2026-10-06-knowledge-sync-disable.md
02-DOCS/process/2026-10-06-sdd-foundation-branch-reconstruction.md
02-DOCS/process/2026-10-06-sdd-foundation-precommit-review.md
02-DOCS/process/2026-10-06-sdd-foundation-ratification.md
02-DOCS/wiki/index.md
02-DOCS/wiki/sdd/config.yaml
02-DOCS/wiki/sdd/constitution.md
02-DOCS/wiki/sdd/decisions.md
CLAUDE.md
```

## Process-report index

The final line counts and first headings were verified after this file was
written. They are also shown in the accompanying Cursor review output.

## Authoritative requirements

These six root files have no diff:

```text
project-overview.md
project-requirements.md
extraction-contract.md
gold-set-contract.md
evaluation-contract.md
ux-requirements.md
```

## Knowledge-sync state

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

## Git reference verification

```text
chore/sdd-foundation
  -> c476d82787976b015a66fbb2a1454084d8e478de

chore/sdd-foundation-auto-backup
  -> dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea

origin/rsc/knowledge
  -> 11afb35da8cab0ff5e0c84fb65aeba85e9e5f14a
```

The active branch has no commit after the authorized reset to `c476d82`.
The remote knowledge ref is unchanged.

## Remaining unresolved scientific and evaluation decisions

The pre-commit review does not resolve:

- canonical banned-field list;
- treatment of `Sin_dato_en_RegulonDB`;
- treatment of `Técnica_confirmada_manualmente`;
- treatment of `Año_confirmado`;
- concrete `.gitignore` strategy for future gold files.

These remain recorded in `02-DOCS/wiki/sdd/decisions.md`.

## Result

The foundation candidate is ready for human review, not for automatic commit.

- The requested config comment is corrected.
- The intended versioned set is explicit.
- Generated local state is excluded.
- Root requirements are unchanged.
- Knowledge sync remains disabled.
- No new commit or push exists.
- SDD remains stopped.
