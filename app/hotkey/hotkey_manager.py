import ctypes, sys, threading
from ctypes import wintypes
from PySide6.QtCore import QObject, Signal

from app.hotkey.keys import MODS, parse, pynput_combo, win_vk


class HotkeyManager(QObject):
    triggered = Signal()
    failed = Signal()

    def __init__(self, combo, hid=1):
        super().__init__(); self.combo, self.tid, self._listener, self.hid = combo, None, None, hid

    def _start_pynput(self):
        try:                                   # macOS: needs Input Monitoring / Accessibility permission
            from pynput import keyboard
            self._listener = keyboard.GlobalHotKeys({pynput_combo(*parse(self.combo)): self.triggered.emit})
            self._listener.start()
        except Exception:
            self.failed.emit()

    def start(self):
        try:
            parse(self.combo)
        except ValueError:
            self.failed.emit(); return
        if sys.platform != "win32":
            return self._start_pynput()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        u = ctypes.windll.user32
        mods, key = parse(self.combo)
        self.tid = ctypes.windll.kernel32.GetCurrentThreadId()
        if not u.RegisterHotKey(None, self.hid, mods | 0x4000, win_vk(key)):   # 0x4000 = no auto-repeat
            self.failed.emit(); return
        msg = wintypes.MSG()
        while u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:  # WM_HOTKEY
                self.triggered.emit()
        u.UnregisterHotKey(None, self.hid)

    def stop(self):
        if self._listener:
            self._listener.stop()
            return
        if self.tid:
            ctypes.windll.user32.PostThreadMessageW(self.tid, 0x0012, 0, 0)  # WM_QUIT
