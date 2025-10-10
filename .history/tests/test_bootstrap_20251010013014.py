from pathlib import Path
import os
import contextlib

from pypia_ctl.bootstrap import init_settings


@contextlib.contextmanager
def chdir(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def test_init_settings_pure(tmp_path: Path):
    with chdir(tmp_path):
        s = init_settings(create_env=False)
    assert s.default_region == "auto"


def test_init_settings_creates_env(tmp_path: Path):
    p = tmp_path / ".env"
    assert not p.exists()
    with chdir(tmp_path):
        _ = init_settings(create_env=True, env_path=".env")
    assert p.exists()
    txt = p.read_text(encoding="utf-8")
    assert "PIA_PROTOCOL=" in txt


def test_init_settings_overrides(tmp_path: Path):
    with chdir(tmp_path):
        s = init_settings(create_env=False, overrides={"protocol": "openvpn"})
    assert s.protocol == "openvpn"
