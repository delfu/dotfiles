---
name: df-stack-extend
description: Use when Delong invokes /df-stack-extend to start new work stacked on top of an existing Graphite stack — opens a new worktree with a Graphite-tracked branch on the stack's top branch, so review fixes can continue in the stack's own worktree.
user-invocable: true
argument-hint: <what to build> [--on <branch>]
---

# Next work session on a stack (Delong)

Start the next idea in a **new worktree**, on a branch Graphite tracks as a child of the stack's top branch. The stack's own worktree stays untouched, so another agent can keep fixing review comments there in parallel.

Graphite never rewrites a branch checked out in another worktree. While this session works, restacks in the stack's worktree skip this branch. `/df-stack-submit` runs `/df-stack-sync` here first, which restacks it onto whatever the stack below has become. Unfinished work isn't published by accident either: review fixes are pushed with `gt submit --stack --update-only`, which skips branches without a PR.

## Workflow

### 1. Find the parent branch

- If `--on <branch>` was given, use it.
- Otherwise, if the current branch is tracked by Graphite, use the top of its stack. Run `gt log short --no-interactive` and take the topmost descendant of the current branch. If the current branch has several children, ask which one.
- Otherwise, list Delong's open stacks (`gh pr list --author @me --state open --json headRefName,baseRefName,title`) and ask.

Check that the parent is safe to build on:

```bash
git fetch origin "$PARENT"
git rev-parse "$PARENT" "origin/$PARENT"
```

If local and remote differ, someone has unpushed or unpulled changes. Show both SHAs and ask. Don't move the local ref: it may be checked out in another worktree.

### 2. Create the worktree

```bash
MAIN_ROOT=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
WT="$MAIN_ROOT/.claude/worktrees/<slug>"
git -C "$MAIN_ROOT" worktree add "$WT" -b "delong/<slug>" "$PARENT"
```

Call **EnterWorktree** with `path: "$WT"`, then track the branch on its parent:

```bash
gt track --parent "$PARENT" --no-interactive
```

Run `./.worktreesetup` in the background.

### 3. Plan and build

Same as `/df-new` steps 2–4: plan with `ce-plan` when the work is non-trivial, then build with agents. Use plain commits on `delong/<slug>`, stage by explicit path, and don't push. Finish by pointing at `/df-stack-submit`, which will extend the stack.

## Common Pitfalls

- Never edit the parent stack's branches from this worktree. Review fixes for lower PRs belong in the stack's own worktree.
- If a lower PR changes or merges while you work, that's fine. `/df-stack-submit` syncs this branch onto the new stack first.
- Two `/df-stack-extend` sessions on the same parent create sibling branches, not a chain. Graphite allows that, but ask Delong if it looks unintended.
