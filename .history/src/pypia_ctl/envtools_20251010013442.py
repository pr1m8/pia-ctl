"""Utilities for managing a local ``.env`` file.

Purpose:
    Generate sensible defaults and non-destructively merge them into a ``.env``.
    Existing keys are preserved; only missing keys are appended.

Design:
    - Pure file I/O; no network calls.
    - Deterministic: stable order, newline-terminated file.
    - CSV-friendly keys for nested Pydantic settings via ``env_nested_delimiter="__"``.

Attributes:
    DEFAULT_ENV (tuple[str, ...]): Canonical default lines to seed/merge.

Examples:
    ::
        >>> from pathlib import Path
        >>> from pypia_ctl.envtools import generate_env_text, ensure_env_file, parse_env
        >>> txt = generate_env_text()
        >>> "PIA_PROTOCOL" in txt
        True
        >>> p = Path("._example.env")
        >>> try:
        ...     ensure_env_file(p)
        ...     d = parse_env(p)
        ...     d["PIA_DEFAULT_REGION"] == "auto"
        ... finally:
        ...     p.unlink(missing_ok=True)
        True
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple

# Canonical defaults; keep order stable for nicer diffs.
# src/pypia_ctl/envtools.py
DEFAULT_ENV: Tuple[str, ...] = (
    "PIA_PROTOCOL=wireguard",
    "PIA_DEFAULT_REGION=auto",
    "PIA_RANDOMIZE_REGION=true",
    # JSON arrays (pydantic-settings expects JSON for list fields)
    "PIA_PREFERRED_REGIONS=[]",
    "PIA_REGION_FILTERS__include_streaming=false",
    "PIA_REGION_FILTERS__include_countries=[]",
    "PIA_REGION_FILTERS__exclude_countries=[]",
    # Proxy
    "PIA_PROXY__KIND=socks5",
    "PIA_PROXY__HOST=",
    "PIA_PROXY__PORT=",
    "PIA_PROXY__USERNAME=",
    "PIA_PROXY__PASSWORD=",
    # Plugins as JSON array
    "PIA_PLUGINS=[]",
)


def generate_env_text(extra: Mapping[str, str] | None = None) -> str:
    """Return newline-terminated ``.env`` content.

    Args:
        extra: Optional mapping of additional key→value pairs to append.

    Returns:
        str: Content suitable to be written to disk.

    Examples:
        ::
            >>> txt = generate_env_text({"FOO": "bar"})
            >>> "FOO=bar" in txt
            True
    """
    lines: List[str] = list(DEFAULT_ENV)
    if extra:
        for k, v in extra.items():
            lines.append(f"{k}={v}")
    return "\n".join(lines) + "\n"


def ensure_env_file(path: str | Path, defaults: Iterable[str] | None = None) -> None:
    """Create or merge a ``.env`` file without overwriting existing keys.

    Behavior:
        - If the file does not exist, write defaults (plus trailing newline).
        - If it exists, append only missing keys (keep current values/comments).
        - Ignores comment/blank lines on read.

    Args:
        path: Destination path for the ``.env`` file.
        defaults: Optional custom defaults (lines like ``KEY=VALUE``). If
            omitted, :data:`DEFAULT_ENV` is used.

    Returns:
        None

    Raises:
        ValueError: If any provided default line lacks an ``=``.

    Examples:
        ::
            >>> from pathlib import Path
            >>> p = Path("._ensure.env")
            >>> try:
            ...     ensure_env_file(p)
            ...     ensure_env_file(p)  # idempotent
            ...     "PIA_PROTOCOL=" in p.read_text()
            ... finally:
            ...     p.unlink(missing_ok=True)
            True
    """
    p = Path(path)
    base: Tuple[str, ...] = tuple(defaults) if defaults is not None else DEFAULT_ENV

    # Validate input defaults early.
    for line in base:
        if "=" not in line:
            raise ValueError(f"invalid default line (missing '='): {line!r}")

    if not p.exists():
        p.write_text(generate_env_text(), encoding="utf-8")
        return

    existing = parse_env(p)
    to_add: List[str] = []
    for line in base:
        key, _, value = line.partition("=")
        if key not in existing:
            to_add.append(f"{key}={value}")

    if to_add:
        with p.open("a", encoding="utf-8") as f:
            f.write("\n".join(to_add) + "\n")


def parse_env(path: str | Path) -> Dict[str, str]:
    """Parse a simple ``.env`` into a dict of key→value.

    Notes:
        - Lines without ``=`` or starting with ``#`` are ignored.
        - No shell expansions; values are taken as-is.

    Args:
        path: File path to read.

    Returns:
        dict[str, str]: Parsed key→value mapping.

    Examples:
        ::
            >>> from pathlib import Path
            >>> p = Path("._parse.env")
            >>> _ = p.write_text("A=1\\n# comment\\nB=2\\n", encoding="utf-8")
            >>> try:
            ...     d = parse_env(p)
            ...     d == {"A": "1", "B": "2"}
            ... finally:
            ...     p.unlink(missing_ok=True)
            True
    """
    p = Path(path)
    data: Dict[str, str] = {}
    if not p.exists():
        return data
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v
    return data
