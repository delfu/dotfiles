---
name: df-stack-submit
description: Use when Delong invokes /df-stack-submit or asks to create a pull request — submits the session's work as draft Graphite PRs (new stack, or extending the stack from /df-stack-extend), splitting ideas into separate PRs when reviewable alone. Titles and descriptions follow the repo's create-pr skill when there is one. Only creates PRs; never updates an existing PR or pushes fixes.
user-invocable: true
argument-hint: [--base <branch>]
---

# Submit a stack (Delong)

Publish this session's work as draft PRs with Graphite (`gt`). This skill owns branches, stacking and publishing. Titles and descriptions come from the repo's own `create-pr` skill when the repo has one (step 3). `gh` is used only to read PR state and to set title, body and labels on PRs `gt` already created.

## When NOT to Use

- When addressing PR comments (use `/df-stack-triage`)
- When updating an existing PR's code, title, description or labels, or pushing a branch that already has a PR. This skill only creates PRs. It never edits a PR that existed before this run.

## Workflow

### 1. Gather context

Resolve `PR_REPO_ROOT=$(git rev-parse --show-toplevel)` and `ORIG_BRANCH=$(git branch --show-current)`. Resolve every repository-relative path from this root, even when invoked inside a project.

Graphite knows the branch's parent: `gt info --branch "$ORIG_BRANCH" --no-interactive`, line `Parent:`. `/df-new` tracks it on `staging`, and `/df-stack-extend` on the stack's top branch.

- If the branch isn't tracked, run `gt track --parent "${BASE:-staging}" --no-interactive`, where `BASE` is the `--base` argument.
- If `--base` names a different parent than Graphite has, move the branch: `gt move --onto "$BASE" --no-interactive`.

#### 1a. Commit and sync

"Submit my current work" includes uncommitted changes. If `git status --porcelain` shows any, commit them first, staging by explicit path. Show Delong the file list.

Then follow `/df-stack-sync` steps 1–3 from this branch. It updates `staging`, drops merged parents and restacks this branch onto the stack's current tip. Stop on anything it stops on. Afterwards, `PR_BASE` is the branch's Graphite parent again (`staging` if every PR below has merged).

Note which existing PR branches below now differ from their remote. Step 4's submit pushes them too, so they go in the approval in step 3.

After the sync, run these reads in parallel:

```bash
git -C "$PR_REPO_ROOT" log --oneline "${PR_BASE}..HEAD"
git -C "$PR_REPO_ROOT" diff "${PR_BASE}...HEAD" --stat
git -C "$PR_REPO_ROOT" diff "${PR_BASE}...HEAD"
```

Look for a Linear task ID (e.g. `WP-10231`) to link in the description. Use the one the user gives you first. If there isn't one, check the branch name (Linear branches look like `delong/wp-10231-short-title`) and then the commit messages. Normalize it to uppercase. If you find none, skip the link rather than guessing.

### 2. Decide: single PR or Graphite stack

Delong stacks PRs with **Graphite** (`gt`), not `gh stack`. Read the diff and ask: does it hold more than one idea that a reviewer could approve on its own?

Split when it makes review easier, for example:
- A refactor or rename that the feature then builds on.
- A backend/API change and the client that uses it.
- A schema or migration change and the code that reads it.
- Unrelated fixes that ended up on the same branch.

Keep one PR when the diff is small (roughly under 300 changed lines of real code), when the parts can't build or pass tests alone, or when splitting would scatter one idea across PRs. Keep tests with the code they test.

Use the commit history as the first guess at the seams: `/df-new` and `/df-stack-extend` commit one idea at a time. In extend mode, judge only this session's commits. The PRs below are already their own reviews.

If a split makes sense, propose it before touching any branch. List each PR in order (bottom first) with a draft title, the files/hunks it takes, and why it stands alone. Wait for Delong to approve or adjust. Rewriting branches is hard to undo, so never split without approval.

To build an approved stack, start from a clean tree, keep a backup ref, and move all changes into the working tree on top of the base. Step 1a already restacked the branch onto `PR_BASE`, so the soft reset carries exactly this session's changes.

```bash
git -C "$PR_REPO_ROOT" branch "backup/${ORIG_BRANCH}" HEAD
git -C "$PR_REPO_ROOT" reset --soft "$PR_BASE"
git -C "$PR_REPO_ROOT" restore --staged .
```

For the **first** (bottom) PR, branch off here and tell Graphite its parent. The uncommitted changes come along.

```bash
git -C "$PR_REPO_ROOT" switch -c delong/<short-name>
gt track --parent "$PR_BASE" --no-interactive
git -C "$PR_REPO_ROOT" add -- <paths for this PR>
git -C "$PR_REPO_ROOT" commit -m "<conventional commit message>"
```

For **each later** PR, stage only its paths and create the branch on top of the previous one:

```bash
git -C "$PR_REPO_ROOT" add -- <paths for this PR>
gt create delong/<short-name> -m "<conventional commit message>" --no-interactive
```

**No split (single PR):** the PR still goes through Graphite, never `gh pr create`. If the branch name isn't descriptive (for example a desktop-app worktree name), rename it with `gt rename delong/<short-name>` and use the new name as `ORIG_BRANCH` from here on. Never use `git branch -m` on a tracked branch: Graphite would lose it.

- When one file's hunks belong to different PRs, stage part of it with `git apply --cached <partial.patch>`. `gt split --by-hunk` and `git add -p` are interactive and won't work here.
- Stage by explicit path only. Never use `-a`/`-A`, and never stage `flow-server/vendor/vime` unless the task is a vime bump.
- After the last branch, `git status` must be clean and `git diff "backup/${ORIG_BRANCH}" HEAD` must be empty. If not, stop and report.
- Run the touched project's checks (at least typecheck/lint) on each branch so every PR is green on its own.
- `ORIG_BRANCH` now points at the base. Ask before deleting it with `gt delete`, and don't delete it if it already has an open PR.

### 3. Write titles and descriptions

**If `$PR_REPO_ROOT/.claude/skills/create-pr/SKILL.md` exists**, read it and follow it for each PR's title, description, review label and sponsor, including the policy, template, learnings and media notes it points to, and its cut pass. Step 1 already covered its context gathering. Skip everything it says about publishing (`git push`, `gh pr create`, the argument arrays) and its follow-through after publishing: step 4 here publishes with Graphite, and step 5 stops.

**Otherwise**, use this short fallback:

- **Title:** `{type}({scope}): {description}`. Type is `feat`, `fix`, `chore`, `refactor`, `test` or `docs`. Scope is `desktop`, `backend`, `ios`, `android`, `admin`, `dash` or `monorepo` (`scope1/scope2` for several). Lowercase, imperative ("add", not "adds"). State the intent, not the mechanism: a fix names the symptom, a feat names the capability. `fix(backend): users logged out unexpectedly when token refresh races`, not `fix(backend): add null check in token refresh handler`.
- **Body:** fill `$PR_REPO_ROOT/.github/pull_request_template.md` if there is one, otherwise use Why / What Changed / Review Guidance / Testing. A reviewer should be able to read it in about 30 seconds. If you're writing a paragraph, cut it to a sentence.
  - **Why:** 1–3 plain sentences on the problem. End with the Linear link when known: `[WP-10231](https://linear.app/wispr/issue/WP-10231)`.
  - **What Changed:** a few bullets on behavior and any important choice. No file-by-file changelog and no code-level detail.
  - **Review Guidance:** one line for the review mode, one for risk and focus.
  - **Testing:** a task list. `- [x] <check> — <result>` for what ran and passed, `- [ ] <check> — <why not>` for the rest. No timestamps.
  - Keep the template's Readiness boxes, unchecked. Remove optional sections that don't apply.
  - **Visual changes:** end with a `# Screenshots / Video` section of visible `_TODO: screenshot of <state>_` placeholders, one per changed screen or state. Delong records and fills them in, so list the shots he needs in your reply.

Either way, in a stack name only the PR below this one ("bottom of stack" for the first), and fill in its number after the submit in step 4. Don't name the PR above: in extend mode that would mean editing an existing PR, and Graphite's stack comment already links the whole stack.

Show every PR's title and body together, plus any existing PR branches that the submit will also push (from step 1a), and wait for Delong's yes. Then write each body to its own `mktemp` file with a file-edit tool. Never put PR text in a heredoc or in shell source.

### 4. Publish with Graphite

Every PR goes through Graphite, including a single one. Never use `gh pr create`: Graphite wouldn't know the branch, and the stack would show up split.

1. From the top new branch, push it and everything below it as drafts, with no prompts and no AI text:

   ```bash
   gt submit --no-stack --draft --no-edit --no-ai --no-interactive
   ```

   `--no-stack` leaves out branches above this one.
2. Apply each new PR's agreed title, body and labels. Only for PRs this run created; never run `gh pr edit` on a PR that existed before:

   ```bash
   gh pr edit "$BRANCH" --title "$PR_TITLE" --body-file "$PR_BODY_FILE" \
     ${REVIEW_MODE_LABEL:+--add-label "$REVIEW_MODE_LABEL"} \
     ${SPONSOR_GH_LOGIN:+--add-assignee "$SPONSOR_GH_LOGIN"}
   ```

   Leave a value unset when it doesn't apply; never pass an empty handle. Remove each body file once its edit succeeds.
3. In extend mode, run `git switch --detach`. That frees the new branch, so restacks from the stack's own worktree can include it. In a `/df-new` worktree, stay on the branch: this worktree is the stack's home.

On failure, check whether GitHub already created the PR before retrying, keep the body file, and never create a duplicate. Return every PR URL, bottom first.

**After everything merges:** run `/df-stack-close` to verify the merges and clean up the branches and worktree.

### 5. Stop after publishing

This skill ends once the PRs exist. Return the URLs, then stop. Don't wait for reviews, fetch comments, or address findings here. Bot reviews land on the drafts over the next few minutes, and Delong runs `/df-stack-triage` once they're in. Publishing doesn't attest to human readiness, so leave the Readiness boxes unchecked.
