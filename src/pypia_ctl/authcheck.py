"""
Auth/Env checks for :mod:`pypia_ctl`.

Purpose:
    Provide a small, testable utility to:
      1) detect a local ``.env``,
      2) load :class:`~pypia_ctl.config.PiaSettings`,
      3) check for proxy credentials,
      4) optionally verify proxy auth by performing a probe HTTP request.

Design:
    - Pure helper functions with clear pre-/post-conditions.
    - No hidden network calls unless explicitly requested by the caller.
    - Uses ``httpx`` when `probe=True` is requested; otherwise no I/O.

Attributes:
    DEFAULT_PROBE_URL (str): Default endpoint used for probe requests (IP echo).

Examples:
    ::
        >>> from pypia_ctl.authcheck import has_proxy_creds
        >>> from pypia_ctl.config import PiaSettings
        >>> s = PiaSettings()  # relies on environment/.env
        >>> isinstance(has_proxy_creds(s), bool)
        True
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pypia_ctl.config import PiaSettings

DEFAULT_PROBE_URL: Final[str] = "https://ipinfo.io/ip"


@dataclass(frozen=True, slots=True)
class EnvStatus:
    """Snapshot of environment/auth readiness.

    Args:
        env_path: Path to the ``.env`` that was detected (if any).
        has_env: True if a ``.env`` file exists at or above CWD (passed-in path).
        has_proxy_host_port: True if both host and port are present.
        has_proxy_creds: True if username and password are present.
        probe_ok: True if the optional probe succeeded (only set when a probe ran).
        detail: Optional short textual reason when probe fails or preconditions unmet.

    Examples:
        ::
            >>> EnvStatus(env_path=None, has_env=False, has_proxy_host_port=False,
            ...           has_proxy_creds=False, probe_ok=None, detail=None)
            EnvStatus(env_path=None, has_env=False, has_proxy_host_port=False, has_proxy_creds=False, probe_ok=None, detail=None)
    """

    env_path: Path | None
    has_env: bool
    has_proxy_host_port: bool
    has_proxy_creds: bool
    probe_ok: bool | None
    detail: str | None


def find_env(start: Path | None = None) -> Path | None:
    """Search upward from ``start`` (or CWD) for a ``.env`` file.

    Args:
        start: Directory to start from; defaults to ``Path.cwd()``.

    Returns:
        Path | None: First ``.env`` found walking up to filesystem root.

    Examples:
        ::
            >>> isinstance(find_env(Path.cwd()), (Path, type(None)))
            True
    """
    cur = (start or Path.cwd()).resolve()
    root = cur.anchor
    while True:
        candidate = cur / ".env"
        if candidate.exists():
            return candidate
        if str(cur) == root:
            return None
        cur = cur.parent


def has_proxy_creds(settings: PiaSettings) -> bool:
    """Return True if proxy username & password are both configured.

    Args:
        settings: Loaded :class:`~pypia_ctl.config.PiaSettings`.

    Returns:
        bool: True when both ``settings.proxy.username`` and ``settings.proxy.password`` are truthy.

    Examples:
        ::
            >>> from pypia_ctl.config import PiaSettings
            >>> s = PiaSettings()
            >>> isinstance(has_proxy_creds(s), bool)
            True
    """
    return bool(settings.proxy.username and settings.proxy.password)


def has_proxy_host_port(settings: PiaSettings) -> bool:
    """Return True if proxy host & port are both configured.

    Args:
        settings: Loaded :class:`~pypia_ctl.config.PiaSettings`.

    Returns:
        bool: True when both host and port are truthy.

    Examples:
        ::
            >>> from pypia_ctl.config import PiaSettings
            >>> s = PiaSettings()
            >>> isinstance(has_proxy_host_port(s), bool)
            True
    """
    return bool(settings.proxy.host and settings.proxy.port)


def status(
    probe: bool = False,
    probe_url: str = DEFAULT_PROBE_URL,
) -> EnvStatus:
    """Compute environment/auth readiness and optionally probe via the proxy.

    Behavior:
        - Always inspects for a `.env` (via :func:`find_env`) and loads
          :class:`~pypia_ctl.config.PiaSettings`.
        - Reports whether proxy host/port and username/password are present.
        - If ``probe=True`` and host/port exist, performs a simple GET to
          ``probe_url`` through the configured proxy.
        - Allows tests to inject a fake ``httpx`` client by setting
          ``pypia_ctl.authcheck.httpx`` (a module global).

    Args:
        probe: When True, make a probe request through the configured proxy.
        probe_url: URL to fetch when probing.

    Returns:
        EnvStatus: Snapshot of `.env` presence, proxy config, and probe result.

    Raises:
        RuntimeError: If ``probe=True`` and a suitable ``httpx`` module is not available.

    Examples:
        ::
            >>> st = status(probe=False)
            >>> isinstance(st, EnvStatus)
            True
    """
    env_path = find_env()
    has_env = env_path is not None

    settings = PiaSettings()
    has_hp = has_proxy_host_port(settings)
    has_creds = has_proxy_creds(settings)

    # If no probe requested, just report static status.
    if not probe:
        return EnvStatus(
            env_path=env_path,
            has_env=has_env,
            has_proxy_host_port=has_hp,
            has_proxy_creds=has_creds,
            probe_ok=None,
            detail=None,
        )

    # Probe requested but we lack host/port.
    if not has_hp:
        return EnvStatus(
            env_path=env_path,
            has_env=has_env,
            has_proxy_host_port=has_hp,
            has_proxy_creds=has_creds,
            probe_ok=False,
            detail="Missing proxy host/port",
        )

    # Allow test-time injection: if `httpx` exists in module globals, use it.
    mod_httpx = globals().get("httpx")
    if mod_httpx is None:
        try:
            import httpx as mod_httpx  # type: ignore[no-redef]
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("httpx is required for probe=True") from exc

    # Build proxy URLs.
    scheme = settings.proxy.kind  # "http" or "socks5"
    user = settings.proxy.username or ""
    pwd = settings.proxy.password or ""
    auth = f"{user}:{pwd}@" if (user and pwd) else ""
    host = settings.proxy.host
    port = settings.proxy.port

    # httpx core understands http:// proxies; SOCKS often needs extra packages.
    # For a lightweight probe, we map both http/https to an HTTP proxy URL.
    # If `scheme == "http"`, we keep it; otherwise fallback to http:// mapping.
    base = (
        f"{scheme}://{auth}{host}:{port}"
        if scheme == "http"
        else f"http://{auth}{host}:{port}"
    )
    proxies = {"http://": base, "https://": base}

    try:
        with mod_httpx.Client(proxies=proxies, timeout=10) as c:
            resp = c.get(probe_url)
            ok = 200 <= resp.status_code < 400
            return EnvStatus(
                env_path=env_path,
                has_env=has_env,
                has_proxy_host_port=has_hp,
                has_proxy_creds=has_creds,
                probe_ok=ok,
                detail=None if ok else f"HTTP {resp.status_code}",
            )
    except Exception as exc:  # pragma: no cover
        return EnvStatus(
            env_path=env_path,
            has_env=has_env,
            has_proxy_host_port=has_hp,
            has_proxy_creds=has_creds,
            probe_ok=False,
            detail=str(exc),
        )
