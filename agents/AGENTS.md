# Delong's workflow

## PR workflow

I build with my `df-*` skills and Graphite (`gt`). The cycle:

1. `/df-new <task>` starts fresh work in a new worktree off `staging`. Use `/df-next <task>` instead to stack new work on top of an existing stack.
2. Build with plain commits. Don't push and don't open PRs.
3. `/df-create-pr`: I run this myself when the work is ready. It submits draft PRs through Graphite, splitting into a stack when that helps review, and then stops.
4. Bot reviews land on the drafts within a few minutes.
5. `/df-comments` shows every review comment in a triage table. I decide each row, then fixes and replies follow, via the repo's `review-pr-comments` skill.
6. `/df-close` runs once the whole stack has merged. It cleans up the local branches and the worktree.

## Pushing

- **New work:** never push or open PRs on your own. `/df-create-pr` is the only way new work gets published, and I call it myself.
- **Fixes to an existing PR** (review comments, CI fixes, any change to a published branch): commit locally, then **stop**. Don't run `gt submit`, `git push` or anything else that updates the remote until I've checked the change myself or told you to push.
- Replies that point to a fix wait until that fix is pushed. Its commit SHA only exists on GitHub after the push.
