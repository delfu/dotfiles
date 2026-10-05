---
name: df-next
description: Use when Delong invokes /df-next to start new work stacked on top of an existing Graphite stack — opens a new worktree off the stack's top branch, kept untracked until /df-create-pr.
user-invocable: true
argument-hint: <what to build> [--on <branch>]
---

# Next work session on a stack (Delong)

Start the next idea in a **new worktree** based on the top branch of an existing Graphite stack. The original stack's worktree stays untouched, so another agent can keep fixing review comments there in parallel.

## The concurrency rule (why this skill looks the way it does)

The new branch is a plain git branch. It is **not tracked by Graphite** until `/df-create-pr`. That's on purpose:

- If it were tracked as a child of the stack, `gt submit --stack` from the other worktree would push this unfinished work as a PR.
- While it's untracked, `gt modify` / `gt restack` in the stack's worktree never see it. Their rewrites can't touch it.
- The cost: the stack below may be rewritten while you work. `/df-create-pr` handles that by rebasing onto the parent's new tip, using the recorded base SHA (`git rebase --onto`).

## Workflow

### 1. Find the parent branch

- If `--on <branch>` was given, use it.
- Otherwise, if the current branch is tracked by Graphite, use the top of its stack. Run `gt log short --no-interactive` and take the topmost descendant of the current branch. If the current branch has several children, ask which one.
- Otherwise, list Delong's open stacks (`gh pr list --author @me --state open --json headRefName,baseRefName,title`) and ask.

Check that the parent is clean to build on:

```bash
git fetch origin "$PARENT"
git rev-parse "$PARENT" "origin/$PARENT"
```

If local and remote differ, someone has unpushed or unpulled changes. Show both SHAs and ask which one to build on. Don't move the local ref: it may be checked out in another worktree.

### 2. Create the worktree

```bash
MAIN_ROOT=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
PARENT_SHA=$(git rev-parse "$PARENT")
WT="$MAIN_ROOT/.claude/worktrees/<slug>"
git -C "$MAIN_ROOT" worktree add "$WT" -b "delong/<slug>" "$PARENT_SHA"
git config "branch.delong/<slug>.delong-parent" "$PARENT"
git config "branch.delong/<slug>.delong-parent-sha" "$PARENT_SHA"
```

Call **EnterWorktree** with `path: "$WT"`. Run `./.worktreesetup` in the background.

**Do not** run `gt track` or `gt create` here.

### 3. Plan and build

Same as `/df-new` steps 2–4: plan with `ce-plan` when the work is non-trivial, then build with agents. Use plain commits on `delong/<slug>`, stage by explicit path, and don't push. Finish by pointing at `/df-create-pr`, which will extend the stack.

## Common Pitfalls

- Never edit the parent stack's branches from this worktree. Review fixes for lower PRs belong in their own worktree.
- If a lower PR merges while you work, that's fine. `/df-create-pr` re-parents onto `staging` once the parent has merged.
- Two `/df-next` sessions on the same parent create sibling branches, not a chain. Graphite allows that, but ask Delong if it looks unintended.
