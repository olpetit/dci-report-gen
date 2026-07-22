# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A YAML-driven report generation engine that fetches data from DCI (Distributed CI), Jira, and GitHub APIs, then renders Markdown or PDF output using Jinja2 templates. Users define reports in YAML config files specifying data sources and a layout template.

## Commands

```bash
# Install (dev mode)
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/test_config.py::test_name

# Lint
ruff check src/ tests/

# Generate a report
dci-report-gen config.yaml -o report.md
```

Uses `uv` for dependency management (uv.lock present). Python 3.10+.

## Architecture

The pipeline is: **YAML config → fetch data → render template → output file**.

- **`config.py`** — Parses YAML into dataclasses (`ReportConfig`, `SourceConfig`, etc.). Handles `{{var}}` substitution in queries. Two config modes: Jinja2 layout mode (has `layout` + `data` block) and legacy sections mode (has `sections` block).

- **`engine.py`** — Orchestrates the pipeline. Routes to `_generate_jinja()` or `_generate_sections()` based on whether `layout` is set. Lazy-loads fetchers on first use.

- **`fetchers/`** — One module per data source (`dci.py`, `jira.py`, `github.py`). Each has a `fetch(source: SourceConfig) -> list[dict]` method. Fetchers are initialized with credentials from env vars (loaded via `python-dotenv` from `.env`).

- **`renderers/jinja.py`** — Renders Jinja2 templates to Markdown, optionally converts to PDF via WeasyPrint. Registers custom filters (`duration`, `date`, `jira_link`, `github_link`).

- **`renderers/markdown.py`** and **`renderers/pdf.py`** — Legacy sections-mode renderers.

- **`templates/registry.py`** — Discovers predefined templates from `templates/*.yaml`. A template bundles a YAML config skeleton + `.md.j2` layout file with declared parameters.

### Template resolution order

Jinja2 templates are searched: (1) directory of the YAML config file, (2) built-in `templates/` directory.

### Two rendering paths

1. **Jinja2 mode** (preferred): config has `layout` field pointing to a `.md.j2` file + `data` block with named sources. All fetched data is passed as template context.
2. **Legacy sections mode**: config has `sections` list, each with `source` + `render` config. Uses `MarkdownRenderer`/`PDFRenderer` directly.

## Credentials

API credentials come from env vars (see `.env` file, which is gitignored). Only credentials for data sources actually used in a config are required.
