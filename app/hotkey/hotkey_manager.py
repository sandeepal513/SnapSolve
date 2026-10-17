import ctypes, sys, threading
from ctypes import wintypes
from PySide6.QtCore import QObject, Signal

MODS = {"alt": 1, "ctrl": 2, "shift": 4, "win": 8}

class HotkeyManager(QObject):
    triggered = Signal()
    failed = Signal()

    def __init__(self, combo):
        super().__init__(); self.combo, self.tid, self._listener = combo, None, None

    def _start_pynput(self):
        try:                                   # macOS: needs Input Monitoring / Accessibility permission
            from pynput import keyboard
            names = {"ctrl": "<ctrl>", "alt": "<alt>", "shift": "<shift>", "win": "<cmd>", "cmd": "<cmd>"}
            parts = self.combo.lower().replace(" ", "").split("+")
            combo = "+".join([names[p] for p in parts[:-1]] + [parts[-1]])
            self._listener = keyboard.GlobalHotKeys({combo: self.triggered.emit})
            self._listener.start()
        except Exception:
            self.failed.emit()

    def start(self):
        if sys.platform != "win32":
            return self._start_pynput()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        u = ctypes.windll.user32
        parts = self.combo.lower().replace(" ", "").split("+")
        mods = 0x4000  # MOD_NOREPEAT
        for p in parts[:-1]:
            mods |= MODS[p]
        self.tid = ctypes.windll.kernel32.GetCurrentThreadId()
        if not u.RegisterHotKey(None, 1, mods, ord(parts[-1].upper())):
            self.failed.emit(); return
        msg = wintypes.MSG()
        while u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:  # WM_HOTKEY
                self.triggered.emit()
        u.UnregisterHotKey(None, 1)

    def stop(self):
        if self._listener:
            self._listener.stop()
            return
        if self.tid:
            ctypes.windll.user32.PostThreadMessageW(self.tid, 0x0012, 0, 0)  # WM_QUIT
