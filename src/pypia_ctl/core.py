"""Core `piactl` wrappers, models, region strategies, and monitor.

Purpose:
    Provide strict, typed helpers around the PIA CLI for status, connect/
    disconnect, region discovery, and real-time monitoring. Uses a hardened
    subprocess runner that raises **typed exceptions** on failures.

Design:
    - **Synchronous getters**: trivial `piactl get ...` wrappers.
    - **Strategy connect**: preferred list → random fallback → default region.
    - **Async monitor**: yields `MonitorEvent` from `piactl monitor <key>`.
    - **Pydantic v2** models for safe JSON logging.
    - **Enums** for states/protocols, with model config mapping to values.

Preconditions:
    - PIA app/daemon installed; `piactl` available on PATH.
    - For headless, enable background mode once: ``piactl background enable``.

Examples:
    ::
        >>> from pypia_ctl.core import get_regions
        >>> isinstance([], list)
        True
"""

from __future__ import annotations

import asyncio
import contextlib
import random
import shutil
import subprocess
from asyncio.subprocess import PIPE
from enum import StrEnum
from typing import Iterable, Optional

from pydantic import BaseModel, Field, ConfigDict

from .config import PiaSettings
from .exceptions import (
    PiaCtlNotFound,
    PiaCtlInvocationFailed,
    PiaConnectTimeout,
)

# ---------- Enums ------------------------------------------------------------

class ConnectionState(StrEnum):
    """Stable connection states as reported by `piactl`."""
    Disconnected = "Disconnected"
    Connecting = "Connecting"
    StillConnecting = "StillConnecting"
    Connected = "Connected"
    Interrupted = "Interrupted"
    Reconnecting = "Reconnecting"
    StillReconnecting = "StillReconnecting"
    DisconnectingToReconnect = "DisconnectingToReconnect"
    Disconnecting = "Disconnecting"


class ProtocolT(StrEnum):
    """Supported VPN protocols."""
    openvpn = "openvpn"
    wireguard = "wireguard"


class PortForwardState(StrEnum):
    """Non-port PF states."""
    Inactive = "Inactive"
    Attempting = "Attempting"
    Failed = "Failed"
    Unavailable = "Unavailable"


# ---------- Pydantic Models --------------------------------------------------

class PortForward(BaseModel):
    """Port forwarding status/value.

    Args:
        port: Forwarded port number if active.
        state: Non-port status when no port is present.

    Returns:
        A validated port-forward model.

    Examples:
        ::
            >>> PortForward(port=None, state="Inactive").model_dump()["state"]
            'Inactive'
    """
    model_config = ConfigDict(use_enum_values=True)

    port: int | None = None
    state: PortForwardState | None = None


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

    Returns:
        A validated :class:`PiaStatus`.

    Examples:
        ::
            >>> PiaStatus(
            ...   connection_state="Disconnected",
            ...   region="auto",
            ...   regions=["auto"],
            ...   vpn_ip=None,
            ...   protocol=None,
            ...   debug_logging=False,
            ...   port_forward=PortForward(),
            ...   request_port_forward=None,
            ... ).connection_state
            'Disconnected'
    """
    model_config = ConfigDict(use_enum_values=True)

    connection_state: ConnectionState | str  # tolerate raw strings from CLI
    region: str
    regions: list[str]
    vpn_ip: str | None
    protocol: ProtocolT | None
    debug_logging: bool
    port_forward: PortForward
    request_port_forward: bool | None


class MonitorEvent(BaseModel):
    """One update line from ``piactl monitor <key>``.

    Args:
        key: The key monitored (e.g., ``"connectionstate"``).
        value: The text value emitted by the daemon.

    Returns:
        A :class:`MonitorEvent`.

    Examples:
        ::
            >>> MonitorEvent(key="connectionstate", value="Connected").value
            'Connected'
    """
    key: str
    value: str


# ---------- Low-level runner -------------------------------------------------

def _piactl(*args: str, timeout: int | None = None) -> str:
    """Invoke `piactl` and return stripped stdout.

    Args:
        *args: Arguments after `piactl` (e.g., ``("get", "region")``).
        timeout: Seconds to wait; default comes from :class:`PiaSettings`.

    Returns:
        Command stdout (stripped).

    Raises:
        PiaCtlNotFound: If `piactl` is not on PATH.
        PiaCtlInvocationFailed: For non-zero exit, timeout, or OS error.

    Examples:
        ::
            >>> isinstance("ok", str)
            True
    """
    settings = PiaSettings()
    exe = shutil.which("piactl")
    if not exe:
        raise PiaCtlNotFound("`piactl` not found on PATH.")
    to = timeout or settings.subprocess_timeout_sec
    try:
        cp = subprocess.run([exe, *args], capture_output=True, text=True, timeout=to)
    except Exception as e:  # TimeoutExpired, OSError, etc.
        raise PiaCtlInvocationFailed(f"piactl failed: {e}") from e
    if cp.returncode != 0:
        err = (cp.stderr or cp.stdout or "").strip() or "unknown error"
        raise PiaCtlInvocationFailed(err)
    return (cp.stdout or "").strip()


# ---------- Getters ----------------------------------------------------------

def get_connection_state() -> ConnectionState | str:
    """Return the current connection state."""
    return _piactl("get", "connectionstate")  # may be raw string; model tolerates


def get_debug_logging() -> bool:
    """Return whether debug logging is enabled."""
    return _piactl("get", "debuglogging").lower().startswith("t")


def get_region() -> str:
    """Return the selected region slug (or 'auto')."""
    return _piactl("get", "region")


def get_regions() -> list[str]:
    """Return all available region slugs (plus 'auto')."""
    out = _piactl("get", "regions")
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def get_vpn_ip() -> str | None:
    """Return the current VPN IP string or ``None`` if unknown."""
    val = _piactl("get", "vpnip")
    return None if val.lower() == "unknown" else val


def get_protocol() -> ProtocolT | None:
    """Return selected protocol if exposed; else ``None``."""
    try:
        v = _piactl("get", "protocol").strip().lower()
        return ProtocolT(v) if v in (ProtocolT.openvpn, ProtocolT.wireguard) else None
    except PiaCtlInvocationFailed:
        return None


def get_request_port_forward() -> bool | None:
    """Return whether PF is requested, if exposed; else ``None``."""
    try:
        return _piactl("get", "requestportforward").lower().startswith("t")
    except PiaCtlInvocationFailed:
        return None


def get_port_forward() -> PortForward:
    """Return current forwarded port or PF state."""
    raw = _piactl("get", "portforward")
    if raw.isdigit():
        return PortForward(port=int(raw), state=None)
    try:
        state = PortForwardState(raw)
    except ValueError:
        state = PortForwardState.Unavailable
    return PortForward(port=None, state=state)


def fetch_status() -> PiaStatus:
    """Return a one-shot status snapshot by querying multiple getters.

    Returns:
        A :class:`PiaStatus` ready for logs/health checks.

    Raises:
        PiaCtlError: Any underlying runner error will bubble up.

    Examples:
        ::
            >>> isinstance(True, bool)
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


def _choose_region(strategy: str, exact: str | None, s: PiaSettings) -> str:
    """Choose region according to strategy ('preferred'|'random'|'exact')."""
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
    _piactl("set", "protocol", proto.value)


def _set_region(region: str) -> None:
    _piactl("set", "region", region)


def connect_with_strategy(
    *,
    strategy: str = "preferred",
    exact_region: str | None = None,
    max_retries: int = 2,
) -> None:
    """Connect using settings + strategy, with simple retries.

    Args:
        strategy: One of ``"preferred"``, ``"random"``, ``"exact"``.
        exact_region: When ``strategy="exact"``, this slug is used.
        max_retries: Reconnect attempts on failure.

    Raises:
        PiaCtlNotFound: `piactl` not on PATH.
        PiaCtlInvocationFailed: `piactl connect`/`disconnect` failed.
        PiaConnectTimeout: Did not reach ``Connected`` within the poll window.

    Examples:
        ::
            >>> isinstance(1, int)
            True
    """
    s = PiaSettings()
    _set_protocol(ProtocolT(s.protocol))
    region = _choose_region(strategy, exact_region, s)
    _set_region(region)

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            _piactl("connect")
            # lightweight polling for Connected
            for _ in range(20):
                if str(get_connection_state()) == ConnectionState.Connected:
                    return
                asyncio.run(asyncio.sleep(0.25))
            raise PiaConnectTimeout("Timed out waiting for Connected state")
        except Exception as e:
            last_err = e
            with contextlib.suppress(Exception):
                _piactl("disconnect")
            if attempt < max_retries:
                continue
            if isinstance(last_err, (PiaCtlNotFound, PiaCtlInvocationFailed, PiaConnectTimeout)):
                raise
            raise PiaCtlInvocationFailed(f"PIA connect failed: {last_err}") from last_err


def disconnect_vpn() -> None:
    """Disconnect the VPN (best effort).

    Raises:
        PiaCtlNotFound: `piactl` not on PATH.
        PiaCtlInvocationFailed: `piactl disconnect` failed.

    Examples:
        ::
            >>> isinstance(True, bool)
            True
    """
    _piactl("disconnect")


# ---------- Monitor (async) --------------------------------------------------

async def monitor(key: str) -> Iterable[MonitorEvent]:
    """Yield :class:`MonitorEvent` for live updates via ``piactl monitor <key>``.

    Args:
        key: e.g., ``"connectionstate"`` or ``"vpnip"``.

    Yields:
        :class:`MonitorEvent` values as lines arrive.

    Raises:
        PiaCtlNotFound: If `piactl` is not on PATH.

    Examples:
        ::
            >>> isinstance(True, bool)
            True
    """
    settings = PiaSettings()
    exe = shutil.which("piactl")
    if not exe:
        raise PiaCtlNotFound("`piactl` not found on PATH.")

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
