# src/pypia_ctl/cli.py
"""Typer CLI for :mod:`pypia_ctl`.

Purpose:
    Provide a compact command-line interface for common ``piactl`` flows:
    environment bootstrapping, one-shot status, connect/disconnect, and
    streaming monitor updates.

Design:
    - Single Typer app with small, composable subcommands.
    - Strict typing, Google-style docstrings, doctestable examples.
    - Defensive error handling with non-zero exit codes on failures.
    - No hidden network calls beyond the underlying library behavior.

Attributes:
    app (typer.Typer): The Typer application instance.

Examples:
    ::
        >>> # One-shot status (JSON)
        >>> # $ pypia status
        ...
        >>> # Connect with default strategy
        >>> # $ pypia connect
        ...
        >>> # Stream connection state updates
        >>> # $ pypia monitor --key connectionstate
        ...
"""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Literal

import typer

from .core import connect_with_strategy, disconnect_vpn, fetch_status, monitor
from .envtools import ensure_env_file, generate_env_text

__all__ = ["app", "main"]

app: typer.Typer = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")

Strategy = Literal["preferred", "random", "exact"]


def _echo_json(data: object) -> None:
    """Print an object as pretty JSON to stdout.

    Args:
        data: Any JSON-serializable structure.

    Returns:
        None

    Examples:
        ::
            >>> _echo_json({"ok": True})  # doctest: +SKIP
    """
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))


@app.command("env-init")
def env_init(
    path: Annotated[str, typer.Option(help="Path to write/merge .env (non-destructive).")] = ".env",
) -> None:
    """Create or merge a ``.env`` file with sensible PIA defaults.

    Args:
        path: Target file path; created if missing, keys merged if present.

    Returns:
        None

    Raises:
        typer.Exit: With code 1 on failure.

    Examples:
        ::
            >>> # $ pypia env-init --path .env
            ...
    """
    try:
        ensure_env_file(path)
        typer.echo(f"Wrote/updated {path}")
    except Exception as exc:  # pragma: no cover
        typer.echo(f"env-init failed: {exc}", err=True)
        raise typer.Exit(1)


@app.command("env-print")
def env_print() -> None:
    """Print suggested ``.env`` content based on current defaults.

    Returns:
        None

    Examples:
        ::
            >>> # $ pypia env-print
            ...
    """
    typer.echo(generate_env_text())


@app.command("status")
def status_cmd() -> None:
    """Print a one-shot status snapshot as JSON.

    Returns:
        None

    Raises:
        typer.Exit: With code 1 on failure.

    Examples:
        ::
            >>> # $ pypia status
            ...
    """
    try:
        st = fetch_status()
        _echo_json(st.model_dump())
    except Exception as exc:  # pragma: no cover
        typer.echo(f"status failed: {exc}", err=True)
        raise typer.Exit(1)


@app.command("connect")
def connect(
    strategy: Annotated[
        Strategy, typer.Option(help="Connection strategy: preferred | random | exact")
    ] = "preferred",
    exact_region: Annotated[
        str | None, typer.Option(help="Region slug when strategy=exact (e.g., ca-ontario).")]
    = None,
    retries: Annotated[int, typer.Option(min=0, help="Max retries for connect workflow.")] = 2,
) -> None:
    """Connect to PIA using the requested strategy.

    Args:
        strategy: Strategy name (``preferred``, ``random``, or ``exact``).
        exact_region: Required when strategy is ``exact``.
        retries: Number of allowed retries on failure paths.

    Returns:
        None

    Raises:
        typer.Exit: With code 2 if ``exact`` without ``--exact-region``; code 1 on other failures.

    Examples:
        ::
            >>> # $ pypia connect --strategy preferred
            ...
    """
    try:
        if strategy == "exact" and not exact_region:
            typer.echo("exact strategy requires --exact-region", err=True)
            raise typer.Exit(2)
        connect_with_strategy(strategy=strategy, exact_region=exact_region, max_retries=retries)
        typer.echo("Connected.")
    except Exception as exc:  # pragma: no cover
        typer.echo(f"connect failed: {exc}", err=True)
        raise typer.Exit(1)


@app.command("disconnect")
def disconnect() -> None:
    """Disconnect PIA.

    Returns:
        None

    Raises:
        typer.Exit: With code 1 on failure.

    Examples:
        ::
            >>> # $ pypia disconnect
            ...
    """
    try:
        disconnect_vpn()
        typer.echo("Disconnected.")
    except Exception as exc:  # pragma: no cover
        typer.echo(f"disconnect failed: {exc}", err=True)
        raise typer.Exit(1)


@app.command("monitor")
def monitor_key(
    key: Annotated[str, typer.Option(help="Key to stream from `piactl monitor <key>`.")] = "connectionstate",
) -> None:
    """Stream ``piactl monitor <key>`` updates continuously.

    Args:
        key: Monitor key, e.g., ``connectionstate`` or ``region``.

    Returns:
        None

    Raises:
        typer.Exit: With code 130 on Ctrl-C; code 1 on other failures.

    Examples:
        ::
            >>> # $ pypia monitor --key connectionstate
            ...
    """
    async def _run() -> int:
        try:
            async for ev in monitor(key):
                typer.echo(f"{ev.key}: {ev.value}")
            return 0
        except asyncio.CancelledError:  # pragma: no cover
            return 130
        except Exception as exc:  # pragma: no cover
            typer.echo(f"monitor failed: {exc}", err=True)
            return 1

    try:
        code = asyncio.run(_run())
        raise typer.Exit(code)
    except KeyboardInterrupt:  # pragma: no cover
        raise typer.Exit(130)


def main() -> None:
    """Entrypoint for console-script ``pypia``.

    Returns:
        None

    Examples:
        ::
            >>> # This is invoked by the installed console script entry point.
            >>> # $ pypia --help
            ...
    """
    app()
