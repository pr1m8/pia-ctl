from __future__ import annotations

import contextlib
import os
from pathlib import Path
import sys
import types
import pytest

from pypia_ctl.plugins import Plugin, load_plugins


@contextlib.contextmanager
def chdir(p: Path):
    prev = Path.cwd()
    os.chdir(p)
    try:
        yield
    finally:
        os.chdir(prev)


def _install_dummy(mod_path: str, class_name: str, base: type[Plugin]) -> None:
    pkg_name = mod_path.split(".", 1)[0]
    sys.modules.setdefault(pkg_name, types.ModuleType(pkg_name))
    mod = types.ModuleType(mod_path)

    class Dummy(base):  # type: ignore[misc]
        def __init__(self) -> None:
            self.ok = True

    setattr(mod, class_name, Dummy)
    sys.modules[mod_path] = mod


def test_load_plugins_success_from_env(tmp_path: Path):
    _install_dummy("dummy.mod", "MyPlugin", Plugin)
    (tmp_path / ".env").write_text('PIA_PLUGINS=["dummy.mod:MyPlugin"]\n', encoding="utf-8")
    with chdir(tmp_path):
        plugs = load_plugins()  # reads from PiaSettings().plugins
    assert len(plugs) == 1 and isinstance(plugs[0], Plugin) and plugs[0].ok is True


def test_load_plugins_with_paths_explicit():
    # Uses explicit list, no .env required
    _install_dummy("d2.m", "C", Plugin)
    plugs = load_plugins(paths=["d2.m:C"])
    assert len(plugs) == 1 and isinstance(plugs[0], Plugin)


def test_load_plugins_bad_path_raises():
    with pytest.raises(Exception):
        _ = load_plugins(paths=["notapkg.notamod:Missing"])


def test_load_plugins_ignore_errors_partial():
    _install_dummy("good.m", "G", Plugin)
    plugs = load_plugins(paths=["good.m:G", "x.y:Z"], ignore_errors=True)
    assert len(plugs) == 1 and isinstance(plugs[0], Plugin)
