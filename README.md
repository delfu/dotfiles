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
this repo. Changes you want to keep have to be copied back here by hand. Any
existing file that differs is replaced, with no backup.

Machine- or work-specific shell settings go in `~/.zshrc.local`, which `zshrc`
sources if it exists. `install.py` asks for `git user.email` per machine.

## Agent config

`agents/` is the single source of truth for coding-agent config. `install.py`
copies `agents/AGENTS.md` to `~/AGENTS.md` and `agents/skills` to
`~/.agents/skills`, then symlinks Claude Code to them:

- `~/.claude/CLAUDE.md` -> `~/AGENTS.md`
- `~/.claude/skills` -> `~/.agents/skills`

As with the other dotfiles, edits to a skill or `~/AGENTS.md` have to be copied
back into `agents/` to keep them.

The Terminal.app color scheme (`colors.terminal`) has to be imported by hand in
Terminal > Settings > Profiles.

## Uninstall

Double check the contents of the files before removing them so you don't lose custom settings.

```
rm -rf ~/.vim ~/.oh-my-zsh
rm ~/.vimrc ~/.zshrc ~/.gitconfig ~/.gitignore_global
rm -rf ~/AGENTS.md ~/.agents/skills ~/.claude/CLAUDE.md ~/.claude/skills
rm ~/.local/bin/git-prom ~/.local/bin/git-undo ~/.local/bin/git-unstage
chsh -s /bin/bash # change back to Bash if you want
```
