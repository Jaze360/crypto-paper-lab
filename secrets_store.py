"""Windows DPAPI: key encrypted for the current Windows account, never returned to UI."""
import ctypes
import os
from ctypes import wintypes
from storage import data_dir

class Blob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_char))]

def crypt(value, decrypt=False):
    if os.name != "nt":
        raise ValueError("API-sleutel bewaren vereist Windows; gebruik anders omgevingsvariabelen.")
    buf = ctypes.create_string_buffer(value)
    source = Blob(len(value), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    target = Blob()
    api = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not api(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ValueError("Windows kon de API-sleutel niet versleutelen/ontsleutelen.")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.windll.kernel32.LocalFree(target.data)

def save_key(key):
    path = data_dir() / "coingecko.dpapi"
    temp = path.with_suffix(".tmp")
    temp.write_bytes(crypt(key.encode("utf-8")))
    os.replace(temp, path)

def get_key():
    path = data_dir() / "coingecko.dpapi"
    if path.exists():
        return crypt(path.read_bytes(), True).decode("utf-8")
    return os.environ.get("COINGECKO_API_KEY", "")

