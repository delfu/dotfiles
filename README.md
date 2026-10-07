#  Dot Files for Delong

Inspired by [ryanb](https://github.com/ryanb/dotfiles) and [skwp](https://github.com/skwp/dotfiles)

## Install

```
git clone https://github.com/delfu/dotfiles.git
cd dotfiles
python3 install.py
```

This installs oh-my-zsh, Homebrew, the packages in `Brewfile` and nvm, copies
the custom git commands into `~/.local/bin`, and copies the dotfiles into
`$HOME`. It then offers to set up an ed25519 SSH key, log in to GitHub with
`gh` (which can upload the key), and make zsh your default shell.

To add a package, add it to `Brewfile` and run `brew bundle`.

Options:

- `--dotfiles-only` just copy dotfiles and git commands, skip installs and account setup
- `--dry-run` print what would happen without changing anything

Dotfiles are **copied**, not symlinked, so editing `~/.zshrc` etc. doesn't touch
this repo. Changes you want to keep have to be copied back with `sync.py`. Any
existing file that differs is replaced, with no backup.

Machine- or work-specific shell settings go in `~/.zshrc.local`, which `zshrc`
sources if it exists. `install.py` asks for `git user.email` per machine.

## Sync back

To pull edits made in `$HOME` back into the repo on a machine that's already set up:

```
python3 sync.py
```

It copies every file `install.py` installs back to its place in the repo, deletions
included, and leaves the changes uncommitted so you can review them with `git diff`.
Only `df-*` skills are synced; other skills in `~/.agents/skills` are workplace
specific. It asks before adding or removing a whole skill, Claude mod or git command. It never copies
`git user.email`. At the end it lists added lines that look work specific: lines
that mention your git email's company domain, plus any `--flag REGEX` you pass.
Use `--dry-run` to preview.

## macOS settings

- **Keyboard shortcuts** (System Settings > Keyboard > Keyboard Shortcuts) live in
  `macos/symbolichotkeys.plist`. `install.py` loads them and `sync.py` exports them
  back. A few only take effect after logging out.
- **Vorssaint** settings live in `macos/vorssaint.plist`, a file exported from
  Vorssaint's Settings > Advanced. On a fresh install, `install.py` loads it before
  Vorssaint first runs. If Vorssaint is already set up, import the file from the app.
  `sync.py` can't export it, so re-export from the app when you change something.
- **Alfred** is installed from the Brewfile. To carry its settings across, point it at a
  synced folder in Alfred > Advanced > Syncing.

## Agent config

`agents/` is the single source of truth for coding-agent config. `install.py`
copies `agents/AGENTS.md` to `~/AGENTS.md` and `agents/skills` to
`~/.agents/skills`, then symlinks Claude Code to them:

- `~/.claude/CLAUDE.md` -> `~/AGENTS.md`
- `~/.claude/skills` -> `~/.agents/skills`

Claude Code's own settings are copied too: `agents/claude/settings.json` to
`~/.claude/settings.json` and `agents/claude/mods` to `~/.claude/mods`.

Skills and mods are installed one at a time, so ones that only exist on a machine
(like workplace skills) are left in place.

As with the other dotfiles, edits to a skill or `~/AGENTS.md` have to be synced
back into `agents/` with `sync.py` to keep them.

The Terminal.app color scheme (`colors.terminal`) has to be imported by hand in
Terminal > Settings > Profiles.

## Uninstall

Double check the contents of the files before removing them so you don't lose custom settings.

```
rm -rf ~/.vim ~/.oh-my-zsh
rm ~/.vimrc ~/.zshrc ~/.gitconfig ~/.gitignore_global
rm -rf ~/AGENTS.md ~/.agents/skills ~/.claude/CLAUDE.md ~/.claude/skills ~/.claude/mods ~/.claude/settings.json
rm ~/.local/bin/git-prom ~/.local/bin/git-undo ~/.local/bin/git-unstage
chsh -s /bin/bash # change back to Bash if you want
```
