"""Shortcut parsing (no Qt, easy to test)."""
import re

MODS = {"alt": 1, "ctrl": 2, "shift": 4, "win": 8}


def parse(combo: str):
    """'ctrl+shift+a' -> (modifier_flags, key). Key = one letter/digit or F1-F12. Raises ValueError."""
    parts = combo.lower().replace(" ", "").split("+")
    key, mods = parts[-1], 0
    for p in parts[:-1]:
        p = "win" if p in ("cmd", "command", "super") else p
        if p not in MODS:
            raise ValueError(f"Unknown key '{p}'. Use ctrl, alt, shift or win.")
        mods |= MODS[p]
    if not mods:
        raise ValueError("Add at least one of ctrl, alt, shift or win.")
    if not ((len(key) == 1 and key.isascii() and key.isalnum()) or re.fullmatch(r"f([1-9]|1[0-2])", key)):
        raise ValueError("The last key must be one letter, one digit, or F1-F12.")
    return mods, key


def win_vk(key: str) -> int:
    return ord(key.upper()) if len(key) == 1 else 0x70 + int(key[1:]) - 1


def pynput_combo(mods: int, key: str) -> str:
    names = {"ctrl": "<ctrl>", "alt": "<alt>", "shift": "<shift>", "win": "<cmd>"}
    return "+".join([names[n] for n, f in MODS.items() if mods & f] + [f"<{key}>" if len(key) > 1 else key])
