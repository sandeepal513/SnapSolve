"""Small OS-specific helpers. Windows behaviour is unchanged; macOS gets its own equivalents."""
import ctypes, sys

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
_quartz = None


def mouse_down() -> bool:
    """True while any mouse button (left/right/middle) is held, anywhere on screen."""
    global _quartz
    if IS_WIN:
        gs = ctypes.windll.user32.GetAsyncKeyState
        return any(gs(vk) & 0x8000 for vk in (0x01, 0x02, 0x04))
    if IS_MAC:
        try:
            if _quartz is None:
                import Quartz
                _quartz = Quartz
            st = _quartz.kCGEventSourceStateCombinedSessionState
            return any(_quartz.CGEventSourceButtonState(st, b) for b in (0, 1, 2))  # left/right/middle
        except Exception:
            return False
    return False


def mac_setup():
    """Menu-bar app: no Dock icon (call after QApplication exists)."""
    if IS_MAC:
        try:
            from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
            NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        except Exception:
            pass


def mac_activate():
    """Bring the app to the front so dialogs / the selection overlay receive keyboard input."""
    if IS_MAC:
        try:
            from AppKit import NSApplication
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except Exception:
            pass
