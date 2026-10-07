# Git autocommit investigation — SDD foundation

This is a process report for human and external review. It is not an authoritative
requirements document and does not authorize corrective action.

## Date, branch, and task

- Date: 2026-10-06 (UTC-6)
- Branch: `chore/sdd-foundation`
- HEAD: `dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea`
- Task: read-only investigation of three unexpected local commits
- SDD progression: stopped
- Corrective action: none

The only project file created by this investigation is this report. It is not committed.

## Executive conclusion

The three local commits were created by **rsc-harness knowledge sync**, invoked by
Cursor's `afterAgentResponse` lifecycle hook.

This conclusion is established, not inferred:

1. `.cursor/hooks.json` runs:

   ```json
   {
     "command": "node \".rsc/knowledge-sync.mjs\" hook cursor turn"
   }
   ```

   under `afterAgentResponse`.

2. `.rsc/knowledge-sync.mjs` says that the `turn` event calls `onTurn(root)`.
   `onTurn` calls `commitLocal(root, s)`.

3. On a non-default branch, `commitLocal` runs:

   ```js
   git(root, [
     '--literal-pathspecs',
     'commit',
     '--quiet',
     '--no-verify',
     '--only',
     '-m',
     message(staged),
     '--',
     ...staged
   ]);
   ```

4. The message generator in that function is:

   ```js
   const message = (names) =>
     `📝 docs(auto): ${summary(names)} ${SKIP_CI}`;
   ```

   and `SKIP_CI` is `[skip ci]`.

5. The resulting messages exactly match the three unexpected commits.

6. The script's sync scope is:

   ```js
   ['01-TOOLS/', '02-DOCS/wiki/', '02-DOCS/attachments/']
   ```

   The three commits contain only changed files under `02-DOCS/wiki/`.

7. `.rsc/knowledge-sync.json` records local HEAD as `dfaf562`, an empty queue, and
   three synced exchange commits.

8. `refs/remotes/origin/rsc/knowledge` contains three corresponding commits with
   identical timestamps, subjects, file stats, and tree objects.

The trigger is a Cursor lifecycle event, but the committing implementation is
rsc-harness. It was not a Git hook, a Cursor Source Control action, or an explicit
agent shell command.

## Current Git state

Command:

```sh
git status --short --branch
```

Output before this report was created:

```text
## chore/sdd-foundation
?? 02-DOCS/process/
?? CLAUDE.md
```

The untracked process directory then contained:

```text
02-DOCS/process/2026-10-06-sdd-foundation-ratification.md
```

After this report was created, it also contains:

```text
02-DOCS/process/2026-10-06-git-autocommit-investigation.md
```

No tracked working-tree changes were present before this report. No upstream is
configured for `chore/sdd-foundation`.

## Branch history

Command:

```sh
git log --oneline --decorate --graph -10
```

Output:

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

## Timeline of the three local commits

| Local commit | Parent | Timestamp | Files | Subject |
|---|---|---|---|---|
| `ed75d343e81f4899d8615f85c9edeec9541323de` | `c476d82787976b015a66fbb2a1454084d8e478de` | `2026-10-06T18:38:57-06:00` | `config.yaml`, `constitution.md`, `decisions.md`, `index.md` | `📝 docs(auto): config, constitution, decisions y 1 más [skip ci]` |
| `183f6120120a0d9efc2ba22cbd010f9ff09e21d3` | `ed75d343e81f4899d8615f85c9edeec9541323de` | `2026-10-06T18:47:38-06:00` | `constitution.md`, `decisions.md` | `📝 docs(auto): constitution, decisions [skip ci]` |
| `dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea` | `183f6120120a0d9efc2ba22cbd010f9ff09e21d3` | `2026-10-06T18:50:49-06:00` | `constitution.md`, `decisions.md`, `index.md` | `📝 docs(auto): constitution, decisions, index [skip ci]` |

All three have:

- Author: `HeladiaSalgado <heladia@ccg.unam.mx>`
- Committer: `HeladiaSalgado <heladia@ccg.unam.mx>`
- matching author and committer timestamps

This identity comes from the global Git configuration:

```text
global file:/Users/heladia/.gitconfig user.name=HeladiaSalgado
global file:/Users/heladia/.gitconfig user.email=heladia@ccg.unam.mx
```

It identifies which Git identity the automation used. It does not show a human
explicitly authorized or typed the commit command.

## `git show --format=fuller --stat`

### `ed75d34`

```text
commit ed75d343e81f4899d8615f85c9edeec9541323de
Author:     HeladiaSalgado <heladia@ccg.unam.mx>
AuthorDate: Tue Oct 6 18:38:57 2026 -0600
Commit:     HeladiaSalgado <heladia@ccg.unam.mx>
CommitDate: Tue Oct 6 18:38:57 2026 -0600

    📝 docs(auto): config, constitution, decisions y 1 más [skip ci]

 02-DOCS/wiki/index.md            |  9 ++++
 02-DOCS/wiki/sdd/config.yaml     | 67 ++++++++++++++++++++++++++++++
 02-DOCS/wiki/sdd/constitution.md | 88 ++++++++++++++++++++++++++++++++++++++++
 02-DOCS/wiki/sdd/decisions.md    | 23 +++++++++++
 4 files changed, 187 insertions(+)
```

### `183f612`

```text
commit 183f6120120a0d9efc2ba22cbd010f9ff09e21d3
Author:     HeladiaSalgado <heladia@ccg.unam.mx>
AuthorDate: Tue Oct 6 18:47:38 2026 -0600
Commit:     HeladiaSalgado <heladia@ccg.unam.mx>
CommitDate: Tue Oct 6 18:47:38 2026 -0600

    📝 docs(auto): constitution, decisions [skip ci]

 02-DOCS/wiki/sdd/constitution.md | 35 ++++++++++-------------------------
 02-DOCS/wiki/sdd/decisions.md    | 20 ++++++++++++++++++++
 2 files changed, 30 insertions(+), 25 deletions(-)
```

### `dfaf562`

```text
commit dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea
Author:     HeladiaSalgado <heladia@ccg.unam.mx>
AuthorDate: Tue Oct 6 18:50:49 2026 -0600
Commit:     HeladiaSalgado <heladia@ccg.unam.mx>
CommitDate: Tue Oct 6 18:50:49 2026 -0600

    📝 docs(auto): constitution, decisions, index [skip ci]

 02-DOCS/wiki/index.md            |  2 +-
 02-DOCS/wiki/sdd/constitution.md | 11 ++++++-----
 02-DOCS/wiki/sdd/decisions.md    | 15 +++++++++++++++
 3 files changed, 22 insertions(+), 6 deletions(-)
```

## Reflog evidence

Command:

```sh
git reflog --date=iso-strict -20
```

Relevant output:

```text
dfaf562 HEAD@{2026-10-06T18:50:49-06:00}: commit: 📝 docs(auto): constitution, decisions, index [skip ci]
183f612 HEAD@{2026-10-06T18:47:38-06:00}: commit: 📝 docs(auto): constitution, decisions [skip ci]
ed75d34 HEAD@{2026-10-06T18:38:57-06:00}: commit: 📝 docs(auto): config, constitution, decisions y 1 más [skip ci]
c476d82 HEAD@{2026-10-06T18:34:31-06:00}: checkout: moving from main to chore/sdd-foundation
c476d82 HEAD@{2026-10-06T18:11:07-06:00}: pull --ff-only: Fast-forward
```

The commits were ordinary commits advancing local branch HEAD. They were not
merge, rebase, cherry-pick, or reset events.

## Remote exchange-branch evidence

The rsc script says it sends knowledge commits to a dedicated exchange branch:
`rsc/knowledge`.

Command:

```sh
git log --oneline --format='%h %aI %s' -10 refs/remotes/origin/rsc/knowledge
```

Output:

```text
11afb35 2026-10-06T18:50:49-06:00 📝 docs(auto): constitution, decisions, index [skip ci]
308ce6e 2026-10-06T18:47:38-06:00 📝 docs(auto): constitution, decisions [skip ci]
f2b0c95 2026-10-06T18:38:57-06:00 📝 docs(auto): config, constitution, decisions y 1 más [skip ci]
c476d82 2026-10-06T18:11:04-06:00 Merge pull request #1 from Helysalgado/chore/rsc-harness-setup
```

Remote-tracking reflog:

```text
11afb35 refs/remotes/origin/rsc/knowledge@{2026-10-06T18:50:53-06:00}: update by push
308ce6e refs/remotes/origin/rsc/knowledge@{2026-10-06T18:47:41-06:00}: update by push
f2b0c95 refs/remotes/origin/rsc/knowledge@{2026-10-06T18:39:02-06:00}: update by push
```

The local and exchange commits have different hashes because they have different
parent chains. Their tree hashes are identical pair by pair:

```text
ed75d34^{tree} = f2b0c95^{tree} = 907fe3c63c6eb7a359836a57b85bad532b26413c
183f612^{tree} = 308ce6e^{tree} = e8fddf3b8ffb82b2df52582aedfec0c600a4195a
dfaf562^{tree} = 11afb35^{tree} = b41945dcd0b5211f709f898ef5dd022b073e2b12
```

This proves that each local automatic commit was replayed to the exchange branch.
It also means a network push occurred through the detached rsc worker, even though
the agent did not issue a `git push` shell command and the feature branch itself has
no upstream.

## rsc state evidence

Read-only command:

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
  "lastFetch": "2026-10-07T00:59:35.017Z",
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

`.rsc/knowledge-sync.json` contains:

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
  "lastFetch": 1791334775017,
  "snap": null,
  "head": "dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea"
}
```

The empty queue and `ours` list show that all three knowledge changes were shipped.

## Responsible configuration and code

### Cursor lifecycle hook

Relevant `.cursor/hooks.json` section:

```json
{
  "afterAgentResponse": [
    {
      "command": "node \".rsc/session-memory-adapter.mjs\" cursor turn"
    },
    {
      "command": "node \".rsc/knowledge-sync.mjs\" hook cursor turn"
    }
  ],
  "beforeSubmitPrompt": [
    {
      "command": "node \".rsc/session-memory-adapter.mjs\" cursor request"
    },
    {
      "command": "node \".rsc/knowledge-sync.mjs\" hook cursor request"
    }
  ]
}
```

The commits appeared after turns that changed files under `02-DOCS/wiki/`.

### rsc knowledge-sync implementation

Relevant statements from `.rsc/knowledge-sync.mjs`:

```js
export const KNOWLEDGE =
  Object.freeze(['01-TOOLS/', '02-DOCS/wiki/', '02-DOCS/attachments/']);
export const OPT_OUT = '.no-knowledge-sync';
export const SKIP_CI = '[skip ci]';
```

```js
function changedKnowledge(root) {
  // Uses git status restricted to KNOWLEDGE paths.
}
```

```js
export function commitLocal(root, s) {
  const branch = line(root, ['rev-parse', '--abbrev-ref', 'HEAD']);
  const files = changedKnowledge(root).slice(0, MAX_FILES);
  const message = (names) =>
    `📝 docs(auto): ${summary(names)} ${SKIP_CI}`;

  // On a non-default branch:
  git(root, ['--literal-pathspecs', 'add', '-A', '--', ...files]);
  git(root, [
    '--literal-pathspecs',
    'commit',
    '--quiet',
    '--no-verify',
    '--only',
    '-m',
    message(staged),
    '--',
    ...staged
  ]);
}
```

```js
export function onTurn(root, { spawnShip = true } = {}) {
  // ...
  commitLocal(root, s);
  // ...
  if (pending && spawnShip) background(root, 'ship');
}
```

```js
export function hook(target, event, native = {}) {
  // ...
  if (event === 'turn' && !native?.stop_hook_active) onTurn(root);
}
```

The file header explicitly documents the behavior:

```text
What you change goes up when your turn ends.
It only ever touches KNOWLEDGE paths.
Every commit it makes says [skip ci].
```

It also states that local file commits happen inside the hook while network push
runs detached.

### Installed harness state

`.cursor/rules/.rsc-state.json` records:

```json
{
  "knowledge": {
    "mode": "wired",
    "reason": null,
    "paths": [
      ".rsc/knowledge-sync.mjs",
      ".rsc/trunk-policy.mjs",
      ".cursor/hooks.json"
    ]
  }
}
```

Paths are shortened here for readability; the source file contains absolute paths.

`.rsc.json` has no knowledge-sync opt-out. Its current opt-outs are:

```json
"optOuts": [
  "trunk-open"
]
```

### Search results

A repository and harness search for:

- `docs(auto)`
- `git commit`
- `auto commit`
- `autocommit`
- `checkpoint`
- `skip ci`

found the operative `docs(auto)` and commit implementation in
`.rsc/knowledge-sync.mjs`. The ordinary workspace search did not initially show
that ignored `.rsc/` code, so `.rsc/` was searched directly.

`.cursor/commands/checkpoint.md` is unrelated. It runs `rsc sello freeze` and
`sello approve`; it does not define these documentation commits.

## Git configuration and Git hooks

Relevant configuration:

```text
core.hooksPath is unset, so Git uses .git/hooks
user.name=HeladiaSalgado
user.email=heladia@ccg.unam.mx
```

No Git alias, commit command wrapper, or commit-related configuration was present.

The only active non-sample hook is executable `.git/hooks/post-merge`. It runs:

```sh
node "$root/.rsc/worktree-reaper.mjs" "$root" auto
```

It is a worktree cleanup hook. It only runs after a merge. The reflog contains no
merge at the three commit timestamps.

It also cannot be the source because `.rsc/knowledge-sync.mjs` commits with
`--no-verify`, and the exact message is generated inside that script.

No active `pre-commit`, `commit-msg`, `post-commit`, or `prepare-commit-msg` hook
was found. Files with those names are only Git's `.sample` files.

## Attribution matrix

| Candidate | Finding | Evidence |
|---|---|---|
| rsc-harness | **Established source** | `knowledge-sync.mjs` contains the exact commit command and exact subject template; state contains the matching SHAs |
| Cursor action | **Lifecycle trigger only** | `.cursor/hooks.json` invokes the rsc script after each agent response |
| Git hook | **Ruled out** | Only active hook is `post-merge`; no merge events; rsc uses `--no-verify` |
| Explicit agent shell command | **No evidence; inconsistent with tool history** | No agent `git commit` command was executed; the exact behavior is automatic hook code |
| Other local automation | **No evidence needed to explain commits** | rsc mechanism completely accounts for paths, messages, timestamps, local refs, and remote exchange refs |

## Can automatic commits be disabled?

Yes. Two documented mechanisms exist.

Read-only help command:

```sh
npx @ericrisco/rsc@3.0.7 knowledge-sync --help
```

Output:

```text
Use: npx @ericrisco/rsc knowledge-sync on|off|status
```

The script's announcement documents:

```text
For this project: rsc knowledge-sync off.
```

The implementation also checks for:

```text
.rsc/.no-knowledge-sync
```

and returns inactive reason `opted-out` when that file exists.

The script describes this as a project switch that travels in `.rsc.json`.
The exact file changes made by the CLI `off` command were not executed or assumed.

To obtain the requested workflow—agent edits, human reviews the diff, explicit
human authorization before commit—the knowledge-sync feature must be disabled
before more edits under `01-TOOLS/`, `02-DOCS/wiki/`, or
`02-DOCS/attachments/`.

No disable action was taken in this investigation.

## Non-destructive remediation options

### Option 1 — Keep the three local commits; disable future knowledge sync

Later, with explicit authorization:

1. Run the documented knowledge-sync off command.
2. Confirm `knowledge-sync status` reports inactive.
3. Continue using the current branch and require explicit human approval for
   future commits.

Advantages:

- No history rewrite.
- No loss of the ratified artifacts.
- Lowest mechanical risk.

Risks:

- The three commits remain even though the human requested review before commit.
- Their automatic granularity and subjects may not match desired branch history.
- Copies remain on `rsc/knowledge`.

### Option 2 — Build a new review branch without rewriting this branch

Later, with explicit authorization:

1. Disable knowledge sync first.
2. Preserve `chore/sdd-foundation` unchanged as evidence.
3. Create a new branch from `c476d82`.
4. Restore the desired SDD artifact contents from `dfaf562` into the new branch's
   working tree without committing them.
5. Review the unstaged diff.
6. Commit only after explicit human authorization.

Advantages:

- Non-destructive to existing refs.
- Produces the intended human-review-before-commit workflow.
- Keeps the automatic commits available for audit.

Risks:

- Requires careful handling of current untracked files before changing branches.
- Produces a second branch.
- The `rsc/knowledge` exchange branch still contains the automatic versions.
- If sync is not disabled first, it may commit or reapply knowledge files again.

This is the recommended way to reconstruct human-controlled branch history
without rewriting evidence.

### Option 3 — Keep history and add a later explanatory commit

Later, after disabling sync and obtaining approval, add only an explanatory
decision or process note.

Advantages:

- No rewrite.
- Easy to audit.

Risks:

- Does not satisfy a strict requirement that the original commits should never
  have existed.
- Adds more history without changing the automatic commits.

### Option 4 — Rewrite the current branch later

A possible later sequence would preserve a backup ref, disable sync, move the
branch back to `c476d82`, and leave the SDD artifacts uncommitted for review.

Advantages:

- Restores the current branch to a human-controlled commit sequence.

Risks:

- Rewrites branch history.
- Commands such as reset/rebase are destructive if used incorrectly.
- Untracked files can be lost or obscured without preparation.
- The remote exchange branch remains separate and may reintroduce files if sync
  is active.
- Requires explicit human approval and a verified backup.

No rewrite command was run. This option is not recommended before Option 2 is
considered.

### Option 5 — Revert the automatic commits

Reverting would add inverse commits and remove the SDD artifacts from the current
tree. Reapplying them later would add more commits.

Advantages:

- No branch rewrite.

Risks:

- Noisy history.
- Temporarily removes approved foundation artifacts.
- Does not produce a clean review-before-first-commit history.

Not recommended.

## Remote exchange branch consideration

The detached rsc worker already pushed the three knowledge snapshots to
`origin/rsc/knowledge`.

Turning sync off prevents future automatic behavior, but does not erase that
remote branch. Deleting or rewriting the remote exchange branch would be a
separate remote mutation. It was not performed and should require explicit human
authorization.

The feature branch itself has no upstream, and no evidence shows it was pushed.

## Failed read-only command during investigation

One read-only shell loop intended to compare tree hashes failed because zsh did
not split the quoted pair as expected:

```text
fatal: ambiguous argument 'ed75d34 f2b0c95^{tree}'
```

It changed nothing. The comparison was rerun with six explicit revisions and
succeeded. The successful hashes are recorded above.

## Current untracked files

Before this report:

```text
02-DOCS/process/2026-10-06-sdd-foundation-ratification.md
CLAUDE.md
```

After this report:

```text
02-DOCS/process/2026-10-06-git-autocommit-investigation.md
02-DOCS/process/2026-10-06-sdd-foundation-ratification.md
CLAUDE.md
```

No untracked file was staged or committed.

## Recommendation

1. Do not continue SDD yet.
2. Do not rewrite the three commits yet.
3. With explicit human approval, disable project knowledge sync using the
   documented rsc command.
4. Confirm it reports inactive before any further `02-DOCS/wiki/` edit.
5. Prefer Option 2 if human-controlled branch history is required: preserve the
   current branch as evidence and reconstruct the approved artifacts as an
   uncommitted diff on a new branch from `c476d82`.
6. Decide separately whether the `rsc/knowledge` remote exchange branch should
   remain or be removed.
7. Resume SDD only after that Git-policy decision.

## Commands executed by this investigation

Read-only commands:

```text
git status --short --branch
git log --oneline --decorate --graph -10
git reflog --date=iso-strict -20
git show --format=fuller --stat ed75d34
git show --format=fuller --stat 183f612
git show --format=fuller --stat dfaf562
git config --show-origin --show-scope --list
git hook list
git for-each-ref ...
git reflog show refs/remotes/origin/rsc/knowledge
git show ... f2b0c95 308ce6e 11afb35
git rev-parse <six tree revisions>
git status --porcelain=v1 --untracked-files=all
npx @ericrisco/rsc@3.0.7 knowledge-sync status
npx @ericrisco/rsc@3.0.7 knowledge-sync --help
```

`git hook list` is unsupported by the installed Git and returned usage text. The
hook directory was therefore inspected directly and relevant files were read.

Files and searches inspected:

```text
.cursor/hooks.json
.cursor/commands/checkpoint.md
.cursor/rules/.rsc-state.json
.git/hooks/post-merge
.rsc/knowledge-sync.mjs
.rsc/knowledge-sync.json
.rsc/auto-update.mjs
.rsc.json
repository and .rsc/.cursor searches for docs(auto), git commit,
auto commit, autocommit, checkpoint, and skip ci
```

No corrective command was executed.
