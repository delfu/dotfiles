---
name: df-stack-sync
description: Use when Delong invokes /df-stack-sync, when a PR in the current Graphite stack has merged, or when the stack is behind staging — updates staging, drops the merged branches and restacks the rest with Graphite. Local only; never pushes.
user-invocable: true
argument-hint: [branch]
---

# Sync a stack (Delong)

Bring the current stack up to date with `staging` using Graphite only. Don't rebuild what `gt` does with `git rebase`: hand-made rebases leave Graphite's metadata stale, and its next restack then replays the wrong commits.

This is local only. Pushing is a separate step that Delong approves.

## Worktrees

Graphite (1.8.4+) never rewrites a branch that is checked out in another worktree. It skips it during sync and restack. It does update local `staging` from any worktree. So a stack should live in one worktree, and stack branches never sit in the main checkout.

## Workflow

### 1. Find the stack

Start from `[branch]`, else the current branch, else (detached HEAD) `git branch --format='%(refname:short)' --points-at HEAD`. Walk down with `gt info --branch <b> --no-interactive`, reading `Parent:`, until it reaches `staging`, then add the children from `gt log short --stack --no-interactive`. That's `STACK`, bottom to top.

`gt log` shows the worktree path next to any branch checked out elsewhere. Note those: Graphite will skip them.

For each branch in `STACK`, run `gh pr view "$b" --json number,state,headRefOid,url`. For an open PR, check that the remote has nothing the local branch lacks: `git merge-base --is-ancestor <headRefOid> "$b"`. If that fails, someone pushed to the PR (the i18n bot does this). Stop and ask: restacking now and pushing later would overwrite their commits.

### 2. Drop merged branches

For each branch whose PR is `MERGED`, bottom first:

- If `git rev-parse "$b"` differs from `headRefOid`, the branch has local commits that never reached the PR. Stop and show them (`git log --oneline <headRefOid>.."$b"`).
- If it's checked out in another worktree, stop. Name the worktree and ask Delong to move it off the branch. Don't touch other worktrees yourself.
- Otherwise delete it locally. Graphite moves its children onto its parent.

  ```bash
  gt delete "$b" --force --no-interactive
  ```

  Never pass `--close`: it acts on GitHub.

A PR that is `CLOSED` without merging: stop and ask. Never use `gt sync -d`, which also deletes closed PRs' branches in every stack.

### 3. Sync and restack

```bash
gt sync --no-interactive
gt restack --no-interactive
```

`gt sync` fast-forwards `staging` and restacks what it can without conflicts. `gt restack` finishes the current stack and stops at the first conflict. On a conflict, stop and report the branch and files. Never resolve conflicts in a lower PR's code silently.

If a branch was skipped because it's checked out in another worktree, say so: `gt restack` has to run in that worktree.

### 4. Report and stop

Show `gt log short --stack --no-interactive`, then each open PR's branch with whether its local head now differs from the remote (`git fetch origin <b>` first). Those branches need a push.

Then stop. Push only after Delong's yes:

```bash
gt submit --stack --update-only --no-edit --no-interactive
```

`--update-only` pushes only branches that already have a PR, so unfinished work stacked on top is never published.
