# Durable media for private-repository PRs

Use this procedure before `gh pr create --body-file`: `gh` does not upload local Markdown image paths. Only publish media approved for the repository audience; inspect captures for user identifiers and secrets. Replace every local image reference with a durable URL, then check the rendered body after publication.

## Assets branch (works before the PR exists)

Choose a new, unique `<ticket>-pr-assets` branch and a temporary directory containing only the intended media. Set `PR_REPO_ROOT`, the absolute `ASSETS_DIR`, and `ASSETS_BRANCH`. Substitute the actual explicit filenames below; do not copy the whole project. This isolated index builds an orphan commit without changing the branch, checkout, or real index:

```bash
(
  set -eu
  PR_ASSET_INDEX=$(mktemp)
  rm -- "$PR_ASSET_INDEX"
  export GIT_INDEX_FILE="$PR_ASSET_INDEX"
  trap 'rm -f -- "$PR_ASSET_INDEX"' EXIT
  git -C "$PR_REPO_ROOT" read-tree --empty
  git -C "$PR_REPO_ROOT" --work-tree="$ASSETS_DIR" add -- before.png after.png demo.webp
  PR_ASSET_TREE=$(git -C "$PR_REPO_ROOT" write-tree)
  PR_ASSET_SHA=$(printf '%s\n' 'docs: add PR review media' | git -C "$PR_REPO_ROOT" commit-tree "$PR_ASSET_TREE")
  git -C "$PR_REPO_ROOT" push origin "${PR_ASSET_SHA}:refs/heads/${ASSETS_BRANCH}"
)
```

Stop on any command failure. Verify the branch name is unused before pushing; never force-update an existing assets branch. Embed `https://github.com/Wispr-AI/aria-flow/blob/<assets-branch>/demo.webp?raw=true` (URL-encode special path characters). Keep the branch after merge so the images remain readable. Brace SHA variables in refspecs: zsh treats `$SHA:r` as a modifier.

## GitHub user attachments (authenticated browser)

In an authorized GitHub PR description editor, use the browser tool's supported file-input upload operation to upload the image or video. With Claude-in-Chrome, find the editor's file input and call `file_upload`; do not click it into a native file picker. Wait for the generated `https://github.com/user-attachments/assets/...` URL, copy it into the final body file, and save that body. For a new PR with no suitable editor, use the assets branch above. Never publish local paths hoping `gh` will upload them.

Devin's `git_create_pr` / `git_update_pr` can upload local images, including animated webp, but returned proxy URLs may expire in seven days. Preserve a durable assets-branch copy and use its URL in the canonical body. These tool-specific uploads do not apply to `gh` publication.

## Bounded headless capture

For a local Storybook iframe on macOS, use the installed Chrome binary with a bounded process timeout (replace the URL/output with the intended surface):

```python
import subprocess
from pathlib import Path

output = Path('/tmp/pr-demo.png')
output.unlink(missing_ok=True)
try:
    subprocess.run([
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '--headless=new', f'--screenshot={output}', '--window-size=900,700',
        '--timeout=15000', 'http://localhost:6006/iframe.html?id=<story-id>&viewMode=story',
    ], timeout=20, check=True)
except subprocess.TimeoutExpired:
    pass  # Chrome can hang after writing the screenshot.
assert output.is_file() and output.stat().st_size > 0
```

Inspect the resulting image before upload; file existence alone does not establish that the intended state rendered. State the actual surface/stubs and untested app integrations next to the media in Testing.
