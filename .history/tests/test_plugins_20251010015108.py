from __future__ import annotations

import contextlib
import os
from pathlib import Path
import sys
import types

from pypia_ctl.plugins import Plugin, load_plugins


@contextlib.contextmanager
def chdir(p: Path):
    prev = Path.cwd()
    os.chdir(p)
    try:
        yield
    finally:
        os.chdir(prev)


def _install_dummy_plugin(mod_path: str, class_name: str, base: type[Plugin]) -> None:
    pkg_name = mod_path.split(".", 1)[0]
    sys.modules.setdefault(pkg_name, types.ModuleType(pkg_name))
    mod = types.ModuleType(mod_path)

    class Dummy(base):  # type: ignore[misc]
        def __init__(self) -> None:
            self.ok = True

    setattr(mod, class_name, Dummy)
    sys.modules[mod_path] = mod


def test_load_plugins_success_from_env(tmp_path: Path):
    _install_dummy_plugin("dummy.mod", "MyPlugin", Plugin)

    (tmp_path / ".env").write_text('PIA_PLUGINS=["dummy.mod:MyPlugin"]\n', encoding="utf-8")

    with chdir(tmp_path):
        plugs = load_plugins()  # zero-arg API reads from settings/env
    assert len(plugs) == 1
    assert isinstance(plugs[0], Plugin)
    assert getattr(plugs[0], "ok", False) is True


def test_load_plugins_empty_env_returns_empty(tmp_path: Path):
    (tmp_path / ".env").write_text("PIA_PLUGINS=[]\n", encoding="utf-8")
    with chdir(tmp_path):
        plugs = load_plugins()
    assert plugs == []


def test_load_plugins_bad_path_raises(tmp_path: Path):
    (tmp_path / ".env").write_text('PIA_PLUGINS=["notapkg.notamod:Missing"]\n', encoding="utf-8")
    with chdir(tmp_path):
        try:
            _ = load_plugins()
        except Exception:
            pass
        else:
            raise AssertionError("expected an exception for bad plugin path")
