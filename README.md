# pia-ctl-sdk

[![PyPI - Version](https://img.shields.io/pypi/v/pia-ctl-sdk.svg)](https://pypi.org/project/pia-ctl-sdk/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pia-ctl-sdk.svg)](https://pypi.org/project/pia-ctl-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python - Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![CI - Release](https://github.com/pr1m8/pia-ctl/actions/workflows/release.yml/badge.svg)](https://github.com/pr1m8/pia-ctl/actions/workflows/release.yml)
[![Code Style - Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checking - mypy](https://img.shields.io/badge/types-mypy-2A6DB2.svg)](http://mypy-lang.org/)
[![Docs - GitHub Pages](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://pr1m8.github.io/pia-ctl/)

A **typed Python SDK** for the Private Internet Access (PIA) VPN CLI (`piactl`) with comprehensive environment management, proxy adapters, and automation capabilities.

## 🚀 Features

- **🔒 VPN Management**: Connect, disconnect, and monitor PIA VPN connections
- **⚙️ Environment Configuration**: Pydantic v2 settings with `.env` file support
- **🌐 Proxy Adapters**: Built-in support for Playwright, httpx, and Selenium
- **📊 Status Monitoring**: Real-time VPN status and connection monitoring
- **🎯 Smart Connection**: Strategy-based connection (preferred → random → default regions)
- **🔌 Plugin System**: Extensible plugin architecture for custom functionality
- **🛠️ CLI Tools**: Command-line interface for VPN management
- **📝 Type Safety**: Full type hints and mypy support

## 📦 Installation

```bash
pip install pia-ctl-sdk
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/pr1m8/pia-ctl.git
cd pia-ctl

# Install with PDM
pdm install -G docs -G dev

# Or install with pip
pip install -e ".[dev,docs]"
```

## 🚀 Quick Start

### Basic Python Usage

```python
from pypia_ctl import init_settings, connect_vpn, get_status

# Initialize with environment settings
settings = init_settings(create_env=True)

# Connect to VPN with preferred region
result = connect_vpn(region="us-east")
print(f"Connected: {result.success}")

# Check VPN status
status = get_status()
print(f"VPN Status: {status.connected}")
print(f"Current Region: {status.region}")
print(f"IP Address: {status.ip_address}")
```

### Advanced Python Examples

```python
from pypia_ctl import PiaSettings, connect_with_strategy, monitor_connection
import asyncio

# Custom settings
settings = PiaSettings(
    protocol="wireguard",
    default_region="auto",
    preferred_regions=["us-east", "us-west", "europe"],
    randomize_region=True
)

# Connect with fallback strategy
result = connect_with_strategy(
    preferred=["us-east", "us-west"],
    fallback="random",
    timeout=30
)

# Async monitoring
async def monitor_vpn():
    async for status in monitor_connection():
        print(f"Status: {status.connected} - Region: {status.region}")
        if not status.connected:
            print("VPN disconnected, attempting reconnection...")
            connect_vpn()

# Run monitoring
asyncio.run(monitor_vpn())
```

### Proxy Integration Examples

```python
from pypia_ctl import PiaSettings
from pypia_ctl.adapters import PlaywrightAdapter, HttpxAdapter
import httpx
from playwright.async_api import async_playwright

# Configure proxy settings
settings = PiaSettings(
    proxy={
        "kind": "socks5",
        "host": "127.0.0.1",
        "port": 1080,
        "username": "user",
        "password": "pass"
    }
)

# Use with httpx
async with HttpxAdapter(settings) as client:
    response = await client.get("https://httpbin.org/ip")
    print(f"IP: {response.json()['origin']}")

# Use with Playwright
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()

    # Configure proxy
    await page.context.set_extra_http_headers({
        "Proxy-Authorization": "Basic dXNlcjpwYXNz"
    })

    await page.goto("https://httpbin.org/ip")
    content = await page.content()
    print("Page loaded with proxy")
```

### CLI Usage

```bash
# Initialize environment configuration
pypia env-init

# Connect to VPN with specific region
pypia connect --region us-east

# Connect with fallback strategy
pypia connect --preferred us-east,us-west --fallback random

# Check detailed status
pypia status --verbose

# Monitor connection in real-time
pypia monitor

# Disconnect
pypia disconnect

# List available regions
pypia regions

# Print environment configuration
pypia env-print
```

### Environment Configuration

Create a `.env` file with your preferences:

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
PIA_PROTOCOL=wireguard
PIA_DEFAULT_REGION=auto
PIA_RANDOMIZE_REGION=true
PIA_PREFERRED_REGIONS=["us-east", "us-west", "europe"]
```

## 📖 API Reference

### Core Functions

```python
from pypia_ctl import (
    init_settings,           # Initialize settings from env/.env
    connect_vpn,            # Connect to VPN
    disconnect_vpn,         # Disconnect VPN
    get_status,             # Get current VPN status
    connect_with_strategy,  # Connect with fallback strategy
    monitor_connection,     # Async connection monitoring
    ensure_env_file,        # Create/merge .env file
    generate_env_text,      # Generate .env content
)

# Settings and Configuration
from pypia_ctl import PiaSettings, EnvStatus

# Adapters for proxy integration
from pypia_ctl.adapters import PlaywrightAdapter, HttpxAdapter, SeleniumAdapter

# Exceptions
from pypia_ctl.exceptions import PiaError, ConnectionError, TimeoutError
```

### Settings Configuration

```python
from pypia_ctl import PiaSettings

# Full configuration example
settings = PiaSettings(
    # VPN Protocol
    protocol="wireguard",  # or "openvpn"

    # Region Settings
    default_region="auto",
    randomize_region=True,
    preferred_regions=["us-east", "us-west", "europe"],

    # Region Filtering
    region_filters={
        "include_streaming": False,
        "include_countries": ["US", "CA", "GB"],
        "exclude_countries": ["CN", "RU"]
    },

    # Proxy Configuration
    proxy={
        "kind": "socks5",
        "host": "127.0.0.1",
        "port": 1080,
        "username": "user",
        "password": "pass"
    },

    # Plugin Configuration
    plugins=["custom_plugin", "monitoring_plugin"]
)
```

## 🎯 Use Cases

### 1. Web Scraping with VPN

```python
from pypia_ctl import connect_vpn, HttpxAdapter
import httpx

# Connect to VPN
connect_vpn(region="us-east")

# Use with httpx for web scraping
async with HttpxAdapter() as client:
    response = await client.get("https://example.com")
    print(f"Scraped content: {response.text[:100]}...")
```

### 2. Automated Testing with Playwright

```python
from pypia_ctl import connect_vpn
from playwright.async_api import async_playwright

# Connect to VPN before testing
connect_vpn(region="europe")

async def test_with_vpn():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Test from different geographic location
        await page.goto("https://httpbin.org/ip")
        ip_info = await page.text_content("body")
        print(f"Testing from IP: {ip_info}")

        await browser.close()

# Run test
import asyncio
asyncio.run(test_with_vpn())
```

### 3. CI/CD Pipeline Integration

```yaml
# .github/workflows/test-with-vpn.yml
name: Test with VPN
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: pip install pia-ctl-sdk

      - name: Connect to VPN and test
        run: |
          pypia connect --region us-east
          python -m pytest tests/
          pypia disconnect
```

### 4. Monitoring and Alerting

```python
import asyncio
from pypia_ctl import monitor_connection, connect_vpn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def vpn_monitor():
    """Monitor VPN connection and auto-reconnect if needed."""
    async for status in monitor_connection():
        if not status.connected:
            logger.warning("VPN disconnected! Attempting reconnection...")
            try:
                connect_vpn()
                logger.info("VPN reconnected successfully")
            except Exception as e:
                logger.error(f"Failed to reconnect VPN: {e}")
        else:
            logger.info(f"VPN connected: {status.region} ({status.ip_address})")

# Run monitoring
asyncio.run(vpn_monitor())
```

## 🔧 Troubleshooting

### Common Issues

#### 1. VPN Connection Fails

```python
from pypia_ctl import connect_vpn, get_status
from pypia_ctl.exceptions import ConnectionError

try:
    result = connect_vpn(region="us-east")
    if not result.success:
        print(f"Connection failed: {result.error}")

        # Try alternative region
        result = connect_vpn(region="us-west")

except ConnectionError as e:
    print(f"Connection error: {e}")

    # Check if piactl is installed
    status = get_status()
    if not status.piactl_available:
        print("piactl not found. Please install PIA client.")
```

#### 2. Environment Configuration Issues

```python
from pypia_ctl import ensure_env_file, generate_env_text

# Create .env file with defaults
ensure_env_file(".env")

# Check generated configuration
env_content = generate_env_text()
print("Generated .env content:")
print(env_content)
```

#### 3. Proxy Configuration Problems

```python
from pypia_ctl import PiaSettings, HttpxAdapter

# Test proxy configuration
settings = PiaSettings(
    proxy={
        "kind": "socks5",
        "host": "127.0.0.1",
        "port": 1080
    }
)

try:
    async with HttpxAdapter(settings) as client:
        response = await client.get("https://httpbin.org/ip")
        print(f"Proxy working: {response.json()}")
except Exception as e:
    print(f"Proxy error: {e}")
```

## 📚 Documentation

### Local Development

```bash
# Serve documentation locally
pdm run docs

# Or with mkdocs directly
mkdocs serve
```

### Online Documentation

- **GitHub Pages**: [https://pr1m8.github.io/pia-ctl/](https://pr1m8.github.io/pia-ctl/)
- **API Reference**: Available in the docs
- **Examples**: See the `examples/` directory in the repository

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/pr1m8/pia-ctl.git
cd pia-ctl

# Install development dependencies
pdm install -G dev -G docs -G test

# Run tests
pdm run test

# Run linting
pdm run lint

# Run type checking
pdm run typecheck
```

### Building Documentation

```bash
# MkDocs (recommended)
pdm run docs

# Sphinx (alternative)
pip install sphinx furo myst-parser
(cd sphinx-docs && make html)
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**William R. Astley** ([@pr1m8](https://github.com/pr1m8))

- GitHub: [https://github.com/pr1m8](https://github.com/pr1m8)
- Email: william.astley@algebraicwealth.com

## 🔗 Links

- **Repository**: [https://github.com/pr1m8/pia-ctl](https://github.com/pr1m8/pia-ctl)
- **PyPI Package**: [https://pypi.org/project/pia-ctl-sdk/](https://pypi.org/project/pia-ctl-sdk/)
- **Issues**: [https://github.com/pr1m8/pia-ctl/issues](https://github.com/pr1m8/pia-ctl/issues)
- **Documentation**: [https://pr1m8.github.io/pia-ctl/](https://pr1m8.github.io/pia-ctl/)

## ⭐ Support

If you find this project helpful, please consider giving it a star on GitHub!
