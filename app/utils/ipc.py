"""Tiny local command channel (Linux/macOS). Lets a keyboard shortcut created in the desktop's own
settings trigger a running SnapSolve - needed on Wayland, where apps cannot grab global keys."""
import os, socket, sys, threading
from app.config.settings import DIR

SOCK = str(DIR / "ipc.sock")
COMMANDS = ("--area", "--full", "--quit")


def available() -> bool:
    return sys.platform != "win32" and hasattr(socket, "AF_UNIX")


def send(cmd: str, path: str = SOCK) -> bool:
    """Ask a running instance to do `cmd`. False if none is running."""
    if not available():
        return False
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(0.5); s.connect(path); s.sendall(cmd.encode()); s.close()
        return True
    except Exception:
        return False


def serve(callback, path: str = SOCK):
    """Listen for commands; returns the server socket (close it to stop) or None."""
    if not available():
        return None
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            os.remove(path)
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(path); os.chmod(path, 0o600); srv.listen(4)   # only your user can connect
    except Exception:
        return None

    def loop():
        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                return
            try:
                conn.settimeout(1.0)
                data = conn.recv(32).decode(errors="ignore").strip()
                if data in COMMANDS:
                    callback(data)
            except Exception:
                pass
            finally:
                conn.close()
    threading.Thread(target=loop, daemon=True).start()
    return srv
