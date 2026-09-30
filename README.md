#  Dot Files for Delong

Inspired by [ryanb](https://github.com/ryanb/dotfiles) and [skwp](https://github.com/skwp/dotfiles)

## Install

```
git clone https://github.com/delfu/dotfiles.git
cd dotfiles
python3 install.py
```

This installs oh-my-zsh, Homebrew (+ a few packages) and nvm, copies the custom
git commands into `~/.local/bin`, and copies the dotfiles into `$HOME`.

Options:

- `--dotfiles-only` just copy dotfiles and git commands, skip installing anything
- `--dry-run` print what would happen without changing anything

Dotfiles are **copied**, not symlinked, so editing `~/.zshrc` etc. doesn't touch
this repo. Changes you want to keep have to be copied back here by hand. Any
existing file that differs is backed up to `<name>.bak` before being replaced.

Machine- or work-specific shell settings go in `~/.zshrc.local`, which `zshrc`
sources if it exists. `install.py` asks for `git user.email` per machine.

The Terminal.app color scheme (`colors.terminal`) has to be imported by hand in
Terminal > Settings > Profiles.

## Uninstall

Double check the contents of the files before removing them so you don't lose custom settings.

```
rm -rf ~/.vim ~/.zsh ~/.oh-my-zsh
rm ~/.vimrc ~/.zshrc ~/.gitconfig ~/.gitignore_global
rm ~/.local/bin/git-undo ~/.local/bin/git-unstage
chsh -s /bin/bash # change back to Bash if you want
```
