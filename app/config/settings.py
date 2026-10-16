import json, os, shutil
from pathlib import Path

_BASE = Path(os.getenv("APPDATA", Path.home()))
DIR = _BASE / "SnapSolve"
_OLD = _BASE / "AIScreenAssistant"          # name used before the rename
if not DIR.exists() and _OLD.exists():      # keep the saved API key and settings
    try:
        shutil.copytree(_OLD, DIR)
    except Exception:
        pass
FILE = DIR / "config.json"
KEYFILES = [DIR / "key_groq.dat", DIR / "key.dat"]   # key.dat = older versions
DEFAULTS = {"hotkey": "ctrl+shift+a", "preferred_model": "",
            "popup_seconds": 15, "temperature": 0.0, "preprocess": False}


class Settings:
    def __init__(self):
        DIR.mkdir(parents=True, exist_ok=True)
        self.data = dict(DEFAULTS)
        if FILE.exists():
            try:
                self.data.update(json.loads(FILE.read_text("utf-8")))
            except Exception:
                pass
        else:
            self.save()
        self._key = self._load_key()

    def __getitem__(self, k):
        return self.data[k]

    def save(self):
        FILE.write_text(json.dumps(self.data, indent=2), "utf-8")

    def _load_key(self) -> str:
        from app.utils.secret import unprotect
        for f in KEYFILES:                     # encrypted, tied to your Windows user
            try:
                k = unprotect(f.read_bytes()).decode("utf-8").strip()
                if k.startswith("gsk_"):
                    return k
            except Exception:
                pass
        return os.getenv("AI_API_KEY", "").strip()

    @property
    def api_key(self) -> str:
        if not self._key:                      # self-heal if the first load failed
            self._key = self._load_key()
        return self._key

    def set_api_key(self, key: str) -> bool:
        key = key.strip()
        self._key = key                        # works immediately for this session
        try:
            from app.utils.secret import protect
            KEYFILES[0].write_bytes(protect(key.encode("utf-8")))
            return True
        except Exception:
            return False
