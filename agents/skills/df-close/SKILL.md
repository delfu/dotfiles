---
name: df-close
description: Use when Delong invokes /df-close — verifies every PR in the current Graphite stack has merged, then deletes the stack's local branches and removes the worktree.
user-invocable: true
argument-hint: [branch]
---

# Close a finished stack (Delong)

Final step after `/df-new` or `/df-next` → `/df-create-pr` → review → merge. Confirm the whole stack is merged, then clean up locally. Nothing here touches GitHub: the repo squash-merges and auto-deletes merged branches, so the remote is already clean.

**Deleting branches and worktrees is destructive.** Do every check first, show the plan, and wait for an explicit yes.

## Workflow

### 1. Find the stack

```bash
MAIN_ROOT=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
WT=$(git rev-parse --show-toplevel)
```

Pick the top branch:
- If `[branch]` was given, use it.
- If the current branch is checked out, use that branch.
- If HEAD is detached (normal after `/df-create-pr`), use `git branch --format='%(refname:short)' --points-at HEAD`.
- If nothing is found, ask.

Walk down to the trunk. Repeat `gt info --branch <b> --no-interactive`, reading its `Parent:` line, until the parent is `staging`. The branches visited form `STACK`, bottom to top.

Also collect the branches stacked **on** this one:
- Graphite-tracked children: run `gt log short --stack --no-interactive` from a stack branch.
- Untracked `/df-next` branches: run `git config --get-regexp 'branch\..*\.delong-parent'` and keep the ones whose value is in `STACK`.

Those belong to other work. Report them and never delete them.

### 2. Verify everything merged

For each branch in `STACK`:

```bash
gh pr view "$b" --json number,state,headRefOid,url,title
```

- All `MERGED` → continue.
- Any `OPEN` (draft or not) → stop. List each one's state and URL.
- Any `CLOSED` without merging → stop and ask. It may be abandoned on purpose, or a mistake.
- No PR found → stop and ask.

### 3. Check nothing would be lost

Stop and report on any of these:

- **Unsaved work in the worktree.** Check `git -C "$WT" status --porcelain`. Gitignored files don't count: `.worktreesetup` mirrors them in from the main checkout.
- **Local commits that never reached the PR.** For each branch, check whether `git rev-parse "$b"` equals `headRefOid`. If it doesn't, list the extra commits with `git log --oneline <headRefOid>.."$b"`.
- **A stack branch checked out in another worktree.** Check `git worktree list --porcelain`. Skip that branch and name the worktree.
- **Children found in step 1.** Deleting their merged parent is safe. Graphite moves tracked children onto `staging`, and `/df-create-pr` re-parents untracked `/df-next` branches when it runs. But mention them.

### 4. Confirm

Show the plan and **wait for a yes**:

- The merged PRs: number, title, URL.
- The branches to delete. Include any `backup/<branch>` refs that `/df-create-pr` left from splits.
- The worktree to remove, and how it will be removed (see step 6).
- Anything skipped, and why.

### 5. Delete the branches

Free the branches first: `git -C "$WT" switch --detach`. Then work top to bottom:

```bash
gt delete "$b" --force --no-interactive   # local only; also clears Graphite metadata and the branch's git config
git branch -D "backup/$b" 2>/dev/null || true
```

`--force` is required. Squash merges never make the branch an ancestor of `staging`, so Graphite and `git branch -d` treat it as unmerged. Step 2 already proved it merged. **Never pass `--close`**: it acts on GitHub.

### 6. Remove the worktree

**Never remove the main checkout** (`$WT` = `$MAIN_ROOT`), and never remove a worktree other than `$WT`.

- **The session is in a worktree the desktop app created** (the session started there): archive this session as the last action, using `archive_session` with `session_id: "self"` and reason `stack merged`. The app removes its worktree, and the conversation ends. So give the final summary *before* the call.
- **The session moved into the worktree via EnterWorktree** (from `/df-new` or `/df-next`): call **ExitWorktree** with `action: "keep"`, then run `git -C "$MAIN_ROOT" worktree remove "$WT"`.
- If `worktree remove` refuses, say why. Use `--force` only after Delong agrees.

Finish with `git -C "$MAIN_ROOT" worktree prune`.

## Common Pitfalls

- Don't `git checkout staging` or run `gt sync` from a worktree. The main checkout owns `staging`, and `gt sync` would act on every stack in the repo, not just this one.
- GitHub retargets child PRs to `staging` after a merge. Walk the stack with Graphite's `Parent:`, not the PRs' `baseRefName`.
- Don't run `git stash` to "clean" the tree before checking. Unsaved work is a reason to stop, not something to tidy away.
