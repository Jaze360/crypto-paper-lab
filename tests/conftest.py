import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest

@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_LAB_DATA_DIR",str(tmp_path/"state"))
    monkeypatch.delenv("COINGECKO_API_KEY",raising=False)
    monkeypatch.delenv("COINGECKO_PLAN",raising=False)
    import app
    app._sessions.clear()
    yield
    app._sessions.clear()
