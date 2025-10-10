# CLI

The `pypia` Typer app exposes env + status + connect/monitor.

```bash
pdm run pypia --help
```

## Commands

- `env-init` — create/merge `.env` defaults (non-destructive)
- `env-print` — print suggested `.env` contents
- `status` — JSON snapshot of PIA status
- `connect` — strategy connect (preferred|random|exact)
- `disconnect` — disconnect VPN
- `monitor` — stream `piactl monitor <key>` updates

Source:

::: pypia_ctl.cli.app
    options:
      show_source: false
