# pypia_ctl

Typed mini-SDK around the official `piactl` CLI (Private Internet Access).  
Use it to **inspect status**, **connect/disconnect** via strategies, **stream monitor
events**, manage **`.env`** defaults, and **wire the PIA proxy** into `httpx`,
Playwright, and Selenium — with a tiny **plugin** system on top.

[![Docs](https://img.shields.io/badge/docs-mkdocs%20material-blue)](./)
[![CI Docs](https://github.com/your-org/pia_ctl/actions/workflows/docs.yml/badge.svg)](https://github.com/your-org/pia_ctl/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)

---

## Why pypia_ctl?

- 🔒 **Safe subprocess wrapper** over `piactl` with typed exceptions
- ⚙️ **Pydantic v2 settings** (env/.env/defaults) — OS env > `.env` > defaults
- 🧠 **Strategy connect** (preferred → random → exact) with retries
- 📡 **Live monitor**: async stream of `piactl monitor <key>` events
- 🧰 **Adapters** for `httpx`, Playwright, Selenium proxying
- 🔌 **Plugins**: load custom hooks via simple `module:Class` paths
- 🧾 **CLI** (Typer): `env-init`, `env-print`, `status`, `connect`, `disconnect`, `monitor`

---

## Requirements

- Python **3.13**
- PIA desktop/daemon + **`piactl`** available on PATH
- macOS/Linux (Windows WSL works if `piactl` is available)

!!! tip
    Not sure if `piactl` is on PATH?  
    ```bash
    which piactl && piactl --version
    ```

---

## Install

Choose your tool:

=== "PDM"
```bash
pdm add pypia-ctl
```

=== "pip"
```bash
python -m pip install pypia-ctl
```

For docs/development:
```bash
pdm add -G docs mkdocs mkdocs-material 'mkdocstrings[python]' \
  mkdocs-gen-files mkdocs-literate-nav mkdocs-section-index mkdocs-include-markdown-plugin
```

---

## Quick start

1) Create defaults:
```bash
pdm run pypia env-init
# writes/merges a .env (non-destructive)
```

2) Inspect current status:
```bash
pdm run pypia status
```

3) Connect using the preferred strategy (tries your preferred list first, then random):
```bash
pdm run pypia connect --strategy preferred
```

4) Stream live monitor updates:
```bash
pdm run pypia monitor --key connectionstate
```

See full command docs in **[CLI](./cli.md)**.

---

## Minimal Python usage

```python
from pypia_ctl import init_settings, fetch_status, connect_with_strategy

# Load settings: OS env > .env > defaults (no writes)
settings = init_settings(create_env=False)

status = fetch_status()
print(status.connection_state)

connect_with_strategy(strategy="preferred", max_retries=2)
```

More walkthroughs in **[Usage](./usage.md)**.

---

## Settings overview

Settings are read from:
1. OS environment (highest precedence)
2. `.env` (middle)
3. Built-in defaults (fallback)

Key environment variables (lists are **JSON arrays**):

| Key | Example |
|---|---|
| `PIA_PROTOCOL` | `wireguard` |
| `PIA_DEFAULT_REGION` | `auto` |
| `PIA_PREFERRED_REGIONS` | `["us-new-york","ca-ontario"]` |
| `PIA_RANDOMIZE_REGION` | `true` |
| `PIA_PROXY__KIND` | `socks5` |
| `PIA_PROXY__HOST` | `localhost` |
| `PIA_PROXY__PORT` | `1080` |
| `PIA_PROXY__USERNAME` / `PIA_PROXY__PASSWORD` | `""` |
| `PIA_PLUGINS` | `["pkg.mod:Hook"]` |
| `PIA_REGION_FILTERS__include_countries` | `["us-","ca-"]` |
| `PIA_REGION_FILTERS__exclude_countries` | `["cn-","ru-"]` |

!!! example ".env template"
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

    PIA_PLUGINS=[]
    PIA_REGION_FILTERS__include_countries=["us-","ca-"]
    PIA_REGION_FILTERS__exclude_countries=[]
    ```

Full schema in **[API](./api.md)**.

---

## Adapters (proxy wiring)

Wire PIA’s proxy into common clients:

=== "httpx"
```python
from pypia_ctl.adapters import httpx_proxy
import httpx

proxies = httpx_proxy()  # respects PIA_PROXY__* settings
with httpx.Client(proxies=proxies, timeout=10) as client:
    r = client.get("https://ipinfo.io/ip")
    print(r.text)
```

=== "Playwright"
```python
from pypia_ctl.adapters import playwright_proxy
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(proxy=playwright_proxy())
    page = browser.new_page()
    page.goto("https://ipinfo.io/ip")
    print(page.text_content("body"))
```

=== "Selenium"
```python
from pypia_ctl.adapters import selenium_proxy
from selenium import webdriver

options = webdriver.ChromeOptions()
selenium_proxy(options)  # mutates options to add proxy
driver = webdriver.Chrome(options=options)
driver.get("https://ipinfo.io/ip")
print(driver.page_source)
driver.quit()
```

Details & caveats in **[Adapters](./adapters.md)**.

---

## Strategy connect

- **preferred**: Try `PIA_PREFERRED_REGIONS` in order. If none available, optionally fall back to random (based on settings).
- **random**: Pick a random eligible region (respecting include/exclude filters).
- **exact**: Connect to exactly the given region slug.

```bash
# exact requires a region slug
pdm run pypia connect --strategy exact --exact-region ca-ontario
```

---

## Plugins

Load custom hooks with a minimal protocol (e.g., observability, extra validation, toggling app behavior).

- Configure as JSON list in `.env`:
  ```env
  PIA_PLUGINS=["pkg.mod:MyPlugin"]
  ```
- The loader imports and instantiates each class at runtime.

See examples in **[API](./api.md)** and test fixtures for reference.

---

## Troubleshooting

!!! note "mkdocs can't import my package"
    Add to `mkdocs.yml`:
    ```yaml
    plugins:
      - mkdocstrings:
          handlers:
            python:
              paths: [src]
    ```
    Or run with `PYTHONPATH=src`.

!!! warning "`piactl` not found"
    Ensure PIA is installed and `piactl` is on PATH:
    ```bash
    which piactl
    piactl --version
    ```

!!! tip "JSON lists in `.env`"
    Use JSON arrays, not CSV. Example:
    ```
    PIA_PREFERRED_REGIONS=["us-new-york","ca-ontario"]
    ```

More errors and fixes in **[Errors](./errors.md)**.

---

## Architecture (high-level)

```
+-------------------+       +--------------------+       +--------------------+
|  Typer CLI (app)  | --->  |   Core (runner)    | --->  |  piactl (daemon)   |
+-------------------+       +--------------------+       +--------------------+
          |                          |
          v                          v
+-------------------+       +--------------------+
|  Env/Settings     |       |  Adapters (proxy)  |
|  (Pydantic v2)    |       |  httpx/PLW/Sel     |
+-------------------+       +--------------------+
          |
          v
+-------------------+
|  Plugins (loader) |
+-------------------+
```

---

## Roadmap

- Optional telemetry hooks via plugin
- Better cross-platform region selectors
- Rich TUI monitor

Contributions welcome — see **CONTRIBUTING.md**.

---

## Publishing to PyPI (quick checklist)

1. Update `pyproject.toml` (name, version, description, classifiers).
2. Build:
   ```bash
   pdm build
   ```
3. Upload (use TestPyPI first):
   ```bash
   pdm publish --repository testpypi
   # then:
   pdm publish
   ```
4. Tag & release on GitHub; CI can build docs from `main`.

---

## Links

- **Usage**: [usage.md](./usage.md)  
- **CLI**: [cli.md](./cli.md)  
- **Adapters**: [adapters.md](./adapters.md)  
- **Errors**: [errors.md](./errors.md)  
- **API**: [api.md](./api.md)
