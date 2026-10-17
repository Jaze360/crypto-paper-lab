"""Stable Windows launcher: apply staged update, repair dependencies, then serve locally."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent

def main():
    if sys.version_info[:2] != (3,13):
        raise ValueError("Gebruik Python 3.13: py install 3.13")
    os.chdir(ROOT)
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1",8501)) == 0:
            raise ValueError("Poort 8501 is al in gebruik. Sluit eerst het draaiende servervenster.")
    import updater
    updater.apply()
    python = ROOT / ".venv-313/Scripts/python.exe"
    if not python.exists():
        subprocess.run([sys.executable,"-m","venv",str(ROOT/".venv-313")], check=True)
    subprocess.run([str(python),"-m","pip","install","--upgrade","pip"],check=True)
    subprocess.run([str(python),"-m","pip","install","--only-binary=:all:","-r","requirements.txt"],check=True)
    child = subprocess.Popen([str(python),"-m","uvicorn","app:app","--host","127.0.0.1","--port","8501"])
    try:
        for _ in range(60):
            if child.poll() is not None:
                raise ValueError("De server is gestopt. Controleer de foutmelding hierboven.")
            try:
                with urllib.request.urlopen("http://127.0.0.1:8501/api/status",timeout=1) as response:
                    if response.status==200:
                        webbrowser.open("http://127.0.0.1:8501")
                        break
            except OSError:
                time.sleep(.5)
        else:
            raise ValueError("De server reageert niet binnen 30 seconden.")
        child.wait()
    except KeyboardInterrupt:
        print("Crypto Paper Lab wordt afgesloten.")
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)

if __name__=="__main__":
    try:
        main()
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        print("Startfout:",exc)
        sys.exit(1)
