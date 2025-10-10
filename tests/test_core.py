import asyncio
import builtins
import types
import pytest

from pypia_ctl.core import (
    _piactl,
    fetch_status,
    get_regions,
    connect_with_strategy,
    disconnect_vpn,
    ConnectionState,
)
from pypia_ctl.exceptions import PiaCtlNotFound, PiaCtlInvocationFailed, PiaConnectTimeout

def test_piactl_not_found(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda exe: None)
    with pytest.raises(PiaCtlNotFound):
        _piactl("get", "region")

def test_piactl_invocation_failed(fake_piactl_path, monkeypatch):
    class Dummy:
        def __init__(self): self.returncode = 1; self.stdout = ""; self.stderr = "boom"
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Dummy())
    with pytest.raises(PiaCtlInvocationFailed):
        _piactl("get", "region")

def test_get_regions(fake_piactl_path, piactl_ok):
    piactl_ok(("/usr/bin/piactl","get","regions"), stdout="auto\nca-ontario\nus-new-york\n")
    regs = get_regions()
    assert regs[0] == "auto"
    assert "ca-ontario" in regs

def test_fetch_status_happy(fake_piactl_path, piactl_ok):
    piactl_ok(("/usr/bin/piactl","get","connectionstate"), stdout="Disconnected")
    piactl_ok(("/usr/bin/piactl","get","region"), stdout="auto")
    piactl_ok(("/usr/bin/piactl","get","regions"), stdout="auto\nca-ontario")
    piactl_ok(("/usr/bin/piactl","get","vpnip"), stdout="unknown")
    piactl_ok(("/usr/bin/piactl","get","protocol"), stdout="wireguard")
    piactl_ok(("/usr/bin/piactl","get","debuglogging"), stdout="false")
    piactl_ok(("/usr/bin/piactl","get","portforward"), stdout="Inactive")
    piactl_ok(("/usr/bin/piactl","get","requestportforward"), stdout="false")
    st = fetch_status()
    assert st.region == "auto"
    assert st.connection_state in ("Disconnected","Connected")
    assert st.vpn_ip is None

def test_connect_with_strategy_timeout(fake_piactl_path, monkeypatch):
    # connect call ok, but connectionstate never becomes Connected -> timeout
    class DummyOk:
        def __init__(self, out=""): self.returncode=0; self.stdout=out; self.stderr=""
    calls = {"n":0}
    def runner(cmd, capture_output=True, text=True, timeout=None):
        if cmd[-1] == "connect":
            return DummyOk("")
        if cmd[-2:] == ["get","connectionstate"]:
            # Always Disconnected to trigger timeout
            return DummyOk("Disconnected")
        if cmd[-2:] == ["set","protocol"]:
            return DummyOk("")
        if cmd[-2:] == ["set","region"]:
            return DummyOk("")
        if cmd[-1] == "disconnect":
            return DummyOk("")
        return DummyOk("")
    monkeypatch.setattr("subprocess.run", runner)
    monkeypatch.setattr("shutil.which", lambda exe: "/usr/bin/piactl")
    with pytest.raises(PiaConnectTimeout):
        connect_with_strategy(strategy="exact", exact_region="ca-ontario", max_retries=0)

def test_disconnect(fake_piactl_path, piactl_ok):
    piactl_ok(("/usr/bin/piactl","disconnect"), stdout="")
    disconnect_vpn()  # should not raise
