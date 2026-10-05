---
name: df-comments
description: Use when Delong invokes /df-comments after opening a PR or Graphite stack — summarizes every review comment (human, bot or LLM) in one triage table with severity and a recommendation, waits for his decisions, then hands off to review-pr-comments to reply and fix.
user-invocable: true
argument-hint: [PR number | PR URL | branch]
---

# Triage review comments (Delong)

A thin layer over the repo's `review-pr-comments` skill. Read `.claude/skills/review-pr-comments/SKILL.md` first and follow it for everything: fetching all three comment surfaces, checking claims against the code, drafting replies, the `Claude: ` prefix, reply style, and asking before posting.

This skill changes only three things: **which PRs** to cover, **the table**, and **a hard stop for Delong's decisions** before anything is fixed or drafted.

## 1. Find the PRs

Pick the target in this order:

1. The argument: a PR number, PR URL or branch name.
2. The current branch. If HEAD is detached (normal after `/df-create-pr`), use `git branch --format='%(refname:short)' --points-at HEAD`.
3. Otherwise, list open PRs with `gh pr list --author @me --state open --json number,title,headRefName,url`.

If the target is in a Graphite stack, cover the **whole stack**. Walk it with `gt info --branch <b> --no-interactive`, reading `Parent:` until you reach `staging`. Then add children from `gt log short --stack --no-interactive`.

**If it's ambiguous, ask before reading anything.** For example: no argument and nothing checked out, several open stacks, or an argument that matches more than one PR. Use AskUserQuestion with each candidate's PR number and title as options.

## 2. Show this table instead of review-pr-comments' triage table

Fetch and verify each PR exactly as `review-pr-comments` says. Then show one table for the whole stack, ordered by PR (bottom of the stack first), then by severity:

```markdown
| # | PR | Comment | From | Issue | Severity | Recommend |
|---|----|---------|------|-------|----------|-----------|
| 1 | #4512 | [inline](https://github.com/.../pull/4512#discussion_r123) | coderabbit 🤖 | Token refresh can race on logout | P0 | **Fix**: confirmed, `refreshToken` has no lock |
| 2 | #4512 | [review](https://github.com/.../pull/4512#pullrequestreview-456) | @alice | Why not reuse `useDebounce`? | other | **Reply**: it can't cancel; explain |
| 3 | #4513 | [comment](https://github.com/.../pull/4513#issuecomment-789) | claude 🤖 | Rename `tmp` to `pending` | nit | **Fix**: trivial |
| 4 | #4513 | [inline](...) | codex 🤖 | Missing null check on `user` | P1 | **Skip**: false positive; the caller guards it |
```

- **Comment:** a direct link to that exact comment.
- **From:** the author's login. Mark bots and LLM tools with 🤖.
- **Issue:** a very short, plain-words summary. Aim for under about 12 words.
- **Severity:**
  - `P0`: a real bug, data loss, a security problem, or a crash. It blocks merge.
  - `P1`: a correctness or robustness problem worth fixing in this PR.
  - `nit`: style, naming, wording, or a small cleanup.
  - `other`: a question, a design discussion, or an FYI.
- **Recommend:** **Fix**, **Skip** or **Reply**, with a few words on why.
- **Rows:** a bot review with several findings gets one row per finding.
- **Under the table:**
  - how many comments were skipped (resolved, noise)
  - any review still running

**Then stop.** Don't plan fixes or draft replies yet. Delong decides each row and may answer in shorthand ("fix 1, 3; skip 4"). Any row he doesn't mention follows your recommendation. Confirm that in one line.

## 3. Hand off

Continue with `review-pr-comments`, using Delong's decisions as the verdicts:

- Re-fetch first. Add any new comments as new rows and ask about them.
- Make each fix on the branch whose PR the comment is on, not on the top of the stack: in the worktree holding the branch, `gt checkout <branch>`, make the change, then `gt modify`. If Graphite reports a branch "needs restack" because it is checked out in another worktree, run `gt restack` in that worktree.
- If a fix changes what the PR description says, fetch the live body (`gh pr view <n> --json body -q .body`), change only the affected lines, and keep everything else (screenshots, videos, Delong's edits) as is. Never regenerate the description. Show the change and wait for Delong's yes before `gh pr edit`.
- **Commit fixes locally, then stop. Don't push.** List the fix commits for each PR and wait until Delong has checked them or tells you to push. Then push with `gt submit --stack --no-edit --no-interactive`.
- Fixed replies name the commit SHA, so they wait until that fix is pushed. Skipped and Reply-only replies can go earlier.
- Post only after Delong's yes, as `review-pr-comments` requires.
