# Delong's workflow

## PR workflow

I build with my `df-*` skills and Graphite (`gt`). The cycle:

1. `/df-new <task>` starts fresh work in a new worktree off `staging`. Use `/df-stack-extend <task>` instead to stack new work on top of an existing stack.
2. Build with plain commits. Don't push and don't open PRs.
3. `/df-stack-submit`: I run this myself when the work is ready. It submits draft PRs through Graphite, splitting into a stack when that helps review, and then stops.
4. Bot reviews land on the drafts within a few minutes.
5. `/df-stack-triage` shows every review comment in a triage table. I decide each row, then fixes and replies follow, via the repo's `review-pr-comments` skill.
6. `/df-stack-sync` runs when part of the stack merges before the rest, or the stack falls behind `staging`. It drops the merged branches and restacks the rest with Graphite, locally only.
7. `/df-stack-close` runs once the whole stack has merged. It cleans up the local branches and the worktree.

## Stacks and worktrees

- Every branch is tracked by Graphite from the moment it's created. Change stack branches only with `gt` (`gt modify`, `gt restack`, `gt sync`, `gt move`), never by hand with `git rebase`, `git reset` or `git commit --amend`.
- Each stack lives in one worktree. Graphite skips any branch checked out in another worktree, so never leave a stack branch checked out in the main checkout.
- Push fixes with `gt submit --stack --update-only`, which only pushes branches that already have a PR.

## Pushing

- **New work:** never push or open PRs on your own. `/df-stack-submit` is the only way new work gets published, and I call it myself.
- **Fixes to an existing PR** (review comments, CI fixes, any change to a published branch): commit locally, then **stop**. Don't run `gt submit`, `git push` or anything else that updates the remote until I've checked the change myself or told you to push.
- Replies that point to a fix wait until that fix is pushed. Its commit SHA only exists on GitHub after the push.
