import pytest
from pypia_ctl.adapters import httpx_proxy, playwright_proxy, selenium_proxy
from pypia_ctl.config import PiaSettings

def test_httpx_proxy_ok(monkeypatch):
    s = PiaSettings()
    s.proxy.host = "example.com"
    s.proxy.port = 1080
    proxies = httpx_proxy(s)
    assert "http://" in proxies and "https://" in proxies

def test_playwright_proxy_includes_auth_when_present():
    s = PiaSettings()
    s.proxy.host = "example.com"; s.proxy.port = 1080
    s.proxy.username = "u"; s.proxy.password = "p"
    d = playwright_proxy(s)
    assert d["server"].startswith("socks5://u:p@")

def test_selenium_proxy_adds_arg(monkeypatch):
    s = PiaSettings()
    s.proxy.host = "example.com"; s.proxy.port = 1080
    class Opts:
        def __init__(self): self.args = []
        def add_argument(self, a): self.args.append(a)
    o = Opts()
    selenium_proxy(o, s)
    assert any("--proxy-server=" in a for a in o.args)

def test_proxy_missing_host_raises():
    s = PiaSettings()
    s.proxy.host = None; s.proxy.port = None
    with pytest.raises(ValueError):
        httpx_proxy(s)
