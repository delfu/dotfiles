#!/usr/bin/env python3
"""Copy dotfiles from $HOME back into this repo, the reverse of install.py.

Run it on a machine that was already set up, then review the result with
`git diff` / `git status` before committing. Nothing is committed for you.

Some edits made on a work machine are company specific, so:
- only df-* skills are synced; other skills are workplace specific
- adding or removing a whole skill, Claude mod or git command asks first
- the per-machine git user.email is never copied back
- lines in the resulting diff that look work specific are listed at the end
"""
import argparse
import filecmp
import re
import shutil
import subprocess
from pathlib import Path

from install import (
    DOTFILES,
    HOME_DIR,
    HOTKEYS_DOMAIN,
    HOTKEYS_FILE,
    LOCAL_BIN,
    REPO_DIR,
    SYMLINKS,
    VORSSAINT_FILE,
    git_email,
    util_confirm,
)

# repo dir -> (home dir, name prefix). Their top-level entries (one skill, mod or command) are
# added or removed only after asking, and only entries starting with the prefix are synced:
# other skills are workplace specific, and ~/.local/bin also holds aws, claude, python etc.
COLLECTIONS = {
    "agents/skills": (HOME_DIR / ".agents" / "skills", "df-"),
    "agents/claude/mods": (HOME_DIR / ".claude" / "mods", ""),
    "git-commands": (LOCAL_BIN, "git-"),
}

# junk that shows up in $HOME copies and never belongs in the repo
IGNORED = {".DS_Store", ".trash", "__pycache__", ".netrwhist", ".VimballRecord"}

# email providers whose domain says nothing about an employer
PERSONAL_DOMAINS = {"gmail", "icloud", "me", "hotmail", "outlook", "yahoo", "proton", "protonmail"}

DRY_RUN = False


def dotfiles_ignored(path):
    return path.name in IGNORED or path.name.endswith(("~", ".swp"))


def dotfiles_write(src, dest):
    print(f"copying {src} -> {dest.relative_to(REPO_DIR)}")
    if DRY_RUN:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest, follow_symlinks=False)


def dotfiles_remove(dest):
    print(f"removing {dest.relative_to(REPO_DIR)}")
    if DRY_RUN:
        return
    if dest.is_dir() and not dest.is_symlink():
        shutil.rmtree(dest)
    else:
        dest.unlink()


def dotfiles_sync_file(src, dest):
    if not dest.exists() or not filecmp.cmp(src, dest, shallow=False):
        dotfiles_write(src, dest)


# mirror src into dest: copy new and changed files, drop files that are gone from src
def dotfiles_sync_tree(src, dest):
    src_names = {p.name for p in src.iterdir() if not dotfiles_ignored(p)}
    dest_names = {p.name for p in dest.iterdir() if not dotfiles_ignored(p)} if dest.exists() else set()
    for name in sorted(src_names | dest_names):
        s, d = src / name, dest / name
        if name not in src_names:
            dotfiles_remove(d)
        elif s.is_dir() and not s.is_symlink():
            if d.exists() and not d.is_dir():
                dotfiles_remove(d)
            dotfiles_sync_tree(s, d)
        else:
            if d.is_dir() and not d.is_symlink():
                dotfiles_remove(d)
            dotfiles_sync_file(s, d)


def dotfiles_sync_collection(repo_rel, home_dir, prefix):
    repo_dir = REPO_DIR / repo_rel
    home_names = {p.name for p in home_dir.iterdir() if not dotfiles_ignored(p) and p.name.startswith(prefix)}
    repo_names = {p.name for p in repo_dir.iterdir() if not dotfiles_ignored(p)} if repo_dir.exists() else set()
    for name in sorted(home_names | repo_names):
        src, dest = home_dir / name, repo_dir / name
        if name not in repo_names:
            if not util_confirm(f"new in {home_dir}: {name}. add it to {repo_rel}/?"):
                continue
        elif name not in home_names:
            if util_confirm(f"{name} is gone from {home_dir}. remove it from {repo_rel}/?"):
                dotfiles_remove(dest)
            continue
        if src.is_dir():
            dotfiles_sync_tree(src, dest)
        else:
            dotfiles_sync_file(src, dest)


# install.py asks for user.email per machine, so keep it out of the repo's gitconfig
def git_scrub_config():
    gitconfig = REPO_DIR / "gitconfig"
    if DRY_RUN or not gitconfig.exists():
        return
    subprocess.run(["git", "config", "--file", str(gitconfig), "--unset-all", "user.email"], capture_output=True)


def dotfiles_sync():
    collections = {REPO_DIR / rel for rel in COLLECTIONS}
    for repo_rel, home_rel in DOTFILES.items():
        src, dest = HOME_DIR / home_rel, REPO_DIR / repo_rel
        if dest in collections:
            continue
        if not src.exists():
            print(f"missing {src}, skipping")
        elif src.is_dir():
            dotfiles_sync_tree(src, dest)
        else:
            dotfiles_sync_file(src, dest)
    for repo_rel, (home_dir, prefix) in COLLECTIONS.items():
        if home_dir.exists():
            dotfiles_sync_collection(repo_rel, home_dir, prefix)
        else:
            print(f"missing {home_dir}, skipping")
    git_scrub_config()


# exported as XML so changes show up in git diff
def mac_sync_hotkeys():
    print(f"exporting {HOTKEYS_DOMAIN} -> {HOTKEYS_FILE.relative_to(REPO_DIR)}")
    if DRY_RUN:
        return
    exported = subprocess.run(["defaults", "export", HOTKEYS_DOMAIN, "-"], capture_output=True, check=True).stdout
    subprocess.run(["plutil", "-convert", "xml1", "-o", str(HOTKEYS_FILE), "-"], input=exported, check=True)


# Claude reads agent config through these symlinks; a tool that replaced one with a
# real file has edits that never reached ~/AGENTS.md or ~/.agents/skills
def agents_check_symlinks():
    for link, target in SYMLINKS.items():
        path = HOME_DIR / link
        if path.exists() and not path.is_symlink():
            print(f"warning: {path} is no longer a symlink to ~/{target}; its edits were not synced")


def work_patterns(extra):
    patterns = list(extra)
    email = git_email()
    if "@" in email:
        domain = email.split("@", 1)[1]
        company = domain.split(".")[0]
        if company.lower() not in PERSONAL_DOMAINS:
            patterns += [re.escape(domain), re.escape(company)]
    return patterns


def git_run(*args):
    return subprocess.run(["git", "-C", str(REPO_DIR), *args], capture_output=True, text=True).stdout


# list added lines (and new untracked files) that match a work pattern, so they get a second look
def work_flag_lines(patterns):
    if not patterns:
        return
    regex = re.compile("|".join(patterns), re.IGNORECASE)
    hits = []
    current = None
    for line in git_run("diff", "--no-color", "-U0").splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and current and regex.search(line):
            hits.append(f"{current}: {line[1:].strip()}")
    for rel in git_run("ls-files", "--others", "--exclude-standard").splitlines():
        try:
            text = (REPO_DIR / rel).read_text()
        except (UnicodeDecodeError, OSError):
            continue
        hits += [f"{rel}:{n}: {line.strip()}" for n, line in enumerate(text.splitlines(), 1) if regex.search(line)]
    if hits:
        print(f"\nPossibly work-specific lines (matching {', '.join(patterns)}):")
        for hit in hits:
            print(f"  {hit}")


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print what would change without changing anything")
    parser.add_argument("--force", action="store_true", help="run even if the repo has uncommitted changes")
    parser.add_argument(
        "--flag",
        action="append",
        default=[],
        metavar="REGEX",
        help="also flag added lines matching REGEX as work specific (repeatable)",
    )
    args = parser.parse_args()
    DRY_RUN = args.dry_run

    if git_run("status", "--porcelain", "--untracked-files=no") and not args.force and not DRY_RUN:
        raise SystemExit("repo has uncommitted changes; commit or stash them first, or pass --force")

    agents_check_symlinks()
    dotfiles_sync()
    mac_sync_hotkeys()
    if not DRY_RUN:
        work_flag_lines(work_patterns(args.flag))
        print("\nDone. Nothing was committed. Review with `git status` and `git diff`, and move")
        print("work-specific shell settings to ~/.zshrc.local instead of committing them.")
        print(f"Vorssaint settings aren't synced: export them from its Settings > Advanced to {VORSSAINT_FILE}.")


if __name__ == "__main__":
    main()
