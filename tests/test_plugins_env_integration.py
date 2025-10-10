from __future__ import annotations

import contextlib
import os
from pathlib import Path
import sys
import types

from pypia_ctl.plugins import Plugin, load_plugins
from pypia_ctl.config import PiaSettings


@contextlib.contextmanager
def chdir(p: Path):
    prev = Path.cwd()
    os.chdir(p)
    try:
        yield
    finally:
        os.chdir(prev)


def test_plugins_list_from_env_and_load(tmp_path: Path):
    sys.modules.setdefault("pkg", types.ModuleType("pkg"))
    mod = types.ModuleType("pkg.mod")

    class Plug(Plugin):  # type: ignore[misc]
        def __init__(self) -> None:
            self.tag = "ok"

    mod.Plug = Plug
    sys.modules["pkg.mod"] = mod

    (tmp_path / ".env").write_text('PIA_PLUGINS=["pkg.mod:Plug"]\n', encoding="utf-8")

    with chdir(tmp_path):
        s = PiaSettings()
        assert s.plugins == ["pkg.mod:Plug"]
        plugs = load_plugins()  # zero-arg path via settings
    assert len(plugs) == 1 and getattr(plugs[0], "tag", "") == "ok"
