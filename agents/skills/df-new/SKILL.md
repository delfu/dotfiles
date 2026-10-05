---
name: df-new
description: Use when Delong invokes /df-new to start a fresh piece of work — opens a new worktree off latest staging, plans, and builds with agents as plain commits until /df-create-pr.
user-invocable: true
argument-hint: <what to build>
---

# New work session (Delong)

Start one focused idea in its own worktree, cut from the latest `origin/staging`. Build it with plain commits on one branch. Graphite is not involved until `/df-create-pr`.

Related: `/df-next` stacks new work on an existing stack; `/df-create-pr` publishes.

## When NOT to Use

- To build on top of an existing stack → `/df-next`.
- To fix review comments on an open PR → work in that PR's worktree (`review-pr-comments`).

## Workflow

### 1. Get into a fresh worktree

```bash
MAIN_ROOT=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
CUR_ROOT=$(git rev-parse --show-toplevel)
git -C "$MAIN_ROOT" fetch origin staging
```

Pick a short kebab-case `<slug>` from the task (ask only if `$ARGUMENTS` is empty). Then:

- **Already in a linked worktree that is untouched**: this is the desktop app's per-session worktree. The test is `CUR_ROOT != MAIN_ROOT`, `git status --porcelain` is empty, and `git log origin/staging..HEAD` is empty. Reuse it. Run `git reset --keep origin/staging` so it starts on latest staging. Rename the branch with `git branch -m delong/<slug>`.
- **Otherwise** (main checkout, or a worktree that already has work), create a new worktree. Never stack unrelated work on top of an existing branch.

  ```bash
  WT="$MAIN_ROOT/.claude/worktrees/<slug>"
  git -C "$MAIN_ROOT" worktree add "$WT" -b "delong/<slug>" origin/staging
  ```

  Then call **EnterWorktree** with `path: "$WT"` so the session moves into it.

Record where the branch came from. `/df-create-pr` reads this:

```bash
git config "branch.delong/<slug>.delong-parent" staging
```

Run `./.worktreesetup` in the background from the worktree root. The SessionStart hook does not fire for a worktree created mid-session. If the task is clearly one project, scope the setup, for example `WORKTREESETUP_PROJECTS=desktop`.

### 2. Plan

Follow the repo's AGENTS.md rule. For anything non-trivial (new feature, multi-file change, bug with unknowns), run the `ce-plan` skill first. Skip planning for one-liners and mechanical changes. Use the repo's preferred skills and agents for the area (see the Skill Priority table), for example `ui-dev` for desktop UI and `backend-py-dev` for aria-web.

### 3. Build

- Dispatch subagents for independent pieces of the plan. Run them in parallel when they touch different files. Give each one the worktree path as its working directory. Don't use `isolation: "worktree"`: their changes must land in this worktree.
- Commit as you go with plain `git commit` on `delong/<slug>`. Stage by explicit path. Never use `git add -A` or `-a`, and never stage `flow-server/vendor/vime`.
- Keep commits shaped around ideas: one refactor, one feature step, and so on. `/df-create-pr` splits the stack along commit lines, so clean commits now mean an easy split later.
- Don't run `gt create` or `gt submit`, and don't push. Publishing is `/df-create-pr`'s job.
- Run the touched project's typecheck, lint and tests before saying a step is done.

### 4. Hand back

Report what was built, the commits, what was verified, and what wasn't. End with the next step: `/df-create-pr` when ready for review.

## Common Pitfalls

- `git checkout staging` / `gt checkout staging` fail inside a worktree, because the main checkout owns `staging`. Always base on `origin/staging`.
- Don't run `git stash` (it's shared across worktrees). Use a WIP commit instead.
- One idea per session. If the work grows a second, unrelated idea, say so. Suggest finishing this one and starting the other with `/df-new` or `/df-next`.
