"""
Plugin protocol and loader for :mod:`pypia_ctl`.

Purpose:
    Allow optional extension points discovered via env settings or passed-in
    paths. A "plugin" is just a class that subclasses :class:`Plugin`. Paths
    are specified as ``"pkg.module:ClassName"``.

Design:
    - No network calls. Pure importlib/dynamic loading.
    - Default behavior reads from :class:`~pypia_ctl.config.PiaSettings`.plugins.
    - Explicit paths parameter overrides env-driven discovery.
    - Raises on bad entries by default; can be made forgiving via ``ignore_errors``.

Examples:
    ::
        >>> from pypia_ctl.plugins import Plugin, load_plugins
        >>> class MyPlug(Plugin): pass
        >>> # Dynamically load a known path
        >>> plugs = load_plugins(paths=["pypia_ctl.plugins:Plugin"], ignore_errors=True)
        >>> isinstance(plugs, list)
        True
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Iterable, List, Sequence


class Plugin:
    """Base class for plugins.

    Notes:
        Subclass this, provide your behavior in __init__/methods, and ensure the
        class can be instantiated without required parameters.
    """
    pass


@dataclass(slots=True, frozen=True)
class PluginSpec:
    """Parsed form of a ``pkg.module:ClassName`` path."""
    module: str
    class_name: str


def _parse_path(p: str) -> PluginSpec:
    if ":" not in p:
        raise ValueError(f"Invalid plugin path (missing ':'): {p!r}")
    mod, cls = p.split(":", 1)
    mod = mod.strip()
    cls = cls.strip()
    if not mod or not cls:
        raise ValueError(f"Invalid plugin path: {p!r}")
    return PluginSpec(module=mod, class_name=cls)


def _instantiate(spec: PluginSpec) -> Plugin:
    mod = importlib.import_module(spec.module)
    try:
        cls = getattr(mod, spec.class_name)
    except AttributeError as exc:
        raise ImportError(f"{spec.class_name!r} not in module {spec.module!r}") from exc
    if not issubclass(cls, Plugin):  # type: ignore[arg-type]
        raise TypeError(f"{spec.module}:{spec.class_name} is not a Plugin subclass")
    return cls()  # type: ignore[call-arg]


def _discover_from_env() -> Sequence[str]:
    # Lazy import to avoid pydantic dependency unless used
    from pypia_ctl.config import PiaSettings
    s = PiaSettings()
    return s.plugins


def load_plugins(
    paths: Iterable[str] | None = None,
    *,
    ignore_errors: bool = False,
) -> List[Plugin]:
    """Load and instantiate plugins.

    Args:
        paths: Iterable of ``"pkg.module:ClassName"`` entries. If ``None``,
            discovery uses :class:`~pypia_ctl.config.PiaSettings`.plugins.
        ignore_errors: If True, skip invalid entries; otherwise raise.

    Returns:
        list[Plugin]: Instantiated plugins (possibly empty).

    Raises:
        ValueError, ImportError, TypeError: When an entry is invalid (and
        ``ignore_errors`` is False).

    Examples:
        ::
            >>> load_plugins(paths=[], ignore_errors=True)
            []
    """
    specs: list[PluginSpec] = []
    entries = list(paths) if paths is not None else list(_discover_from_env())

    for p in entries:
        try:
            specs.append(_parse_path(p))
        except Exception:
            if ignore_errors:
                continue
            raise

    out: list[Plugin] = []
    for spec in specs:
        try:
            out.append(_instantiate(spec))
        except Exception:
            if ignore_errors:
                continue
            raise
    return out
