import os

import pytest

from antennacalc.reveal import reveal_command, reveal_label


def test_macos_reveals_the_file_in_finder():
    assert reveal_command("/Users/me/r.pdf", "darwin") == ["open", "-R", "/Users/me/r.pdf"]
    assert reveal_label("darwin") == "Show in Finder"


def test_windows_selects_the_file_in_explorer():
    assert reveal_command(r"C:\Users\me\r.pdf", "win32") == [
        "explorer", r"/select,C:\Users\me\r.pdf"]
    assert reveal_label("win32") == "Show in Explorer"


@pytest.mark.parametrize("platform", ["linux", "freebsd13"])
def test_other_systems_open_the_folder(platform):
    path = os.path.join("home", "me", "r.pdf")
    assert reveal_command(path, platform) == ["xdg-open", os.path.dirname(os.path.abspath(path))]
    assert reveal_label(platform) == "Open folder"
