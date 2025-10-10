"""Bootstrap helpers for :mod:`pypia_ctl` `.env` handling.

Purpose:
    Give callers one explicit entry point to:
      - optionally create/merge a `.env` (non-destructive),
      - then build a typed :class:`~pypia_ctl.config.PiaSettings`.

Design:
    - No implicit writes; you must opt in with `create_env=True`.
    - If you skip `.env`, you still get fully-typed defaults from `PiaSettings()`.
    - Precedence remains standard: OS env vars > .env > defaults.

Examples:
    ::
        >>> from pypia_ctl.bootstrap import init_settings
        >>> s = init_settings(create_env=False)  # no file writes
        >>> isinstance(s.protocol, str)
        True
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from .config import PiaSettings
from .envtools import ensure_env_file, DEFAULT_ENV_PATH

def init_settings(*, create_env: bool = False, env_path: str | Path = DEFAULT_ENV_PATH) -> PiaSettings:
    """Optionally create/merge a `.env`, then return loaded settings.

    Args:
        create_env: If True, create `.env` (or append missing keys) at `env_path`.
        env_path: Filesystem path to the `.env` file.

    Returns:
        A freshly loaded :class:`PiaSettings` instance.

    Examples:
        ::
            >>> # 1) Pure defaults (no .env file writes):
            >>> s = init_settings(create_env=False)  # doctest: +SKIP
            >>> # 2) Ensure `.env` exists and contains all PIA_* keys:
            >>> s2 = init_settings(create_env=True)  # doctest: +SKIP
    """
    if create_env:
        ensure_env_file(env_path)
    return PiaSettings()
