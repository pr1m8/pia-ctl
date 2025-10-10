"""Private Internet Access (PIA) CLI Mini-SDK — :mod:`pypia_ctl`.

Purpose:
    A compact, typed wrapper around the official :mod:`piactl` command for
    Python apps that need to programmatically control PIA and route that state
    into HTTP/browser clients. Provides:
      * Strict subprocess runner with **typed exceptions**.
      * Synchronous getters and **strategy connect** (preferred → random → default).
      * Async **monitor** for live updates.
      * :mod:`pydantic_settings`-backed configuration (env/.env/defaults).
      * Non-destructive **.env** helpers (create/merge/print).
      * (Optional) adapters for Playwright/httpx/Selenium proxy setup.
      * (Optional) tiny plugin protocol and loader.

Design:
    - Zero hidden caching; every call shells ``piactl``.
    - No network calls beyond invoking the PIA daemon via CLI.
    - Side effects only when calling mutators (``connect``, ``disconnect``, ``set``).

Public API:
    Config & bootstrap:
        - :class:`~pypia_ctl.config.PiaSettings`
        - :func:`~pypia_ctl.bootstrap.init_settings`
        - :func:`~pypia_ctl.envtools.ensure_env_file`
        - :func:`~pypia_ctl.envtools.generate_env_text`
    Core:
        - :class:`~pypia_ctl.core.PiaStatus`
        - :class:`~pypia_ctl.core.MonitorEvent`
        - :func:`~pypia_ctl.core.fetch_status`
        - :func:`~pypia_ctl.core.connect_with_strategy`
        - :func:`~pypia_ctl.core.disconnect_vpn`
        - :func:`~pypia_ctl.core.get_regions`
        - :func:`~pypia_ctl.core.monitor`
    Exceptions:
        - :class:`~pypia_ctl.exceptions.PiaCtlError`
        - :class:`~pypia_ctl.exceptions.PiaCtlNotFound`
        - :class:`~pypia_ctl.exceptions.PiaCtlInvocationFailed`
        - :class:`~pypia_ctl.exceptions.PiaConnectTimeout`
    Optional:
        - :mod:`pypia_ctl.adapters` (proxy helpers)
        - :class:`~pypia_ctl.plugins.Plugin`, :func:`~pypia_ctl.plugins.load_plugins`

Examples:
    ::
        >>> from pypia_ctl import init_settings, fetch_status
        >>> s = init_settings(create_env=False)  # no writes; OS env > .env > defaults
        >>> isinstance(s.protocol, str)
        True
"""

from .config import PiaSettings
from .bootstrap import init_settings
from .envtools import ensure_env_file, generate_env_text
from .core import (
    PiaStatus,
    MonitorEvent,
    fetch_status,
    connect_with_strategy,
    disconnect_vpn,
    get_regions,
    monitor,
)
from .exceptions import (
    PiaCtlError,
    PiaCtlNotFound,
    PiaCtlInvocationFailed,
    PiaConnectTimeout,
)
from . import adapters  # optional proxy helpers
from .plugins import Plugin, load_plugins  # optional plugin mechanism

__all__ = [
    # config / bootstrap / env
    "PiaSettings",
    "init_settings",
    "ensure_env_file",
    "generate_env_text",
    # core
    "PiaStatus",
    "MonitorEvent",
    "fetch_status",
    "connect_with_strategy",
    "disconnect_vpn",
    "get_regions",
    "monitor",
    # exceptions
    "PiaCtlError",
    "PiaCtlNotFound",
    "PiaCtlInvocationFailed",
    "PiaConnectTimeout",
    # optional
    "adapters",
    "Plugin",
    "load_plugins",
]
