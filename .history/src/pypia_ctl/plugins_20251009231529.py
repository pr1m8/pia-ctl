"""Plugin interface & loader for :mod:`pypia_ctl`.

Purpose:
    Provide an ultra-light “hook” system so apps can register side effects
    around connect/disconnect or regular status sampling (e.g., logging,
    metrics, policy enforcement, per-worker routing plans).

Protocol:
    Implement any subset of:
        - on_connect(status: PiaStatus) -> None
        - on_disconnect(status: PiaStatus) -> None
        - on_status(status: PiaStatus) -> None

Discovery:
    Read from env var ``PIA_PLUGINS`` as a comma-separated list of fully-
    qualified class paths. Each class must be constructible with ``()``.

Examples:
    ::
        # .env
        # PIA_PLUGINS=my_pkg.plugins.LogPlugin

        >>> from pypia_ctl import load_plugins, fetch_status
        >>> # ps = load_plugins()  # doctest: +SKIP
        >>> True
"""

from __future__ import annotations

import importlib
from typing import Protocol

from .config import PiaSettings
from .core import PiaStatus


class Plugin(Protocol):
    """Plugin protocol for PIA lifecycle hooks.

    Implement any subset of:
        - on_connect(status: PiaStatus) -> None
        - on_disconnect(status: PiaStatus) -> None
        - on_status(status: PiaStatus) -> None
    """


def load_plugins() -> list[Plugin]:
    """Instantiate plugins declared in ``PIA_PLUGINS``.

    Returns:
        A list of plugin instances (may be empty).

    Examples:
        ::
            >>> True
            True
    """
    s = PiaSettings()
    out: list[Plugin] = []
    for path in s.plugins:
        try:
            mod_name, cls_name = path.rsplit(".", 1)
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            out.append(cls())  # type: ignore[misc]
        except Exception:
            # Soft-fail: skip bad plugins but keep running.
            continue
    return out
