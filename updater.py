"""Explicit updates from one private GitHub repo, authenticated with GitHub CLI.
Stage during use; apply only before starting the server. All overwritten code is backed up.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import zipfile
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone
from storage import data_dir

ROOT = Path(__file__).resolve().parent
REPO = "Jaze360/crypto-paper-lab"
_LOCK = __import__("threading").Lock()

def gh(*args, binary=False):
    # Public repositories need no credentials. Private repos fall back to gh's own login.
    endpoint = args[-1]
    if len(args) != 2 or args[0] != "api" or not endpoint.startswith(f"repos/{REPO}/"):
        raise ValueError("Niet toegestane GitHub-aanvraag.")
    try:
        request = Request("https://api.github.com/" + endpoint,
                          headers={"User-Agent":"CryptoPaperLab/0.2", "Accept":"application/vnd.github+json"})
        with urlopen(request, timeout=90) as response:
            content = response.read(20_000_001)
        if len(content) > 20_000_000:
            raise ValueError("GitHub-download is te groot.")
        return content if binary else content.decode("utf-8")
    except HTTPError as exc:
        if exc.code not in (401,403,404,429):
            raise ValueError(f"GitHub antwoordt met HTTP {exc.code}; probeer later opnieuw.") from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError("GitHub niet bereikbaar; controleer je internetverbinding.") from exc
    exe = shutil.which("gh")
    if not exe:
        raise ValueError("GitHub geeft geen toegang of de publieke limiet is bereikt. Voor een private repo of hogere limiet: installeer GitHub CLI via winget install --id GitHub.cli -e en voer gh auth login uit.")
    result = subprocess.run([exe, *args], capture_output=True, timeout=120,
                            creationflags=0x08000000 if os.name == "nt" else 0)
    if result.returncode:
        raise ValueError("GitHub niet bereikbaar of geen toegang tot de private repo. Voer gh auth login uit en controleer je verbinding.")
    return result.stdout if binary else result.stdout.decode("utf-8")

def installed():
    path = ROOT / ".installed-commit"
    return path.read_text().strip() if path.exists() else None

def check():
    latest = json.loads(gh("api", f"repos/{REPO}/commits/main"))
    sha = latest["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Ongeldige commit van GitHub.")
    pending = data_dir() / "pending-update.json"
    return dict(installed=installed(), latest=sha, available=installed()!=sha,
                message=latest["commit"]["message"].splitlines()[0],
                pending=pending.exists(), url=f"https://github.com/{REPO}/commit/{sha}")

def archive_files(raw):
    """No extractall, symlinks, secrets, traversal, executable binaries, or unbounded archives."""
    import io
    if len(raw) > 20_000_000:
        raise ValueError("Update is te groot.")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        if len(infos) > 300 or sum(i.file_size for i in infos) > 30_000_000:
            raise ValueError("Te veel updatebestanden.")
        result = {}
        roots = set()
        for info in infos:
            parts = PurePosixPath(info.filename).parts
            if not parts or any(p in ("..", ".") for p in parts) or "\\" in info.filename or info.filename.startswith("/"):
                raise ValueError("Onveilig updatepad.")
            roots.add(parts[0])
            if info.is_dir():
                continue
            if len(parts) < 2 or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Ongeldig updatebestand.")
            path = PurePosixPath(*parts[1:])
            name = str(path)
            if any(p.startswith(".") for p in path.parts) and name not in (".gitignore", ".env.example"):
                raise ValueError("Verborgen bestanden zijn niet toegestaan in updates.")
            if path.suffix not in (".py", ".js", ".html", ".css", ".md", ".txt", ".bat", ".json") and name not in (".gitignore", ".env.example"):
                raise ValueError("Bestandstype niet toegestaan.")
            if len(path.parts) > 1 and path.parts[0] not in ("static", "tests"):
                raise ValueError("Map niet toegestaan.")
            if name in result or path.name.lower() in ("con", "nul", "aux", "prn") or ":" in name:
                raise ValueError("Ongeldige bestandsnaam.")
            result[name] = z.read(info)
        if len(roots) != 1 or not {"app.py", "updater.py", "storage.py", "start_lab.py", "secrets_store.py", "market_data.py", "research.py", "engine.py", "strategies.py", "static/index.html", "static/app.js", "static/style.css", "requirements.txt", "START_WINDOWS.bat", "version.json"}.issubset(result):
            raise ValueError("Update mist verplichte bronbestanden.")
        version = json.loads(result["version.json"])
        if version.get("paper_only") is not True:
            raise ValueError("Update is niet als paper-only gemarkeerd.")
        release=version.get("version","")
        if not isinstance(release,str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+",release):
            raise ValueError("Ongeldige updateversie.")
        if tuple(map(int,release.split(".")))>=(0,13,0):
            required={"simple_lab.py","protocol.py","universe.py","cartridges.py","cartridge_api.py",
                      "cartridge_ema.py","cartridge_rsi.py","cartridge_breakout.py","cartridge_pullback.py",
                      "static/lab.html","static/lab.js","static/lab.css"}
            if not required.issubset(result):raise ValueError("Update mist bestanden voor het cartridgelab.")
        if tuple(map(int,release.split(".")))>=(0,14,0):
            if not {"cartridge_momentum63.py","cartridge_donchian55.py","slow_features.py"}.issubset(result):
                raise ValueError("Update mist de langzame cartridges.")
        return result

def stage():
    with _LOCK:
        info = check()
        if not info["available"]:
            return dict(**info, staged=False)
        raw = gh("api", f"repos/{REPO}/zipball/{info['latest']}", binary=True)
        files = archive_files(raw)
        folder = data_dir()
        temp = folder / "update.zip.tmp"
        temp.write_bytes(raw)
        os.replace(temp, folder / "update.zip")
        manifest = {"sha": info["latest"], "sha256": hashlib.sha256(raw).hexdigest(),
                    "files": sorted(files), "root": str(ROOT)}
        tmpmanifest = folder / "pending-update.tmp"
        tmpmanifest.write_text(json.dumps(manifest), encoding="utf-8")
        os.replace(tmpmanifest, folder / "pending-update.json")
        return dict(**info, staged=True, note="Update klaar. Sluit het servervenster en start START_WINDOWS.bat opnieuw. Eerst wordt een back-up gemaakt.")

def restore(journal):
    backup = Path(journal["backup"])
    for name, existed in journal["files"].items():
        target = ROOT / name
        if existed:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup / name, target)
        elif target.exists():
            target.unlink()

def apply():
    folder = data_dir()
    transaction = folder / "update-transaction.json"
    if transaction.exists():
        journal = json.loads(transaction.read_text())
        if journal["root"] != str(ROOT):
            raise ValueError("Er is een onderbroken update van een andere installatie.")
        restore(journal)
        transaction.unlink()
    pending = folder / "pending-update.json"
    if not pending.exists():
        return
    manifest = json.loads(pending.read_text())
    if manifest["root"] != str(ROOT):
        raise ValueError("De klaargezette update hoort bij een andere installatiemap.")
    raw = (folder / "update.zip").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
        raise ValueError("Updatebestand is beschadigd; haal de update opnieuw op.")
    files = archive_files(raw)
    files[".installed-commit"] = manifest["sha"].encode()
    backup = folder / "backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    backup.mkdir(parents=True)
    journal = {"root": str(ROOT), "backup": str(backup), "files": {}}
    for name in files:
        target = ROOT / name
        if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != ROOT.parent):
            raise ValueError("Update naar symbolische link niet toegestaan.")
        journal["files"][name] = target.exists()
        if target.exists():
            dest = backup / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, dest)
    transaction.write_text(json.dumps(journal), encoding="utf-8")
    try:
        for name, content in files.items():
            target = ROOT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(target.name + ".update-tmp")
            temp.write_bytes(content)
            os.replace(temp, target)
    except Exception:
        restore(journal)
        transaction.unlink()
        raise
    transaction.unlink()
    pending.unlink()
    print("Update toegepast. Back-up:", backup)

if __name__ == "__main__":
    import sys
    try:
        if sys.argv[1:] == ["--apply"]:
            # Never alter files while this installation is serving requests.
            import socket
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", 8501)) == 0:
                    if (data_dir() / "pending-update.json").exists():
                        raise ValueError("Sluit eerst de draaiende app op poort 8501.")
                else:
                    apply()
        else:
            print(json.dumps(check(), indent=2))
    except Exception as exc:
        print("Updatefout:", exc)
        sys.exit(1)


