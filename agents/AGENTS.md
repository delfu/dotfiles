# Delong's workflow

## General workflow

- Do not launch long processes (eg: dev servers, servers, ...) unless explicitly told to or for you to test quickly and then tear down. I want to avoid having long processes outside of my terminals

## PR workflow

- Start brand new work on a new worktree. I want to avoid conflict with other agents
- Keep commits as isolated ideas. Commits should be easily reviewable and never glob a bunch of fixes together (unless they are purely trivial changes). I want my history to be browseable.
- A PR (standalone or within a stack of PRs) can contain multiple commits if need to. I want to avoid having too many PRs while keeping PRs easy to review. Commits should be readable on their own, if need be. 
- Once ready, submit the entire stack of commits as a Graphite PR. I want my reviewers to review as quickly as possible.
- Do not create new worktrees, keep the entire stack within the same worktree. Worktrees are reserved for purely brand new or parallel work. I want to avoid exploding worktree and branch maintenance. 
- Do not ever push new code or update PR without explicit confirmation from me. I need to test everything before it goes out
- Use `gt` commands if they are available, prefer them over plain `git` commands. I want to avoid graphite issues
- Always submit new PRs as draft
- experimental: before pushing up PRs, run the /quiz-me skill to make sure i understand it

## Communication

- Keep your communication to me as short and as concise as possible. I get innundated with agent messages so I need to avoid spam. 
- Avoid using lingo that are specific to the codebase. You can use general software engineering terms. 
	- examples: do not use terms like "arming", "sentry" (not the SaaS product but as a concept), 
- Prefer bullet point messages, keeping each bullet at most two sentences.
- Avoid telling me what you did, only communicate what you need me to do and an executive summary of your actions since last time I messaged you. 
- I might occasionally ask you questions on what you did or explain something. In those times, ignore the brevity and explain in details ELI5
- If there's anything that I need to try/test/make decision on, flag it explicitly, in a visually distinct block (ie: not hidden as a bullet point). If it's a decision, use the questions UI
