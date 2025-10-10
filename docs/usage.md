# Usage

## CLI

```bash
pdm run pypia env-init
pdm run pypia env-print
pdm run pypia status
pdm run pypia connect --strategy preferred
pdm run pypia disconnect
pdm run pypia monitor --key connectionstate
```

## Python

```python
from pypia_ctl import init_settings, fetch_status, connect_with_strategy

s = init_settings(create_env=False)
st = fetch_status()
connect_with_strategy()
```

## .env keys (JSON for lists)

```env
PIA_PROTOCOL=wireguard
PIA_DEFAULT_REGION=auto
PIA_PREFERRED_REGIONS=["us-new-york","ca-ontario"]
PIA_RANDOMIZE_REGION=true
PIA_PROXY__KIND=socks5
PIA_PROXY__HOST=localhost
PIA_PROXY__PORT=1080
PIA_PROXY__USERNAME=
PIA_PROXY__PASSWORD=
PIA_PLUGINS=["pkg.mod:Class"]
```
