"""Show a saved file in the system file manager."""

from __future__ import annotations

import os
import subprocess
import sys


def reveal_label(platform: str = sys.platform) -> str:
    if platform == "darwin":
        return "Show in Finder"
    if platform == "win32":
        return "Show in Explorer"
    return "Open folder"


def reveal_command(path: str, platform: str = sys.platform) -> list[str]:
    """Finder and Explorer select the file; elsewhere the containing folder opens."""
    if platform == "darwin":
        return ["open", "-R", path]
    if platform == "win32":
        return ["explorer", f"/select,{path}"]
    return ["xdg-open", os.path.dirname(os.path.abspath(path))]


def reveal(path: str) -> None:
    subprocess.Popen(reveal_command(path))
