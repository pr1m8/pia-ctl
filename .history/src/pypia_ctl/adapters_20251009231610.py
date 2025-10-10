"""Proxy adapters for Playwright, httpx, and Selenium.

Purpose:
    While :mod:`pypia_ctl` manages the PIA VPN/CLI state, *sometimes* you want
    per-client proxy routing instead of (or in addition to) a VPN tunnel.
    These helpers *do not* configure the VPN; they build **proxy configs** using
    the preferences in :class:`~pypia_ctl.config.PiaSettings`.

Security & Scope:
    - We only return config dicts / args you pass to each library.
    - If your PIA plan exposes SOCKS5 creds, put them in ``.env`` as
      ``PIA_PROXY_*``. This module won’t store or print secrets.

Examples:
    ::
        >>> from pypia_ctl import adapters, PiaSettings
        >>> s = PiaSettings()  # doctest: +SKIP
        >>> # Playwright:
        >>> # pw_proxy = adapters.playwright_proxy(s)  # doctest: +SKIP
        >>> # browser = pw.chromium.launch(proxy=pw_proxy)  # doctest: +SKIP

        >>> # httpx:
        >>> # proxies = adapters.httpx_proxy(s)  # doctest: +SKIP
        >>> # client = httpx.Client(proxies=proxies)  # doctest: +SKIP

        >>> # Selenium:
        >>> # from selenium.webdriver import ChromeOptions
        >>> # opts = ChromeOptions()
        >>> # adapters.selenium_proxy(opts, s)  # modifies options  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any
from .config import PiaSettings


def _auth_segment(username: str | None, password: str | None) -> str:
    if username and password:
        return f"{username}:{password}@"
    if username and not password:
        return f"{username}@"
    return ""


def _proxy_url(s: PiaSettings) -> str:
    """Return a full proxy URL like ``socks5://user:pass@host:port``."""
    kind = s.proxy.kind.lower()
    if not (s.proxy.host and s.proxy.port):
        raise ValueError("Proxy host/port not configured (see PIA_PROXY_HOST/PORT).")
    auth = _auth_segment(s.proxy.username, s.proxy.password)
    return f"{kind}://{auth}{s.proxy.host}:{s.proxy.port}"


# ---- Playwright -------------------------------------------------------------

def playwright_proxy(s: PiaSettings | None = None) -> dict[str, Any]:
    """Build a Playwright ``proxy=`` dict.

    Args:
        s: Optional settings. Defaults to :class:`PiaSettings()`.

    Returns:
        Dict suitable for ``chromium.launch(proxy=...)`` or per-context.

    Examples:
        ::
            >>> True
            True
    """
    s = s or PiaSettings()
    url = _proxy_url(s)
    out: dict[str, Any] = {"server": url}
    if s.proxy.username:
        out["username"] = s.proxy.username
    if s.proxy.password:
        out["password"] = s.proxy.password
    return out


# ---- httpx ------------------------------------------------------------------

def httpx_proxy(s: PiaSettings | None = None) -> dict[str, str]:
    """Build an ``httpx.Client(proxies=...)`` mapping.

    Args:
        s: Optional settings. Defaults to :class:`PiaSettings()`.

    Returns:
        Dict mapping scheme to proxy URL (both ``http`` and ``https``).

    Examples:
        ::
            >>> True
            True
    """
    s = s or PiaSettings()
    url = _proxy_url(s)
    return {"http://": url, "https://": url}


# ---- Selenium ---------------------------------------------------------------

def selenium_proxy(options: Any, s: PiaSettings | None = None) -> Any:
    """Mutate Selenium ``Options`` to add proxy arguments.

    Args:
        options: A WebDriver *Options* object (e.g., ``ChromeOptions``).
        s: Optional settings. Defaults to :class:`PiaSettings()`.

    Returns:
        The same options object (mutated in place).

    Notes:
        For Chrome-family drivers we inject ``--proxy-server=<url>``.
        For username/password, Selenium often requires using a *proxy auth
        extension* or a driver-level auth dialog; many headless environments
        prefer **no auth** proxies or pre-configured credentials.

    Examples:
        ::
            >>> True
            True
    """
    s = s or PiaSettings()
    url = _proxy_url(s)
    # Chrome / Edge style:
    if hasattr(options, "add_argument"):
        options.add_argument(f"--proxy-server={url}")
    return options
