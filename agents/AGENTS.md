# Delong's workflow

## General workflow

- Do not launch long processes (eg: dev servers, servers, ...) unless explicitly told to or for you to test quickly and then tear down. I want to avoid having long processes outside of my terminals
- Do not use /quiz-me before opening PRs. Open the PRs and then quiz me. I prefer to get context by reading the PR
- Every PR needs a Linear task. If you dont know which project it should be referring to (and you weren't able to infer) ask. If there's no appropriate task for it, create it. Link the task to the PR description
- Do not create a PR before getting my confirmation. I need to test what's being put out
- For all multiple choice decisions you're asking, always end on "Do you have more instructions?". This is to avoid me finishing the questions and you immediately start doing things bfore i had a chance to add extra details/commands

## Commit messages

- Keep the commit message body short
- Describe what was changed and why. Do not describe how.
- Example of what not to do:
```
    feat(desktop): the sparkle popover shows the same Skills menu, searchable

    The sparkle popover drops its Prebuilt / Your Skills tabs for the menu the
    `/` list uses: My Skills, then Suggested, then Browse all Skills and Create
    Skill. Focus lands in its search field, which filters the same ranked list;
    the arrow keys move the highlight and Enter picks, without leaving the field.

    The search field can now act as a combobox for the list it filters, so a
    screen reader follows the highlight. The tab labels are gone from every
    locale.
```
- Example of what to do instead:
```
    feat(desktop): Consolidate chat sparkle menu and the slash command Skills menu

	Re-use the same menu for `/` and the sparkle button. And better accessibility
```
- Commit messages should be quickly scanning through git history to find the right commit. Not or getting a full picture of what the commit is doing. 
	

## PR workflow

- Limit your PRs to 300 total lines changed. If it's longer than that then it's not a good, reviewable PR
- After pushing up the PR, use the /ponytail-review skill to review it and address the feedback and push up the update
- When creating branches, always use the `delong/` prefix
- Start brand new work on a new worktree. I want to avoid conflict with other agents
- Name the worktree something that's related to the feature we are working on
- Every PR, standalone or within a stack, must be focused and reviewable as a whole.
- In addition, every commit within a PR must be independently reviewable: one coherent idea with a clear purpose and diff. Do not bundle unrelated fixes into a commit unless they are purely trivial changes. Reviewers should be able to review the PR commit by commit, and the history should remain easy to browse.
- A PR can contain multiple related commits. Group them into one focused PR when that keeps review manageable; independently reviewable commits do not each need their own PR.
- Once ready, submit the entire stack of commits as a Graphite PR. I want my reviewers to review as quickly as possible.
- Do not create new worktrees, keep the entire stack within the same worktree. Worktrees are reserved for purely brand new or parallel work. I want to avoid exploding worktree and branch maintenance. 
- Use `gt` commands if they are available, prefer them over plain `git` commands. I want to avoid graphite issues
- Always submit new PRs as draft
- In a stack, PR branches should share the same base name with their order as a suffix (eg: "delong/somefeature-1")
- Do not create a stack unless the individual PRs relate to each other

## Communication

- Keep your communication to me as short and as concise as possible. I get innundated with agent messages so I need to avoid spam. 
- Avoid using lingo that are specific to the codebase. You can use general software engineering terms. 
	- examples: do not use terms like "arming", "sentry" (not the SaaS product but as a concept), 
- Prefer bullet point messages, keeping each bullet at most two sentences.
- Avoid telling me what you did, only communicate what you need me to do and an executive summary of your actions since last time I messaged you. 
- I might occasionally ask you questions on what you did or explain something. In those times, ignore the brevity and explain in details ELI5
- If there's anything that I need to try/test/make decision on, flag it explicitly, in a visually distinct block (ie: not hidden as a bullet point). If it's a decision, use the questions UI

## Code Styleguide
### React
- name variables with descriptive verbs like `isSomeState` or `shouldOpenSomeModal` or `hasSomeProperty` instead of just `someState` or `openSomeModal` (when it's not a callback) or `someProperty`. Having a verb there conveys more clearly what it's describing.
- callbacks should always be named `on`Something. Callbacks are reactive on an event so should be prefixed with `on`
