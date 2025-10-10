"""Private Internet Access (PIA) CLI Mini-SDK — :mod:`pypia_ctl`.

Purpose:
    A compact, typed wrapper around the official :mod:`piactl` command for
    Python apps that need to *programmatically* control PIA and wire that state
    into HTTP/browser clients (Playwright, httpx, Selenium) via a tiny plugin
    system.

Design:
    * **No hidden caching**: every call shells `piactl`.
    * **Pure I/O boundary**: we only execute the CLI you’d run by hand.
    * **Pydantic v2** settings**:** one place for `.env` & defaults.
    * **Plugins** (optional): hooks you can trigger around connect/disconnect
      or regular status sampling; included adapters produce proxy configs.

Public API:
    - :class:`~pypia_ctl.config.PiaSettings`
    - :class:`~pypia_ctl.core.PiaStatus`
    - :class:`~pypia_ctl.core.MonitorEvent`
    - :func:`~pypia_ctl.core.fetch_status`
    - :func:`~pypia_ctl.core.connect_with_strategy`
    - :func:`~pypia_ctl.core.disconnect_vpn`
    - :func:`~pypia_ctl.core.get_regions`
    - :func:`~pypia_ctl.core.monitor`
    - :class:`~pypia_ctl.plugins.Plugin`
    - :func:`~pypia_ctl.plugins.load_plugins`
    - Proxy helpers in :mod:`pypia_ctl.adapters`:
      :func:`~pypia_ctl.adapters.playwright_proxy`,
      :func:`~pypia_ctl.adapters.httpx_proxy`,
      :func:`~pypia_ctl.adapters.selenium_proxy`.

Examples:
    ::
        >>> from pypia_ctl import PiaSettings, fetch_status
        >>> s = PiaSettings()  # loads PIA_* envs from .env automatically
        >>> # st = fetch_status()  # doctest: +SKIP
        >>> # st.connection_state in {"Connected", "Disconnected"}  # doctest: +SKIP
        True
"""

from .config import PiaSettings
from .core import (
    PiaStatus,
    MonitorEvent,
    fetch_status,
    connect_with_strategy,
    disconnect_vpn,
    get_regions,
    monitor,
)
from .plugins import Plugin, load_plugins
from . import adapters

__all__ = [
    "PiaSettings",
    "PiaStatus",
    "MonitorEvent",
    "fetch_status",
    "connect_with_strategy",
    "disconnect_vpn",
    "get_regions",
    "monitor",
    "Plugin",
    "load_plugins",
    "adapters",
]
