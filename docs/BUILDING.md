# Building antennacalc from source

antennacalc is pure Python plus Tkinter, so the same source runs on every platform.
Packaged apps must be built **on the target OS** (PyInstaller cannot cross-compile).
The GitHub Actions workflow in `.github/workflows/build.yml` does this automatically for
all three; the sections below show how to do it by hand.

All platforms need **Python 3.9 or newer** and this repository:

```
git clone https://github.com/WT1W-Actual/antennacalc.git
cd antennacalc
```

Then follow the section for your OS.

## Windows

1. Install Python from [python.org](https://www.python.org/downloads/) (Tkinter is included;
   leave "tcl/tk and IDLE" checked). Tick "Add python.exe to PATH".
2. In PowerShell from the repo folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-windows.txt
pip install -e .
pytest
python -m antennacalc                # run from source
pyinstaller --onefile --windowed --name antennacalc --paths src run_antennacalc.py
```

Result: `dist\antennacalc.exe`, a single file that needs no Python install. Windows
SmartScreen may warn about an unsigned app: choose **More info → Run anyway**.

## macOS

1. Install Python with Tkinter. Either use the installer from
   [python.org](https://www.python.org/downloads/) (includes Tk), or with Homebrew:
   `brew install python python-tk`.
2. In Terminal from the repo folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-macos.txt
pip install -e .
pytest
python -m antennacalc                # run from source
pyinstaller --windowed --name antennacalc --paths src run_antennacalc.py
```

Result: `dist/antennacalc.app`. Zip it for sharing with
`ditto -c -k --keepParent dist/antennacalc.app antennacalc-macos.zip`.

The build is for the CPU you build on (Apple Silicon or Intel). Because the app is
unsigned and not notarized, Gatekeeper will block the first launch: right-click the app,
choose **Open**, then **Open** again (or run `xattr -dr com.apple.quarantine antennacalc.app`).

## Linux

1. Install Python, venv support and Tkinter:

| Distro | Command |
|--------|---------|
| Debian / Ubuntu | `sudo apt install python3 python3-venv python3-tk` |
| Fedora | `sudo dnf install python3 python3-tkinter` |
| Arch | `sudo pacman -S python tk` |

2. From the repo folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-linux.txt
pip install -e .
pytest
python -m antennacalc                # run from source
pyinstaller --onefile --windowed --name antennacalc --paths src run_antennacalc.py
```

Result: `dist/antennacalc`, a single executable (`chmod +x` if needed). It is built against
your system's glibc, so build on the oldest distro you want to support. A desktop
session (X11 or Wayland with XWayland) is required to display the window.

## Running without building

If you only want to use the app, skip PyInstaller:

```
pip install .
antennacalc
```

## Publishing a release

Pushing a tag that starts with `v` (matching the version in `pyproject.toml` and
`src/antennacalc/__init__.py`, which you should bump first) runs the workflow, builds all three apps, and attaches
them to a GitHub release:

```
git tag v0.2.1
git push origin v0.2.1
```

Pushes to `main` and pull requests run the tests and build, with the apps available as
workflow artifacts.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'tkinter'`**: install the Tk package for your
  OS (see above).
- **Frozen app exits immediately with "Unhandled exception in script"**: build from
  `run_antennacalc.py`, not `src/antennacalc/__main__.py` (relative imports fail when a
  module is run as a top-level script).
- **Blurry text on high-DPI Windows displays**: this is a Tk default and does not affect results.
