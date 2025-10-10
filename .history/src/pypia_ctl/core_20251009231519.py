"""Core `piactl` wrappers, models, region strategies, and monitor.

Purpose:
    Provide strict, typed helpers around the PIA CLI for status, connect/
    disconnect, region discovery, and real-time monitoring. All state is read
    from the daemon via `piactl`; no private APIs are used.

Design:
    - **Synchronous getters** (simple subprocess calls).
    - **Strategy connect**: preferred list → random fallback → default.
    - **Async monitor**: stream ``piactl monitor <key>`` lines.
    - **Typed models**: safe JSON logging via Pydantic v2.

Preconditions:
    - PIA app/daemon is installed and available on PATH as ``piactl``.
    - For headless, enable background mode once: ``piactl background enable``.

Examples:
    ::
        >>> from pypia_ctl.core import get_regions
        >>> # regs = get_regions()  # doctest: +SKIP
        >>> True
"""

from __future__ import annotations

import asyncio
import contextlib
import random
import shutil
import subprocess
from asyncio.subprocess import PIPE
from typing import Iterable, Literal, Optional

from pydantic import BaseModel, Field

from .config import PiaSettings

# ---------- Types & Models ---------------------------------------------------

ConnectionState = Literal[
    "Disconnected",
    "Connecting",
    "StillConnecting",
    "Connected",
    "Interrupted",
    "Reconnecting",
    "StillReconnecting",
    "DisconnectingToReconnect",
    "Disconnecting",
]
ProtocolT = Literal["openvpn", "wireguard"]
PortForwardState = Literal["Inactive", "Attempting", "Failed", "Unavailable"]


class PortForward(BaseModel):
    """Port forwarding status/value.

    Args:
        port: Forwarded port number if active.
        state: Non-port status when no port is present.
    """
    port: Optional[int] = None
    state: Optional[PortForwardState] = None


class PiaStatus(BaseModel):
    """Snapshot of PIA state (JSON-log friendly).

    Args:
        connection_state: Current state.
        region: Selected region slug (or ``"auto"``).
        regions: All known region slugs (plus ``"auto"``).
        vpn_ip: Current VPN IP string or ``None``.
        protocol: Selected protocol (if exposed by this build).
        debug_logging: Whether debug logging is enabled.
        port_forward: Port forward model.
        request_port_forward: Whether PF is requested (if exposed).
    """
    connection_state: ConnectionState
    region: str
    regions: list[str]
    vpn_ip: Optional[str]
    protocol: Optional[ProtocolT]
    debug_logging: bool
    port_forward: PortForward
    request_port_forward: Optional[bool]


class MonitorEvent(BaseModel):
    """One update line from ``piactl monitor <key>``.

    Args:
        key: The key monitored (e.g., ``"connectionstate"``).
        value: The text value emitted by the daemon.
    """
    key: str
    value: str


# ---------- Low-level runner -------------------------------------------------

def _piactl(*args: str, timeout: Optional[int] = None) -> str:
    """Invoke `piactl` and return stripped stdout.

    Args:
        *args: Arguments after `piactl`, e.g., ``("get", "region")``.
        timeout: Seconds to wait; defaults to settings.

    Returns:
        Command stdout (stripped).

    Raises:
        RuntimeError: When `piactl` is missing or returns non-zero.

    Examples:
        ::
            >>> isinstance("ok", str)
            True
    """
    settings = PiaSettings()
    exe = shutil.which("piactl")
    if not exe:
        raise RuntimeError("`piactl` not found on PATH.")
    to = timeout or settings.subprocess_timeout_sec
    try:
        cp = subprocess.run([exe, *args], capture_output=True, text=True, timeout=to)
    except Exception as e:  # TimeoutExpired, OSError, etc.
        raise RuntimeError(f"piactl failed: {e}") from e
    if cp.returncode != 0:
        err = (cp.stderr or cp.stdout or "").strip() or "unknown error"
        raise RuntimeError(f"piactl error: {err}")
    return (cp.stdout or "").strip()


# ---------- Getters ----------------------------------------------------------

def get_connection_state() -> ConnectionState:
    return _piactl("get", "connectionstate")  # type: ignore[return-value]


def get_debug_logging() -> bool:
    return _piactl("get", "debuglogging").lower().startswith("t")


def get_region() -> str:
    return _piactl("get", "region")


def get_regions() -> list[str]:
    out = _piactl("get", "regions")
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def get_vpn_ip() -> Optional[str]:
    val = _piactl("get", "vpnip")
    return None if val.lower() == "unknown" else val


def get_protocol() -> Optional[ProtocolT]:
    try:
        v = _piactl("get", "protocol").strip().lower()
        return v if v in ("openvpn", "wireguard") else None  # type: ignore[return-value]
    except RuntimeError:
        return None


def get_request_port_forward() -> Optional[bool]:
    try:
        return _piactl("get", "requestportforward").lower().startswith("t")
    except RuntimeError:
        return None


def get_port_forward() -> PortForward:
    raw = _piactl("get", "portforward")
    if raw.isdigit():
        return PortForward(port=int(raw), state=None)
    known = {"Inactive", "Attempting", "Failed", "Unavailable"}
    return PortForward(port=None, state=raw if raw in known else "Unavailable")  # type: ignore[arg-type]


def fetch_status() -> PiaStatus:
    """Return a one-shot status snapshot by querying multiple getters.

    Returns:
        A :class:`PiaStatus` ready for logs/health checks.

    Examples:
        ::
            >>> True
            True
    """
    return PiaStatus(
        connection_state=get_connection_state(),
        region=get_region(),
        regions=get_regions(),
        vpn_ip=get_vpn_ip(),
        protocol=get_protocol(),
        debug_logging=get_debug_logging(),
        port_forward=get_port_forward(),
        request_port_forward=get_request_port_forward(),
    )


# ---------- Region filtering & strategies -----------------------------------

def _filter_regions(all_regions: list[str], s: PiaSettings) -> list[str]:
    """Apply include/exclude filters and streaming flag."""
    regs = [r for r in all_regions if r]
    if not s.region_filters.include_streaming:
        regs = [r for r in regs if "-streaming-optimized" not in r]
    if s.region_filters.include_countries:
        pref = tuple(s.region_filters.include_countries)
        regs = [r for r in regs if r.startswith(pref)]
    if s.region_filters.exclude_countries:
        pref = tuple(s.region_filters.exclude_countries)
        regs = [r for r in regs if not r.startswith(pref)]
    if "auto" in regs:
        regs = ["auto"] + [r for r in regs if r != "auto"]
    return regs


def _choose_region(strategy: Literal["preferred", "random", "exact"],
                   exact: Optional[str],
                   s: PiaSettings) -> str:
    regs = _filter_regions(get_regions(), s)
    if strategy == "exact":
        return exact or s.default_region
    if strategy == "preferred":
        for r in s.preferred_regions:
            if r in regs:
                return r
    if s.randomize_region:
        pool = [r for r in regs if r != "auto"] or regs
        return random.choice(pool)
    return s.default_region if s.default_region in regs else (regs[0] if regs else "auto")


# ---------- Mutating helpers -------------------------------------------------

def _set_protocol(proto: ProtocolT) -> None:
    _piactl("set", "protocol", proto)


def _set_region(region: str) -> None:
    _piactl("set", "region", region)


def connect_with_strategy(
    *,
    strategy: Literal["preferred", "random", "exact"] = "preferred",
    exact_region: Optional[str] = None,
    max_retries: int = 2,
) -> None:
    """Connect using settings + strategy, with simple retries.

    Args:
        strategy: Region selection approach.
        exact_region: When ``strategy="exact"``, use this slug.
        max_retries: Reconnect attempts on failure.

    Raises:
        RuntimeError: On failure after retries.

    Examples:
        ::
            >>> True
            True
    """
    s = PiaSettings()
    _set_protocol(s.protocol)
    region = _choose_region(strategy, exact_region, s)
    _set_region(region)

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            _piactl("connect")
            # lightweight polling for Connected
            for _ in range(20):
                if get_connection_state() == "Connected":
                    return
                asyncio.run(asyncio.sleep(0.25))
            raise RuntimeError("Timed out waiting for Connected state")
        except Exception as e:  # noqa: BLE001
            last_err = e
            with contextlib.suppress(Exception):
                _piactl("disconnect")
            if attempt < max_retries:
                continue
            raise RuntimeError(f"PIA connect failed: {last_err}") from last_err


def disconnect_vpn() -> None:
    """Disconnect the VPN (best effort)."""
    _piactl("disconnect")


# ---------- Monitor (async) --------------------------------------------------

async def monitor(key: str) -> Iterable[MonitorEvent]:
    """Yield :class:`MonitorEvent` for live updates via ``piactl monitor <key>``.

    Args:
        key: e.g., ``"connectionstate"`` or ``"vpnip"``.

    Yields:
        :class:`MonitorEvent` values as lines arrive.

    Examples:
        ::
            >>> True
            True
    """
    settings = PiaSettings()
    exe = shutil.which("piactl")
    if not exe:
        raise RuntimeError("`piactl` not found on PATH.")

    proc = await asyncio.create_subprocess_exec(exe, "monitor", key, stdout=PIPE, stderr=PIPE)
    try:
        while True:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=settings.monitor_line_timeout_sec)  # type: ignore[arg-type]
            if not line:
                break
            text = line.decode("utf-8", "ignore").strip()
            if ":" in text:
                k, v = text.split(":", 1)
                yield MonitorEvent(key=k.strip(), value=v.strip())
            else:
                yield MonitorEvent(key=key, value=text)
    finally:
        with contextlib.suppress(Exception):
            proc.kill()
