"""Typer CLI for `pypia_ctl` env + status workflow."""
from __future__ import annotations
import asyncio
import typer
from .envtools import ensure_env_file, generate_env_text
from .core import fetch_status, connect_with_strategy, disconnect_vpn, monitor

app = typer.Typer(no_args_is_help=True)

@app.command("env-init")
def env_init(path: str = ".env"):
    """Create or merge `.env` with PIA_* defaults (non-destructive)."""
    ensure_env_file(path)
    typer.echo(f"Wrote/updated {path}")

@app.command("env-print")
def env_print():
    """Print suggested .env content from current defaults."""
    typer.echo(generate_env_text())

@app.command("status")
def status():
    """Print one-shot status as JSON."""
    st = fetch_status()
    typer.echo(st.model_dump_json(indent=2))

@app.command("connect")
def connect(strategy: str = "preferred", exact_region: str | None = None, retries: int = 2):
    """Connect using strategy (preferred|random|exact)."""
    connect_with_strategy(strategy=strategy, exact_region=exact_region, max_retries=retries)
    typer.echo("Connected.")

@app.command("disconnect")
def disconnect():
    """Disconnect VPN."""
    disconnect_vpn()
    typer.echo("Disconnected.")

@app.command("monitor")
def monitor_key(key: str = "connectionstate"):
    """Stream `piactl monitor <key>` updates."""
    async def _run():
        async for ev in monitor(key):
            typer.echo(f"{ev.key}: {ev.value}")
    asyncio.run(_run())

def main():
    app()

if __name__ == "__main__":
    main()
