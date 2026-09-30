#!/usr/bin/env python3
"""Set up a new machine from this dotfiles repo.

Dotfiles are *copied* into $HOME (not symlinked), so edits made in $HOME
don't show up as changes in this repo. Existing files that differ are backed
up to <name>.bak before being replaced.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
HOME_DIR = Path.home()
LOCAL_BIN = HOME_DIR / ".local" / "bin"
OH_MY_ZSH_DIR = HOME_DIR / ".oh-my-zsh"
BREW_PACKAGES = ["ack", "bat", "gh", "git-lfs"]
NVM_VERSION = "v0.40.3"

# repo path -> destination in $HOME
DOTFILES = {
    "zshrc": ".zshrc",
    "vimrc": ".vimrc",
    "vim": ".vim",
    "zsh": ".zsh",
    "gitconfig": ".gitconfig",
    "gitignore_global": ".gitignore_global",
    "KeyBindings/DefaultKeyBinding.dict": "Library/KeyBindings/DefaultKeyBinding.dict",
}

DRY_RUN = False


def run(cmd, check=True):
    print(f"[run] {cmd}")
    if not DRY_RUN:
        subprocess.run(cmd, shell=True, check=check)


def confirm(question):
    response = input(f"{question} [ynq] ").strip().lower()
    if response == "q":
        raise SystemExit(0)
    return response == "y"


def install_oh_my_zsh():
    if OH_MY_ZSH_DIR.exists():
        print("found ~/.oh-my-zsh")
    elif confirm("install oh-my-zsh?"):
        run(f"git clone https://github.com/ohmyzsh/ohmyzsh.git {OH_MY_ZSH_DIR}")
    else:
        print("skipping oh-my-zsh, you will need to change ~/.zshrc")


def brew_path():
    return shutil.which("brew") or next(
        (p for p in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew") if os.path.exists(p)), None
    )


def install_homebrew():
    if brew_path():
        print("found Homebrew")
        return
    run('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')


def install_bins():
    brew = brew_path()
    if brew:
        run(f"{brew} install {' '.join(BREW_PACKAGES)}")
    else:
        print("brew not found, skipping packages: " + " ".join(BREW_PACKAGES))

    if (HOME_DIR / ".nvm").exists():
        print("found ~/.nvm")
    else:
        # PROFILE=/dev/null stops the nvm installer from appending to ~/.zshrc; our zshrc loads nvm itself
        run(f"curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_VERSION}/install.sh | PROFILE=/dev/null bash")


# install custom git commands to ~/.local/bin, which zshrc puts on PATH
def install_git_commands():
    print("Installing custom git commands")
    if not DRY_RUN:
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)
    for command in sorted((REPO_DIR / "git-commands").iterdir()):
        if command.is_file():
            copy(command, LOCAL_BIN / command.name)


def same(src, dest):
    if dest.is_symlink() or not dest.exists():
        return False
    if src.is_dir():
        if not dest.is_dir():
            return False
        cmp = filecmp.dircmp(src, dest)
        return not (cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files) and all(
            same(src / d, dest / d) for d in cmp.common_dirs
        )
    return dest.is_file() and filecmp.cmp(src, dest, shallow=False)


def copy(src, dest):
    if same(src, dest):
        print(f"up to date: {dest}")
        return
    if dest.is_symlink():
        # e.g. a leftover symlink from the old install into this repo
        print(f"removing symlink {dest} -> {os.readlink(dest)}")
        if not DRY_RUN:
            dest.unlink()
    elif dest.exists():
        backup = dest.with_name(dest.name + ".bak")
        print(f"backing up {dest} -> {backup}")
        if not DRY_RUN:
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            elif backup.exists() or backup.is_symlink():
                backup.unlink()
            dest.rename(backup)
    print(f"copying {src.relative_to(REPO_DIR)} -> {dest}")
    if DRY_RUN:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dest, symlinks=True)
    else:
        shutil.copy2(src, dest)


def copy_dotfiles():
    for src, dest in DOTFILES.items():
        copy(REPO_DIR / src, HOME_DIR / dest)


def configure_git_email():
    result = subprocess.run(["git", "config", "--global", "user.email"], capture_output=True, text=True)
    if result.stdout.strip():
        print(f"git user.email is {result.stdout.strip()}")
        return
    email = input("git user.email for this machine (blank to skip): ").strip()
    if email:
        run(f"git config --global user.email {email!r}")


def configure_macos():
    # disable mouse acceleration (takes effect after logging out and back in)
    run("defaults write .GlobalPreferences com.apple.mouse.scaling -1")


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print what would happen without changing anything")
    parser.add_argument("--dotfiles-only", action="store_true", help="only copy dotfiles and git commands, skip installs")
    args = parser.parse_args()
    DRY_RUN = args.dry_run or os.environ.get("DEBUG") == "1"

    if not args.dotfiles_only:
        install_oh_my_zsh()
        install_homebrew()
        install_bins()
        configure_macos()
    install_git_commands()
    copy_dotfiles()
    configure_git_email()
    print("\nDone. Import colors.terminal manually in Terminal > Settings > Profiles if you want the color scheme.")


if __name__ == "__main__":
    main()
