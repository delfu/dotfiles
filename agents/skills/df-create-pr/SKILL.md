---
name: df-create-pr
description: Use when Delong invokes /df-create-pr or asks to create a pull request — submits the session's work as draft Graphite PRs (new stack, or extending the stack from /df-next), splitting ideas into separate PRs when reviewable alone, with short plain-language descriptions. Only creates PRs; never updates an existing PR or pushes fixes.
user-invocable: true
argument-hint: [--base <branch>]
---

# Create PR (Delong)

Publish PRs with Graphite (`gt`), applying the shared PR policy and template. `gt` owns branches, stacking and PR creation. `gh` is used only to read PR state and to set title, body and labels on PRs `gt` already created. Calling skills supply domain-specific evidence, routing, and flags; they do not maintain their own body templates.

## When to Use

- When asked to create a PR or open a pull request
- When work on a branch is ready for automated review, before human handoff

## When NOT to Use

- When the user just wants a diff review (use `deep-review`)
- When addressing PR comments (use `/df-comments`)
- When updating an existing PR's code, title, description or labels, or pushing a branch that already has a PR. This skill only creates PRs. It never edits a PR that existed before this run.

## Learnings

Before starting, grep `.claude/learnings/pr-review.md` for PR/media/CLI gotchas and the affected project's learnings for relevant constraints. Record only reusable traps that survive the change.

## Workflow

### 1. Gather context

Resolve `PR_REPO_ROOT=$(git rev-parse --show-toplevel)`. Read `$PR_REPO_ROOT/docs/pr-review.md` for policy and `$PR_REPO_ROOT/.github/pull_request_template.md` for structure. Resolve every repository-relative path from this root, even when invoked inside a project.

Resolve `PR_BASE` first, in this order:

1. The explicit `--base`.
2. The branch's recorded parent: `git config "branch.$(git branch --show-current).delong-parent"`. `/df-new` sets it to `staging`. `/df-next` sets it to the stack's top branch and also records `delong-parent-sha`.
3. Otherwise `staging`.

If `PR_BASE` is a stack branch, check whether its PR has merged **before** fetching: `gh pr view "$PR_BASE" --json state -q .state`. The repo squash-merges and auto-deletes merged branches, so the fetch would fail, and `/df-close` may have deleted the local branch too. If the state is `MERGED`, set `PR_BASE=staging` and remember to use the merged-parent path in step 1a.

Refresh that remote branch before gathering the diff. Stop if the fetch fails rather than use a stale local base:

```bash
git -C "$PR_REPO_ROOT" fetch origin "+refs/heads/${PR_BASE}:refs/remotes/origin/${PR_BASE}"
```

Every session runs in a worktree, and the main checkout owns `staging`. Never `git checkout`/`gt checkout` the trunk, and never `git fetch origin X:X` into a local branch. Both fail when another worktree has that branch checked out.

#### 1a. Commit and sync onto the base

"Submit my current work" includes uncommitted changes. If `git status --porcelain` shows any, commit them first, staging by explicit path. Show Delong the file list.

Then put the branch on the base's current tip. Stop on any rebase conflict and report. Never resolve conflicts in the lower PRs' code silently.

- **Base is `staging`**: run `git rebase origin/staging`.
- **Base is a stack branch** (extend mode, from `/df-next`). The stack below may have been rewritten since this work started, for example by another agent fixing review comments.
  1. If the parent's PR merged (detected in step 1), run `git rebase --onto origin/staging "$PARENT_SHA"`. The squash-merge left the parent's commits in staging under new SHAs, so this drops the originals. Update the recorded `delong-parent` to `staging`.
  2. Otherwise, require `git rev-parse "$PR_BASE"` = `git rev-parse "origin/$PR_BASE"`. If they differ, another session has unpushed or unpulled work on the stack. **Stop and ask.** Submitting now would push or clobber it.
  3. Run `git rebase --onto "$PR_BASE" "$PARENT_SHA"`. Here `PARENT_SHA` is the recorded `delong-parent-sha`. This moves only this session's commits onto the parent's new tip.

After a successful fetch and sync, run these reads in parallel:

```bash
git -C "$PR_REPO_ROOT" log --oneline "origin/${PR_BASE}..HEAD"
git -C "$PR_REPO_ROOT" diff "origin/${PR_BASE}...HEAD" --stat
git -C "$PR_REPO_ROOT" diff "origin/${PR_BASE}...HEAD"
```

Look for a Linear task ID (e.g. `WP-10231`). Use the one the user gives you first. If there isn't one, check the branch name (Linear branches look like `delong/wp-10231-short-title`) and then the commit messages. Normalize it to uppercase. If you find none, skip the link rather than guessing.

### 2. Decide: single PR or Graphite stack

Delong stacks PRs with **Graphite** (`gt`), not `gh stack`. Read the diff and ask: does it hold more than one idea that a reviewer could approve on its own?

Split when it makes review easier, for example:
- A refactor or rename that the feature then builds on.
- A backend/API change and the client that uses it.
- A schema or migration change and the code that reads it.
- Unrelated fixes that ended up on the same branch.

Keep one PR when the diff is small (roughly under 300 changed lines of real code), when the parts can't build or pass tests alone, or when splitting would scatter one idea across PRs. Keep tests with the code they test.

Use the commit history as the first guess at the seams: `/df-new` and `/df-next` commit one idea at a time. In extend mode, judge only this session's commits. The PRs below are already their own reviews.

If a split makes sense, propose it before touching any branch. List each PR in order (bottom first) with its title, the files/hunks it takes, and why it stands alone. Wait for Delong to approve or adjust. Rewriting branches is hard to undo, so never split without approval.

To build an approved stack, start from a clean tree, keep a backup ref, and move all changes into the working tree on top of the base. Step 1a already rebased the branch onto `BASE_REF`, so the soft reset carries exactly this session's changes.

```bash
ORIG_BRANCH=$(git -C "$PR_REPO_ROOT" branch --show-current)
BASE_REF=$([ "$PR_BASE" = staging ] && echo origin/staging || echo "$PR_BASE")
git -C "$PR_REPO_ROOT" branch "backup/${ORIG_BRANCH}" HEAD
git -C "$PR_REPO_ROOT" reset --soft "$BASE_REF"
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

**No split (single PR):** the PR still goes through Graphite, never `gh pr create`. Run `gt track --parent "$PR_BASE" --no-interactive` on the current branch. If the branch name isn't descriptive (for example a desktop-app worktree name), first rename it with `git branch -m delong/<short-name>`.

- When one file's hunks belong to different PRs, stage part of it with `git apply --cached <partial.patch>`. `gt split --by-hunk` and `git add -p` are interactive and won't work here.
- Stage by explicit path only. Never use `-a`/`-A`, and never stage `flow-server/vendor/vime` unless the task is a vime bump.
- After the last branch, `git status` must be clean and `git diff "backup/${ORIG_BRANCH}" HEAD` must be empty. If not, stop and report.
- Run the touched project's checks (at least typecheck/lint) on each branch so every PR is green on its own.
- `ORIG_BRANCH` now points at the base. Ask before deleting it, and don't delete it if it already has an open PR.

### 3. Determine the PR title

Follow this naming convention:
```
{type}({scope}): {description}
```

| Part | Values |
|------|--------|
| **type** | `feat`, `fix`, `chore`, `refactor`, `test`, `docs` |
| **scope** | `desktop`, `backend`, `ios`, `android`, `admin`, `dash`, `monorepo` — use `scope1/scope2` if multiple |
| **description** | Short, specific, lowercase, imperative mood ("add", not "adds" or "added") |

**The title states the intent, not the implementation.** A reader scanning the PR list should learn what outcome this PR delivers, without knowing the codebase internals. The test: would someone who hasn't read the diff understand what changed for users (or for the system)? The implementation details — the mechanism, the code-level cause — belong in the PR description body, not the title.

- For `fix`: name the **symptom** being fixed, not the code-level cause or mechanism.
- For `feat`: name the **capability** the user gains, not the components added.
- For `refactor`/`chore`: naming the mechanical change is fine — that *is* the intent.

| ❌ Mechanism (don't) | ✅ Intent (do) |
|---|---|
| `fix(ios): don't reserve layout space for hidden onboarding Skip button` | `fix(ios): onboarding progress bars misaligned when Skip button is hidden` |
| `fix(backend): add null check in token refresh handler` | `fix(backend): users logged out unexpectedly when token refresh races` |
| `feat(desktop): add HistorySearchService and search index` | `feat(desktop): add voice command history search` |

Examples:
- `feat(desktop): add voice command history search`
- `fix(backend): resolve transcription timeout on long audio`
- `chore(desktop): upgrade electron to 28.2.0`
- `refactor(android): extract keyboard layout logic`
- `fix(backend/desktop): align auth token refresh flow`

### 4. Prepare publication inputs

Apply the guide to the full diff and fill the canonical template. Incorporate the calling workflow's required evidence, operational metadata/footer, and sponsor/reviewer selection. For private-repo images, read the “Private-repository PR images need an authenticated rendering path” entry in `.claude/learnings/pr-review.md`.

#### Keep it simple and short

Delong wants descriptions a reviewer can read in about 30 seconds, well under the guide's 150–300 word target. Reviewers skim, and every extra sentence hides what matters. So:

- Use plain words and short sentences. Leave out jargon, filler ("This PR…", "In order to…") and anything the diff already shows clearly.
- **Why:** 1–3 sentences on the problem. Think of this as the problem statement/user pain point.
- **What Changed:** a few bullets on behavior and any important choice. Don't write a file-by-file changelog. Do not include code level details (eg: "no longer reference this variable" is not relevant)
- **Review Guidance:** one line each for mode and for risk/focus. Drop the sponsor and agent-review bullets when they don't apply.
- **Testing:** a Markdown checklist in place of the template's "Completed" / "Not tested" bullets. See below.
- Remove the diarization checkbox when the PR doesn't touch `flow_eval/diarization`. Remove the `<details>` appendix when there's no extended evidence.
- Keep the four Readiness checkboxes, unchecked. The repo's review process depends on them.
- **Stacks:** in What Changed, add one line naming the PR below this one (or "bottom of stack"). Don't name the PR above: that would mean editing an existing PR later, and Graphite's stack comment already links the whole stack.

If you find yourself writing a paragraph, cut it to a sentence.

#### Testing checklist

Write each check as a GitHub task-list item so it renders as a checkbox. `- [x]` means it was run and passed; put the result on the same line. `- [ ]` means it wasn't run yet (or failed); say why in a few words. Don't add dates, times or timestamps anywhere in the Testing section.

```markdown
# Testing

- [x] `yarn test src/history` — 42 passed
- [x] Searched history in the dev app — results update as you type
- [ ] Windows — no Windows machine available
- [ ] Very large history (10k+ items) — not tried yet
```

Tick a box only for something that actually ran. Keep the diarization checkbox (when it applies) separate from this list.

#### Screenshots / video (visual changes only)

When a PR changes anything a user can see (UI, layout, styling, copy, animation, overlays, icons), add this as the **last section** of that PR's body, after Readiness and the appendix. Don't try to run the app or capture media. Always write the placeholders; Delong records and fills them in. Tailor the rows to the actual visual changes in the diff, one row per screen or state that changed, and name each one concretely:

```markdown
# Screenshots / Video

| | Now | Notes |
|---|---|---|
| Speaker picker (open) | _TODO: screenshot_ | |
| Speaker picker (hover on row) | _TODO: screenshot_ | |

**Video:** _TODO: screen recording of <the specific interaction>_
```

- Placeholders are visible text, not HTML comments, so the PR visibly reads as unfinished until they're replaced.
- Add the **Video** line only when motion or interaction matters (animations, drag, hover, transitions). 
- For Devin agents: screenshot and fill in automatically the before and after states when there are visual changes.
- In a stack, add the section only to the PRs that contain visual changes.
- In your reply, list which PRs need media and the shots each one needs, so Delong has a capture checklist. `references/pr-media.md` explains how to upload media later (local paths don't work in a PR body).
- Leave the section out for non-visual changes.

#### Linear link

If a Linear task ID is known, end the Why section with a line holding just the link. The link text is the ID and nothing else:

```markdown
[WP-10231](https://linear.app/wispr/issue/WP-10231)
```

Show the proposed title and complete description. If creation is already authorized, proceed; otherwise obtain authorization before publishing. Write the final Markdown to `PR_BODY_FILE=$(mktemp)` using a file-edit tool. For programmatically assembled content, append data already held in variables with `printf '%s\n' "$BODY_TEXT" >> "$PR_BODY_FILE"`. Never embed untrusted text (including pinned comments or disclosure text) in shell source or a heredoc: even a quoted delimiter can occur in the text and terminate the heredoc. Static, trusted scaffolding may use a quoted heredoc.

Set `PR_TITLE` and `REVIEW_MODE_LABEL` for each PR from the agreed title and the guide. Use `SPONSOR_GH_LOGIN` only for a verified sponsor. Leave a value unset when it doesn't apply, and never pass an empty handle. If the review label is unavailable, report that as the guide directs.

### 5. Publish with Graphite

Every PR goes through Graphite, including a single one. Never use `gh pr create`: Graphite wouldn't know the branch, and the stack would show up split.

1. Prepare a title and body file for every new PR. Show them all together for approval.
2. Check the remote heads first. The i18n bot pushes commits to PR branches, and a submit would overwrite them. For every branch from the base up to the top, run `git fetch origin <branch>` and compare it with the local ref. If the remote is ahead, stop and fast-forward that branch in the worktree that owns it.
3. From the top new branch, push it and everything below it as drafts, with no prompts and no AI text:

   ```bash
   gt submit --no-stack --draft --no-edit --no-ai --no-interactive
   ```

   `--no-stack` leaves out branches above this one. In extend mode the lower PRs should already match the remote (checked in step 1a), so Graphite skips or re-pushes them unchanged.
4. Apply each new PR's agreed title, body and labels. Only for PRs this run created; never run `gh pr edit` on a PR that existed before:

   ```bash
   gh pr edit "$BRANCH" --title "$PR_TITLE" --body-file "$PR_BODY_FILE" \
     ${REVIEW_MODE_LABEL:+--add-label "$REVIEW_MODE_LABEL"} \
     ${SPONSOR_GH_LOGIN:+--add-assignee "$SPONSOR_GH_LOGIN"}
   ```

5. Clean up local state:

   ```bash
   git config --unset "branch.${ORIG_BRANCH}.delong-parent-sha" || true
   git switch --detach
   ```

   The work is now tracked by Graphite, so the recorded SHA is no longer needed. Detaching frees the branches, so `gt modify`/`gt restack` from other worktrees can restack them. Graphite skips any branch that is checked out elsewhere. To make review fixes here later, run `gt checkout <branch>` first.

On failure, check whether GitHub already created the PR before retrying, keep the body file, and never create a duplicate. Return every PR URL, bottom first.

**After everything merges:** run `/df-close` to verify the merges and clean up the branches and worktree.

### 6. Stop after publishing

This skill ends once the PRs exist. Return the URLs, then stop. Don't wait for reviews, fetch comments, or address findings here. Bot reviews land on the drafts over the next few minutes, and Delong runs `/df-comments` once they're in. Publishing doesn't attest to human readiness, so leave the Readiness boxes unchecked.
