from __future__ import annotations

from pathlib import Path
import contextlib
import os

import pytest

from pypia_ctl.config import PiaSettings


@contextlib.contextmanager
def chdir(path: Path):
    """Temporarily chdir for the duration of the context."""
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def test_defaults_load_without_env(tmp_path: Path):
    with chdir(tmp_path):
        s = PiaSettings()
    assert s.protocol == "wireguard"
    assert s.default_region == "auto"
    assert s.proxy.kind in {"socks5", "http"}


def test_nested_proxy_env(tmp_path: Path):
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
    assert s.proxy.host == "localhost"
    assert s.proxy.port == 1080
    assert s.proxy.username == "alice"
    assert s.proxy.password == "secret"


def test_json_lists_parse(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        'PIA_PREFERRED_REGIONS=["us-new-york","ca-ontario"]\n'
        'PIA_PLUGINS=["a.b:Cls","c.d:Cls2"]\n'
        'PIA_REGION_FILTERS__include_countries=["us-","ca-"]\n'
        'PIA_REGION_FILTERS__exclude_countries=["cn-","ru-"]\n',
        encoding="utf-8",
    )
    with chdir(tmp_path):
        s = PiaSettings()
    assert s.preferred_regions == ["us-new-york", "ca-ontario"]
    assert s.plugins == ["a.b:Cls", "c.d:Cls2"]
    assert s.region_filters.include_countries == ["us-", "ca-"]
    assert s.region_filters.exclude_countries == ["cn-", "ru-"]


def test_port_validation():
    with pytest.raises(ValueError):
        PiaSettings(proxy={"port": 70000})
