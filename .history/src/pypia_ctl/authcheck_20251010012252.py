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


def status(probe: bool = False, probe_url: str = DEFAULT_PROBE_URL) -> EnvStatus:
    """Compute environment/auth readiness and optionally probe via the proxy.

    Args:
        probe: If True, perform a simple GET to ``probe_url`` via configured proxy.
        probe_url: URL to fetch when probing; defaults to a public IP echo.

    Returns:
        EnvStatus: A snapshot describing presence of ``.env``, proxy config, and probe result.

    Raises:
        RuntimeError: When ``probe=True`` but ``httpx`` is not installed.

    Examples:
        ::
            >>> st = status(probe=False)
            >>> isinstance(st, EnvStatus)
            True
    """
    env_path = find_env()
    has_env = env_path is not None
    s = PiaSettings()
    hp = has_proxy_host_port(s)
    hc = has_proxy_creds(s)

    if not probe:
        return EnvStatus(env_path=env_path, has_env=has_env,
                         has_proxy_host_port=hp, has_proxy_creds=hc,
                         probe_ok=None, detail=None)

    if not hp:
        return EnvStatus(env_path=env_path, has_env=has_env,
                         has_proxy_host_port=hp, has_proxy_creds=hc,
                         probe_ok=False, detail="Missing proxy host/port")

    try:
        import httpx  # runtime import to avoid hard dep when unused
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("httpx is required for probe=True") from exc

    scheme = s.proxy.kind
    auth = ""
    if s.proxy.username and s.proxy.password:
        auth = f"{s.proxy.username}:{s.proxy.password}@"
    server = f"{scheme}://{auth}{s.proxy.host}:{s.proxy.port}"

    proxies = {
        "http://": server if scheme == "http" else f"http://{auth}{s.proxy.host}:{s.proxy.port}",
        "https://": server if scheme == "http" else f"http://{auth}{s.proxy.host}:{s.proxy.port}",
    }

    try:
        with httpx.Client(proxies=proxies, timeout=10) as c:
            r = c.get(probe_url)
            ok = 200 <= r.status_code < 400
            return EnvStatus(env_path=env_path, has_env=has_env,
                             has_proxy_host_port=hp, has_proxy_creds=hc,
                             probe_ok=ok, detail=None if ok else f"HTTP {r.status_code}")
    except Exception as exc:  # pragma: no cover
        return EnvStatus(env_path=env_path, has_env=has_env,
                         has_proxy_host_port=hp, has_proxy_creds=hc,
                         probe_ok=False, detail=str(exc))
