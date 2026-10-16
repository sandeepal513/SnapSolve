"""Encrypt/decrypt small secrets with Windows DPAPI (tied to the current Windows user)."""
import ctypes
from ctypes import wintypes


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _run(fn, data: bytes) -> bytes:
    buf = ctypes.create_string_buffer(data, len(data))
    inb = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = _Blob()
    if not fn(ctypes.byref(inb), None, None, None, None, 0, ctypes.byref(out)):
        raise OSError("DPAPI failed")
    res = ctypes.string_at(out.pbData, out.cbData)
    ctypes.windll.kernel32.LocalFree(out.pbData)
    return res


def protect(data: bytes) -> bytes:
    return _run(ctypes.windll.crypt32.CryptProtectData, data)


def unprotect(data: bytes) -> bytes:
    return _run(ctypes.windll.crypt32.CryptUnprotectData, data)
