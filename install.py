#!/usr/bin/env python3
"""Set up a new machine from this dotfiles repo.

Dotfiles are *copied* into $HOME (not symlinked), so edits made in $HOME
don't show up as changes in this repo. Existing files that differ are replaced.
"""
import argparse
import filecmp
import os
import plistlib
import shlex
import shutil
import subprocess
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
HOME_DIR = Path.home()
LOCAL_BIN = HOME_DIR / ".local" / "bin"
OH_MY_ZSH_DIR = HOME_DIR / ".oh-my-zsh"
NVM_VERSION = "v0.40.3"

# keyboard shortcuts from System Settings > Keyboard > Keyboard Shortcuts
HOTKEYS_DOMAIN = "com.apple.symbolichotkeys"
HOTKEYS_FILE = REPO_DIR / "macos" / "symbolichotkeys.plist"
# a file saved by Vorssaint's own Settings > Advanced > Export
VORSSAINT_DOMAIN = "com.vorssaint.utils"
VORSSAINT_FILE = REPO_DIR / "macos" / "vorssaint.plist"

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


def util_run(cmd, check=True):
    print(f"[run] {cmd}")
    if not DRY_RUN:
        subprocess.run(cmd, shell=True, check=check)


def util_confirm(question):
    response = input(f"{question} [ynq] ").strip().lower()
    if response == "q":
        raise SystemExit(0)
    return response == "y"


def zsh_install_oh_my_zsh():
    if OH_MY_ZSH_DIR.exists():
        print("found ~/.oh-my-zsh")
    elif util_confirm("install oh-my-zsh?"):
        util_run(f"git clone https://github.com/ohmyzsh/ohmyzsh.git {OH_MY_ZSH_DIR}")
    else:
        print("skipping oh-my-zsh, you will need to change ~/.zshrc")


def brew_path():
    return shutil.which("brew") or next(
        (p for p in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew") if os.path.exists(p)), None
    )


def brew_install():
    if brew_path():
        print("found Homebrew")
        return
    util_run('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')


def brew_bundle():
    brew = brew_path()
    if brew:
        util_run(f"{brew} bundle --file={REPO_DIR / 'Brewfile'}")
    else:
        print("brew not found, skipping Brewfile packages")


def node_install_nvm():
    if (HOME_DIR / ".nvm").exists():
        print("found ~/.nvm")
    else:
        # PROFILE=/dev/null stops the nvm installer from appending to ~/.zshrc; our zshrc loads nvm itself
        util_run(f"curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_VERSION}/install.sh | PROFILE=/dev/null bash")


# install custom git commands to ~/.local/bin, which zshrc puts on PATH
def git_install_commands():
    print("Installing custom git commands")
    if not DRY_RUN:
        LOCAL_BIN.mkdir(parents=True, exist_ok=True)
    for command in sorted((REPO_DIR / "git-commands").iterdir()):
        if command.is_file():
            dotfiles_copy(command, LOCAL_BIN / command.name)


def dotfiles_same(src, dest):
    if dest.is_symlink() or not dest.exists():
        return False
    if src.is_dir():
        if not dest.is_dir():
            return False
        cmp = filecmp.dircmp(src, dest)
        return not (cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files) and all(
            dotfiles_same(src / d, dest / d) for d in cmp.common_dirs
        )
    return dest.is_file() and filecmp.cmp(src, dest, shallow=False)


# remove whatever is at dest so it can be replaced
def dotfiles_clear(dest):
    if dest.is_symlink() or dest.is_file():
        print(f"removing {dest}")
        if not DRY_RUN:
            dest.unlink()
    elif dest.exists():
        print(f"removing {dest}")
        if not DRY_RUN:
            shutil.rmtree(dest)


def dotfiles_copy(src, dest):
    if dotfiles_same(src, dest):
        print(f"up to date: {dest}")
        return
    dotfiles_clear(dest)
    print(f"copying {src.relative_to(REPO_DIR)} -> {dest}")
    if DRY_RUN:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dest, symlinks=True)
    else:
        shutil.copy2(src, dest)


def dotfiles_copy_all():
    for src, dest in DOTFILES.items():
        if src in MERGED_DIRS:
            for entry in sorted((REPO_DIR / src).iterdir()):
                dotfiles_copy(entry, HOME_DIR / dest / entry.name)
        else:
            dotfiles_copy(REPO_DIR / src, HOME_DIR / dest)


def dotfiles_link(dest, target):
    if dest.is_symlink() and dest.resolve() == target.resolve():
        print(f"up to date: {dest} -> {target}")
        return
    dotfiles_clear(dest)
    print(f"linking {dest} -> {target}")
    if DRY_RUN:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(target)


def agents_link_config():
    for dest, target in SYMLINKS.items():
        dotfiles_link(HOME_DIR / dest, HOME_DIR / target)


def git_email():
    result = subprocess.run(["git", "config", "--global", "user.email"], capture_output=True, text=True)
    return result.stdout.strip()


def git_configure_email():
    if git_email():
        print(f"git user.email is {git_email()}")
        return
    email = input("git user.email for this machine (blank to skip): ").strip()
    if email:
        util_run(f"git config --global user.email {shlex.quote(email)}")


def ssh_setup_key():
    key = HOME_DIR / ".ssh" / "id_ed25519"
    if key.exists():
        print(f"found {key}")
        return
    if not util_confirm("generate an ed25519 SSH key?"):
        return
    if not DRY_RUN:
        key.parent.mkdir(mode=0o700, exist_ok=True)
    util_run(f"ssh-keygen -t ed25519 -C {shlex.quote(git_email() or os.environ.get('USER', ''))} -f {key}")
    # store the passphrase in the macOS keychain and load the key automatically
    ssh_config = HOME_DIR / ".ssh" / "config"
    if not ssh_config.exists() or "UseKeychain" not in ssh_config.read_text():
        print(f"adding keychain settings to {ssh_config}")
        if not DRY_RUN:
            with ssh_config.open("a") as f:
                f.write(f"\nHost *\n  AddKeysToAgent yes\n  UseKeychain yes\n  IdentityFile {key}\n")
    util_run(f"ssh-add --apple-use-keychain {key}", check=False)


def gh_login():
    # on a fresh machine Homebrew's bin dir isn't on this process's PATH yet
    brew = brew_path()
    gh = shutil.which("gh") or (brew and shutil.which("gh", path=os.path.dirname(brew)))
    if not gh:
        print("gh not found, skipping GitHub login")
        return
    if subprocess.run([gh, "auth", "status"], capture_output=True).returncode == 0:
        print("already logged in to GitHub")
    elif util_confirm("log in to GitHub with gh? (it can also upload your SSH key)"):
        util_run(f"{gh} auth login", check=False)


def zsh_set_default_shell():
    zsh = shutil.which("zsh") or "/bin/zsh"
    if os.environ.get("SHELL", "").endswith("/zsh"):
        print("default shell is already zsh")
    elif util_confirm("make zsh your default shell?"):
        util_run(f"chsh -s {zsh}")


# takes effect after logging out and back in
def mac_disable_mouse_acceleration():
    util_run("defaults write .GlobalPreferences com.apple.mouse.scaling -1")


def mac_restore_hotkeys():
    util_run(f"defaults import {HOTKEYS_DOMAIN} {shlex.quote(str(HOTKEYS_FILE))}")
    # applies them without logging out; a few only switch over after a logout
    util_run("/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u", check=False)


def mac_has_defaults(domain):
    return subprocess.run(["defaults", "read", domain], capture_output=True).returncode == 0


# Vorssaint only imports backups through its UI, so on a fresh install write the backup's
# settings straight into its defaults before its first launch, which is what its import does
def vorssaint_restore():
    if not VORSSAINT_FILE.exists():
        print(f"no {VORSSAINT_FILE.relative_to(REPO_DIR)}, skipping Vorssaint settings")
        return
    if mac_has_defaults(VORSSAINT_DOMAIN):
        print(f"Vorssaint is already set up; import {VORSSAINT_FILE} from its Settings > Advanced if you want it")
        return
    with VORSSAINT_FILE.open("rb") as f:
        settings = plistlib.load(f)["settings"]
    print(f"loading Vorssaint settings from {VORSSAINT_FILE.relative_to(REPO_DIR)}")
    if not DRY_RUN:
        subprocess.run(["defaults", "import", VORSSAINT_DOMAIN, "-"], input=plistlib.dumps(settings), check=True)


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print what would happen without changing anything")
    parser.add_argument("--dotfiles-only", action="store_true", help="only copy dotfiles and git commands, skip installs")
    args = parser.parse_args()
    DRY_RUN = args.dry_run or os.environ.get("DEBUG") == "1"

    if not args.dotfiles_only:
        zsh_install_oh_my_zsh()
        brew_install()
        brew_bundle()
        node_install_nvm()
        mac_disable_mouse_acceleration()
        mac_restore_hotkeys()
        vorssaint_restore()
    git_install_commands()
    dotfiles_copy_all()
    agents_link_config()
    git_configure_email()
    if not args.dotfiles_only:
        ssh_setup_key()
        gh_login()
        zsh_set_default_shell()
    print("\nDone. Import colors.terminal manually in Terminal > Settings > Profiles if you want the color scheme.")


if __name__ == "__main__":
    main()
