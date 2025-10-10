"""Utilities for managing a local ``.env`` file.

Purpose:
    Generate sensible defaults and non-destructively merge them into a ``.env``.

Design:
    - Append missing keys; never overwrite existing ones.
    - Keep behavior minimal and explicit.

Examples:
    ::
        >>> from pathlib import Path
        >>> from pypia_ctl.envtools import generate_env_text, ensure_env_file
        >>> txt = generate_env_text()
        >>> "PIA_PROTOCOL" in txt
        True
"""

from __future__ import annotations

from pathlib import Path


DEFAULT_ENV_LINES: tuple[str, ...] = (
    "PIA_PROTOCOL=wireguard",
    "PIA_DEFAULT_REGION=auto",
    "PIA_RANDOMIZE_REGION=true",
    "PIA_PREFERRED_REGIONS=",
    # region filters (CSV lists)
    "PIA_REGION_FILTERS__include_streaming=false",
    "PIA_REGION_FILTERS__include_countries=",
    "PIA_REGION_FILTERS__exclude_countries=",
    # proxy
    "PIA_PROXY__KIND=socks5",
    "PIA_PROXY__HOST=",
    "PIA_PROXY__PORT=",
    "PIA_PROXY__USERNAME=",
    "PIA_PROXY__PASSWORD=",
    # plugins (CSV of fully-qualified classes)
    "PIA_PLUGINS=",
)


def generate_env_text() -> str:
    """Return suggested ``.env`` text with defaults.

    Returns:
        str: Newline-terminated string suitable for writing to disk.

    Examples:
        ::
            >>> txt = generate_env_text()
            >>> txt.endswith("\\n")
            True
    """
    return "\n".join(DEFAULT_ENV_LINES) + "\n"


def ensure_env_file(path: str | Path) -> None:
    """Create or merge a ``.env`` file without overwriting existing keys.

    Args:
        path: Destination path for the ``.env`` file.

    Returns:
        None

    Examples:
        ::
            >>> from pathlib import Path
            >>> p = Path("._example.env")
            >>> try:
            ...     ensure_env_file(p)
            ...     p.exists()
            ... finally:
            ...     p.unlink(missing_ok=True)
            True
    """
    p = Path(path)
    existing: dict[str, str] = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            k, _sep, v = line.partition("=")
            existing[k.strip()] = v

    to_add: list[str] = []
    for line in DEFAULT_ENV_LINES:
        key, _sep, value = line.partition("=")
        if key not in existing:
            to_add.append(f"{key}={value}")

    if not p.exists():
        p.write_text(generate_env_text(), encoding="utf-8")
        return

    if to_add:
        with p.open("a", encoding="utf-8") as f:
            f.write("\n".join(to_add) + "\n")
