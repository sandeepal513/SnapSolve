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
