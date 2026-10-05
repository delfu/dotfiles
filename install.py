#!/usr/bin/env python3
"""Set up a new machine from this dotfiles repo.

Dotfiles are *copied* into $HOME (not symlinked), so edits made in $HOME
don't show up as changes in this repo. Existing files that differ are replaced.
"""
import argparse
import filecmp
import os
import shlex
import shutil
import subprocess
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
HOME_DIR = Path.home()
LOCAL_BIN = HOME_DIR / ".local" / "bin"
OH_MY_ZSH_DIR = HOME_DIR / ".oh-my-zsh"
NVM_VERSION = "v0.40.3"

# repo path -> destination in $HOME
DOTFILES = {
    "zshrc": ".zshrc",
    "vimrc": ".vimrc",
    "vim": ".vim",
    "gitconfig": ".gitconfig",
    "gitignore_global": ".gitignore_global",
    "KeyBindings/DefaultKeyBinding.dict": "Library/KeyBindings/DefaultKeyBinding.dict",
    # agent config: one source of truth, which Claude reads through the symlinks below
    "agents/AGENTS.md": "AGENTS.md",
    "agents/skills": ".agents/skills",
    "agents/claude/settings.json": ".claude/settings.json",
    "agents/claude/mods": ".claude/mods",
}

# dirs installed entry by entry, so skills and mods that only exist on this machine
# (e.g. workplace skills in ~/.agents/skills) are left alone
MERGED_DIRS = {"agents/skills", "agents/claude/mods"}

# symlink in $HOME -> target in $HOME
SYMLINKS = {
    ".claude/CLAUDE.md": "AGENTS.md",
    ".claude/skills": ".agents/skills",
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
        run(f"{brew} bundle --file={REPO_DIR / 'Brewfile'}")
    else:
        print("brew not found, skipping Brewfile packages")

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


# remove whatever is at dest so it can be replaced
def clear(dest):
    if dest.is_symlink() or dest.is_file():
        print(f"removing {dest}")
        if not DRY_RUN:
            dest.unlink()
    elif dest.exists():
        print(f"removing {dest}")
        if not DRY_RUN:
            shutil.rmtree(dest)


def copy(src, dest):
    if same(src, dest):
        print(f"up to date: {dest}")
        return
    clear(dest)
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
        if src in MERGED_DIRS:
            for entry in sorted((REPO_DIR / src).iterdir()):
                copy(entry, HOME_DIR / dest / entry.name)
        else:
            copy(REPO_DIR / src, HOME_DIR / dest)


def link(dest, target):
    if dest.is_symlink() and dest.resolve() == target.resolve():
        print(f"up to date: {dest} -> {target}")
        return
    clear(dest)
    print(f"linking {dest} -> {target}")
    if DRY_RUN:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(target)


def link_agent_config():
    for dest, target in SYMLINKS.items():
        link(HOME_DIR / dest, HOME_DIR / target)


def git_email():
    result = subprocess.run(["git", "config", "--global", "user.email"], capture_output=True, text=True)
    return result.stdout.strip()


def configure_git_email():
    if git_email():
        print(f"git user.email is {git_email()}")
        return
    email = input("git user.email for this machine (blank to skip): ").strip()
    if email:
        run(f"git config --global user.email {shlex.quote(email)}")


def setup_ssh_key():
    key = HOME_DIR / ".ssh" / "id_ed25519"
    if key.exists():
        print(f"found {key}")
        return
    if not confirm("generate an ed25519 SSH key?"):
        return
    if not DRY_RUN:
        key.parent.mkdir(mode=0o700, exist_ok=True)
    run(f"ssh-keygen -t ed25519 -C {shlex.quote(git_email() or os.environ.get('USER', ''))} -f {key}")
    # store the passphrase in the macOS keychain and load the key automatically
    ssh_config = HOME_DIR / ".ssh" / "config"
    if not ssh_config.exists() or "UseKeychain" not in ssh_config.read_text():
        print(f"adding keychain settings to {ssh_config}")
        if not DRY_RUN:
            with ssh_config.open("a") as f:
                f.write(f"\nHost *\n  AddKeysToAgent yes\n  UseKeychain yes\n  IdentityFile {key}\n")
    run(f"ssh-add --apple-use-keychain {key}", check=False)


def gh_login():
    # on a fresh machine Homebrew's bin dir isn't on this process's PATH yet
    brew = brew_path()
    gh = shutil.which("gh") or (brew and shutil.which("gh", path=os.path.dirname(brew)))
    if not gh:
        print("gh not found, skipping GitHub login")
        return
    if subprocess.run([gh, "auth", "status"], capture_output=True).returncode == 0:
        print("already logged in to GitHub")
    elif confirm("log in to GitHub with gh? (it can also upload your SSH key)"):
        run(f"{gh} auth login", check=False)


def set_default_shell():
    zsh = shutil.which("zsh") or "/bin/zsh"
    if os.environ.get("SHELL", "").endswith("/zsh"):
        print("default shell is already zsh")
    elif confirm("make zsh your default shell?"):
        run(f"chsh -s {zsh}")


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
    link_agent_config()
    configure_git_email()
    if not args.dotfiles_only:
        setup_ssh_key()
        gh_login()
        set_default_shell()
    print("\nDone. Import colors.terminal manually in Terminal > Settings > Profiles if you want the color scheme.")


if __name__ == "__main__":
    main()
