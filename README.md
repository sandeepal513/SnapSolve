# SnapSolve

Hotkey (Ctrl+Shift+A) -> drag a region -> OCR -> clipboard -> parse -> Groq -> bottom-right answer.

## Run (Windows 10/11)
    python -m venv .venv && .venv\Scripts\activate
    python -m pip install -r requirements.txt
    python -m app.main
Then right-click the tray icon > Set API Key... and paste your Groq key (starts with gsk_).
Get a key at https://console.groq.com/keys

## Build the portable .exe (no installer / no admin)
Double-click `build.bat` (needs Python 3.10-3.12 on the build PC). Result: `dist\SnapSolve.exe`.
Or push this folder to GitHub and run the "Build Windows EXE" action, then download the artifact.
On first launch the app asks for your Groq key; it is stored encrypted under %APPDATA%\SnapSolve.

## Windows 11 "Smart App Control blocked an app"
A freshly built, unsigned .exe is blocked when Smart App Control is on. Run the app from source instead:
double-click `start.bat` (needs the one-time setup above). To start with Windows, put a shortcut to
`start.bat` in the folder opened by Win+R > `shell:startup`.

## Custom logo
Put your picture in `assets/` named `icon.png` (or icon.jpg / icon.webp), then run `build.bat`.
It becomes the .exe icon and the tray icon. Square images, 256x256 or larger, look best.

## Double-click shortcut without the .exe (recommended on Windows 11 with Smart App Control)
After the one-time setup (venv + pip install), double-click `make_shortcut.bat`.
It puts a SnapSolve shortcut with your logo on the Desktop. Manual alternative: New shortcut, Target:
`"<project folder>\.venv\Scripts\pythonw.exe" -m app.main`, Start in: `<project folder>`.

## macOS
Needs macOS 11+ and Python 3.10-3.12 (python.org or Homebrew).
- Run: double-click `start.command` (first run installs everything), or
  `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python -m app.main`
- Build an app: `./build_mac.sh` -> `dist/SnapSolve.app` (first open: right-click > Open, because it is not notarized).
- Permissions (System Settings > Privacy & Security): **Screen Recording** (to read the selected area) and
  **Input Monitoring** (for the Ctrl+Shift+A shortcut) for the app that runs SnapSolve (Terminal/Python or SnapSolve.app).
  Restart SnapSolve after allowing them.
- Settings are stored in `~/Library/Application Support/SnapSolve`; the API key is kept in the macOS Keychain.
- Text is read with Apple's built-in Vision OCR (RapidOCR is the fallback).

### Building the Mac app without a Mac
A .app can only be built on macOS. Push the project to GitHub and run the "Build SnapSolve" action:
the `build-mac` job builds it on a Mac in the cloud. Download `SnapSolve-mac` from the run's artifacts, unzip it,
right-click SnapSolve.app > Open. If macOS says the app is "damaged", run `xattr -cr SnapSolve.app` once in Terminal.
