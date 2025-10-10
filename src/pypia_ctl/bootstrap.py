"""Bootstrap helpers for :mod:`pypia_ctl`.

Purpose:
    Provide a single entry point to initialize settings with optional
    non-destructive ``.env`` creation and on-the-fly overrides.

Design:
    - No side effects unless explicitly requested.
    - Delegates ``.env`` creation to :func:`pypia_ctl.envtools.ensure_env_file`.

Examples:
    ::
        >>> from pypia_ctl.bootstrap import init_settings
        >>> s = init_settings(create_env=False)  # pure load
        >>> s.default_region == "auto"
        True
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import PiaSettings
from .envtools import ensure_env_file


def init_settings(
    create_env: bool = False,
    env_path: str | None = ".env",
    overrides: dict[str, Any] | None = None,
) -> PiaSettings:
    """Initialize :class:`~pypia_ctl.config.PiaSettings`.

    Args:
        create_env: If True, ensure a ``.env`` exists (non-destructive merge).
        env_path: Path to the ``.env`` to create/merge (when ``create_env``).
        overrides: In-memory overrides to apply after loading from env/.env.

    Returns:
        PiaSettings: A loaded, optionally overridden settings object.

    Examples:
        ::
            >>> from pypia_ctl.bootstrap import init_settings
            >>> s = init_settings(create_env=False, overrides={"protocol": "openvpn"})
            >>> s.protocol
            'openvpn'
    """
    if create_env and env_path:
        ensure_env_file(Path(env_path))

    settings = PiaSettings()

    if overrides:
        # Build a new settings object using existing values plus overrides.
        data = settings.model_dump()
        data.update(overrides)
        settings = PiaSettings.model_validate(data)

    return settings
