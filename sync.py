#!/usr/bin/env python3
"""Copy dotfiles from $HOME back into this repo, the reverse of install.py.

Run it on a machine that was already set up, then review the result with
`git diff` / `git status` before committing. Nothing is committed for you.

Some edits made on a work machine are company specific, so:
- adding or removing a whole skill or git command asks first
- the per-machine git user.email is never copied back
- lines in the resulting diff that look work specific are listed at the end
"""
import argparse
import filecmp
import re
import shutil
import subprocess
from pathlib import Path

from install import DOTFILES, HOME_DIR, LOCAL_BIN, REPO_DIR, SYMLINKS, confirm

# repo dirs whose top-level entries (one skill, one command) are added or removed only after asking
COLLECTIONS = {
    "agents/skills": HOME_DIR / ".agents" / "skills",
    "git-commands": LOCAL_BIN,
}

# junk that shows up in $HOME copies and never belongs in the repo
IGNORED = {".DS_Store", ".trash", "__pycache__", ".netrwhist", ".VimballRecord"}

# email providers whose domain says nothing about an employer
PERSONAL_DOMAINS = {"gmail", "icloud", "me", "hotmail", "outlook", "yahoo", "proton", "protonmail"}

DRY_RUN = False


def ignored(path):
    return path.name in IGNORED or path.name.endswith(("~", ".swp"))


def in_collection(name, home_dir):
    # ~/.local/bin also holds aws, claude, python etc.; only git-* commands come from this repo
    return home_dir != LOCAL_BIN or name.startswith("git-")


def write(src, dest):
    print(f"copying {src} -> {dest.relative_to(REPO_DIR)}")
    if DRY_RUN:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest, follow_symlinks=False)


def remove(dest):
    print(f"removing {dest.relative_to(REPO_DIR)}")
    if DRY_RUN:
        return
    if dest.is_dir() and not dest.is_symlink():
        shutil.rmtree(dest)
    else:
        dest.unlink()


def sync_file(src, dest):
    if not dest.exists() or not filecmp.cmp(src, dest, shallow=False):
        write(src, dest)


# mirror src into dest: copy new and changed files, drop files that are gone from src
def sync_tree(src, dest):
    src_names = {p.name for p in src.iterdir() if not ignored(p)}
    dest_names = {p.name for p in dest.iterdir() if not ignored(p)} if dest.exists() else set()
    for name in sorted(src_names | dest_names):
        s, d = src / name, dest / name
        if name not in src_names:
            remove(d)
        elif s.is_dir() and not s.is_symlink():
            if d.exists() and not d.is_dir():
                remove(d)
            sync_tree(s, d)
        else:
            if d.is_dir() and not d.is_symlink():
                remove(d)
            sync_file(s, d)


def sync_collection(repo_rel, home_dir):
    repo_dir = REPO_DIR / repo_rel
    home_names = {p.name for p in home_dir.iterdir() if not ignored(p) and in_collection(p.name, home_dir)}
    repo_names = {p.name for p in repo_dir.iterdir() if not ignored(p)}
    for name in sorted(home_names | repo_names):
        src, dest = home_dir / name, repo_dir / name
        if name not in repo_names:
            if not confirm(f"new in {home_dir}: {name}. add it to {repo_rel}/?"):
                continue
        elif name not in home_names:
            if confirm(f"{name} is gone from {home_dir}. remove it from {repo_rel}/?"):
                remove(dest)
            continue
        if src.is_dir():
            sync_tree(src, dest)
        else:
            sync_file(src, dest)


# install.py asks for user.email per machine, so keep it out of the repo's gitconfig
def scrub_gitconfig():
    gitconfig = REPO_DIR / "gitconfig"
    if DRY_RUN or not gitconfig.exists():
        return
    subprocess.run(["git", "config", "--file", str(gitconfig), "--unset-all", "user.email"], capture_output=True)


def sync_dotfiles():
    collections = {REPO_DIR / rel for rel in COLLECTIONS}
    for repo_rel, home_rel in DOTFILES.items():
        src, dest = HOME_DIR / home_rel, REPO_DIR / repo_rel
        if dest in collections:
            continue
        if not src.exists():
            print(f"missing {src}, skipping")
        elif src.is_dir():
            sync_tree(src, dest)
        else:
            sync_file(src, dest)
    for repo_rel, home_dir in COLLECTIONS.items():
        if home_dir.exists():
            sync_collection(repo_rel, home_dir)
        else:
            print(f"missing {home_dir}, skipping")
    scrub_gitconfig()


# Claude reads agent config through these symlinks; a tool that replaced one with a
# real file has edits that never reached ~/AGENTS.md or ~/.agents/skills
def check_symlinks():
    for link, target in SYMLINKS.items():
        path = HOME_DIR / link
        if path.exists() and not path.is_symlink():
            print(f"warning: {path} is no longer a symlink to ~/{target}; its edits were not synced")


def work_patterns(extra):
    patterns = list(extra)
    result = subprocess.run(["git", "config", "--global", "user.email"], capture_output=True, text=True)
    email = result.stdout.strip()
    if "@" in email:
        domain = email.split("@", 1)[1]
        company = domain.split(".")[0]
        if company.lower() not in PERSONAL_DOMAINS:
            patterns += [re.escape(domain), re.escape(company)]
    return patterns


def git(*args):
    return subprocess.run(["git", "-C", str(REPO_DIR), *args], capture_output=True, text=True).stdout


# list added lines (and new untracked files) that match a work pattern, so they get a second look
def flag_work_specific(patterns):
    if not patterns:
        return
    regex = re.compile("|".join(patterns), re.IGNORECASE)
    hits = []
    current = None
    for line in git("diff", "--no-color", "-U0").splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and current and regex.search(line):
            hits.append(f"{current}: {line[1:].strip()}")
    for rel in git("ls-files", "--others", "--exclude-standard").splitlines():
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

    if git("status", "--porcelain", "--untracked-files=no") and not args.force and not DRY_RUN:
        raise SystemExit("repo has uncommitted changes; commit or stash them first, or pass --force")

    check_symlinks()
    sync_dotfiles()
    if not DRY_RUN:
        flag_work_specific(work_patterns(args.flag))
        print("\nDone. Nothing was committed. Review with `git status` and `git diff`, and move")
        print("work-specific shell settings to ~/.zshrc.local instead of committing them.")


if __name__ == "__main__":
    main()
