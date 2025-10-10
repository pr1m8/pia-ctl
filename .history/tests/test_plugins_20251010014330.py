# tests/test_plugins.py
from __future__ import annotations
import sys, types
import pytest

def test_load_plugins_success(monkeypatch):
    from pypia_ctl.plugins import Plugin, load_plugins

    mod = types.ModuleType("dummy.mod")

    class MyPlugin(Plugin):  # type: ignore[misc]
        """Minimal plugin for testing."""
        def __init__(self) -> None:
            self.ok = True

    mod.MyPlugin = MyPlugin
    pkg = types.ModuleType("dummy")
    sys.modules["dummy"] = pkg
    sys.modules["dummy.mod"] = mod

    plugs = load_plugins(["dummy.mod:MyPlugin"])
    assert len(plugs) == 1
    assert isinstance(plugs[0], Plugin)
    assert getattr(plugs[0], "ok", False) is True
