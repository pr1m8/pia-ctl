import types
import pytest

class DummyCP:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

@pytest.fixture
def fake_piactl_path(monkeypatch):
    # Pretend piactl exists at /usr/bin/piactl
    monkeypatch.setattr("shutil.which", lambda exe: "/usr/bin/piactl" if exe == "piactl" else None)
    return "/usr/bin/piactl"

@pytest.fixture
def subprocess_run(monkeypatch):
    state = {"calls": []}
    def runner(cmd, capture_output=True, text=True, timeout=None):
        # By default return ok with empty output
        state["calls"].append((tuple(cmd), timeout))
        return DummyCP(stdout="")
    monkeypatch.setattr("subprocess.run", runner)
    return state

@pytest.fixture
def piactl_ok(monkeypatch, fake_piactl_path):
    # Helper to set subprocess.run to return specific outputs per command tuple
    registry = {}
    def set_reply(cmd_tuple, stdout="", stderr="", returncode=0):
        registry[tuple(cmd_tuple)] = DummyCP(stdout=stdout, stderr=stderr, returncode=returncode)
    def runner(cmd, capture_output=True, text=True, timeout=None):
        return registry.get(tuple(cmd), DummyCP(stdout=""))
    monkeypatch.setattr("subprocess.run", runner)
    return set_reply
