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

### Basic Usage

```python
from pypia_ctl import init_settings, connect_vpn

# Initialize with environment settings
settings = init_settings(create_env=True)

# Connect to VPN with preferred region
result = connect_vpn(region="us-east")
print(f"Connected: {result.success}")
```

### CLI Usage

```bash
# Initialize environment configuration
pypia env-init

# Connect to VPN
pypia connect --region us-east

# Check status
pypia status

# Disconnect
pypia disconnect
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
