from pathlib import Path
import contextlib
import os
import types
import pytest

from pypia_ctl.authcheck import find_env, has_proxy_creds, has_proxy_host_port, status
from pypia_ctl.config import PiaSettings

@contextlib.contextmanager
def chdir(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)

def test_find_env_walks_up(tmp_path: Path):
    root = tmp_path
    sub = root / "a" / "b"
    sub.mkdir(parents=True)
    (root / ".env").write_text("PIA_PROXY__HOST=localhost\n", encoding="utf-8")
    with chdir(sub):
        p = find_env()
    assert p == root / ".env"

def test_has_proxy_flags_roundtrip(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "PIA_PROXY__HOST=localhost\n"
        "PIA_PROXY__PORT=1080\n"
        "PIA_PROXY__USERNAME=alice\n"
        "PIA_PROXY__PASSWORD=secret\n",
        encoding="utf-8",
    )
    with chdir(tmp_path):
        s = PiaSettings()
    assert has_proxy_host_port(s) is True
    assert has_proxy_creds(s) is True

def test_status_no_probe(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("PIA_PROXY__HOST=localhost\nPIA_PROXY__PORT=1080\n", encoding="utf-8")
    with chdir(tmp_path):
        st = status(probe=False)
    assert st.has_env is True
    assert st.has_proxy_host_port is True
    assert st.probe_ok is None

def test_status_probe_success(monkeypatch, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "PIA_PROXY__HOST=localhost\nPIA_PROXY__PORT=1080\nPIA_PROXY__USERNAME=u\nPIA_PROXY__PASSWORD=p\n",
        encoding="utf-8",
    )
    with chdir(tmp_path):
        # Fake httpx.Client.get success
        class DummyResp:
            status_code = 200
        class DummyClient:
            def __init__(self, *a, **k): pass
            def __enter__(self): return self
            def __exit__(self, *exc): return False
            def get(self, url): return DummyResp()
        dummy_httpx = types.SimpleNamespace(Client=DummyClient)
        monkeypatch.setitem(sys.modules, "httpx", dummy_httpx) if False else None  # optional safety
        monkeypatch.setenv("PYTHONHASHSEED", "0")  # no-op, keeps mypy quiet
        import builtins
        # Patch import inside status() by injecting into globals after import
        from pypia_ctl import authcheck as ac
        ac.httpx = dummy_httpx  # type: ignore[attr-defined]
        st = status(probe=True)
    assert st.probe_ok is True

def test_status_probe_missing_host_port(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("", encoding="utf-8")
    with chdir(tmp_path):
        st = status(probe=True)
    assert st.probe_ok is False
    assert "host/port" in (st.detail or "").lower()
