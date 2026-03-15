"""Shared utilities for workspace scripts."""

import json
import re
from pathlib import Path

WORKSPACE_FILE = Path(__file__).resolve().parent.parent / "ModernAppTemplate.code-workspace"


def get_repos():
    """Return list of (name, path) for each git repo in the workspace."""
    # Strip JSONC features (comments, trailing commas) before parsing
    text = WORKSPACE_FILE.read_text()
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    workspace = json.loads(text)
    workspace_dir = WORKSPACE_FILE.parent

    repos = []

    for folder in workspace["folders"]:
        path = (workspace_dir / folder["path"]).resolve()
        name = folder.get("name", path.name)

        if not (path / ".git").exists():
            continue

        repos.append((name, path))

    return repos
