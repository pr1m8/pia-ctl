"""Bootstrap helpers for :mod:`pypia_ctl` `.env` + settings workflow.

Purpose:
    Provide a single explicit entry point to optionally create/merge `.env`
    (non-destructive) and then load :class:`~pypia_ctl.config.PiaSettings`.

Rules:
    - No implicit writes: you must pass ``create_env=True`` to write files.
    - Precedence remains: OS env > .env > code defaults.

Functions:
    init_settings: Optionally ensure `.env`, then return loaded settings.

Examples:
    ::
        >>> from pypia_ctl.bootstrap import init_settings
        >>> s = init_settings(create_env=False)  # doctest: +SKIP
        >>> # s.protocol, s.default_region, etc.
"""

from __future__ import annotations
from pathlib import Path

from .config import PiaSettings
from .envtools import ensure_env_file, DEFAULT_ENV_PATH


def init_settings(*, create_env: bool = False, env_path: str | Path = DEFAULT_ENV_PATH) -> PiaSettings:
    """Optionally create/merge a `.env`, then return loaded settings.

    Args:
        create_env: If True, create/merge `.env` before loading settings.
        env_path: Path to `.env`.

    Returns:
        A freshly loaded :class:`PiaSettings`.
    """
    if create_env:
        ensure_env_file(env_path)
    return PiaSettings()
