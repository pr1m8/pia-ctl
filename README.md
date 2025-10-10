# pypia_ctl


[![PyPI - Version](https://img.shields.io/pypi/v/pypia-ctl.svg)](https://pypi.org/project/pypia-ctl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI - Lint](https://github.com/your-org/pypia_ctl/actions/workflows/lint.yml/badge.svg)](https://github.com/your-org/pypia_ctl/actions/workflows/lint.yml)
[![CI - Tests](https://github.com/your-org/pypia_ctl/actions/workflows/tests.yml/badge.svg)](https://github.com/your-org/pypia_ctl/actions/workflows/tests.yml)
[![Docs - GitHub Pages](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://your-org.github.io/pypia_ctl/)
[![Read the Docs](https://img.shields.io/readthedocs/pypia-ctl)](https://readthedocs.org/projects/pypia-ctl/)
[![Code Style - Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checking - mypy](https://img.shields.io/badge/types-mypy-2A6DB2.svg)](http://mypy-lang.org/)


Typed wrapper around the **Private Internet Access** CLI (`piactl`) with:
- strict subprocess runner + typed exceptions
- status getters & strategy connect (preferred → random → default)
- async monitor (`piactl monitor`)
- Pydantic v2 settings via `.env` / env vars
- proxy adapters (Playwright, httpx, Selenium)
- `.env` tools (create/merge)
- plugin hooks

## Install (PDM or pip)

```bash
# PDM
pdm install -G docs -G dev -G sphinx

# pip
pip install pydantic pydantic-settings mkdocs mkdocs-material mkdocstrings[python] ruff mypy pytest sphinx furo myst-parser
```

## Docs (MkDocs + Material)

```bash
pdm run mkdocs serve    # or: mkdocs serve
```

## Sphinx (optional)

```bash
pip install sphinx furo myst-parser
(cd sphinx-docs && make html)
open sphinx-docs/_build/html/index.html
```
