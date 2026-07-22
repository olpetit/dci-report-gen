# dci-report-gen

A YAML-driven report generation engine for [DCI](https://docs.distributed-ci.io/) (Distributed CI), Jira, and GitHub data. Define your report in a YAML config file with a Jinja2 template for layout, and the engine fetches data from the APIs and produces PDF or Markdown output.

## Installation

```bash
pip install .
```

Or in development mode:

```bash
pip install -e ".[dev]"
```

### System dependencies (for PDF output)

WeasyPrint requires system libraries for PDF rendering. On Fedora/RHEL:

```bash
dnf install pango cairo gdk-pixbuf2
```

On Debian/Ubuntu:

```bash
apt install libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0
```

## Quick start

```bash
# Generate a Markdown report
dci-report-gen config.yaml -o report.md

# Generate a PDF report
dci-report-gen config.yaml -o report.pdf

# Override variables from the command line
dci-report-gen config.yaml -o report.md --var date_start=2025-06-01

# Use a predefined template
dci-report-gen --list-templates
```

## Authentication

Credentials are read from environment variables. Create a `.env` file in the project root (it is gitignored):

```env
# DCI (required for DCI data)
DCI_CS_URL=https://api.distributed-ci.io
DCI_CLIENT_ID=remoteci/<your-client-id>
DCI_API_SECRET=<your-api-secret>

# Jira (required for Jira data)
JIRA_URL=https://redhat.atlassian.net
JIRA_API_TOKEN=<your-jira-token>

# GitHub (required for GitHub data)
GITHUB_TOKEN=<your-github-token>
```

Only the credentials for data sources used in your config are required.

## Config file format

A config file defines the report metadata, named data sources, variables, and a Jinja2 layout template.

```yaml
report:
  title: "Weekly CI Report"
  author: "DCI Team"
  date: auto
  layout: weekly-report.md.j2

vars:
  date_start: "2025-06-01"

data:
  daily_jobs:
    type: dci
    query: "(((tags in ['daily']) and (components.type='ocp')) and (created_at>='{{date_start}}'))"
    fields: ["id", "name", "status", "created_at", "duration"]
    limit: 20
    sort: "-created_at"
  open_tickets:
    type: jira
    jql: "project = CILAB AND status = Open"
    max_results: 50
```

The engine fetches all named data sources, then passes them as context variables to the Jinja2 template.

### Data sources

Each entry in the `data` block defines a named data source.

**DCI** (`type: dci`) — searches DCI jobs via the analytics API:

| Field   | Description                          | Default         |
|---------|--------------------------------------|-----------------|
| `query` | DCI search query (parenthesized DSL) | required        |
| `fields`| List of fields to return             | all             |
| `limit` | Max number of results                | `100`           |
| `sort`  | Sort field (prefix `-` for desc)     | `-created_at`   |
| `aggs`  | Elasticsearch aggregation object     | none            |

**Jira** (`type: jira`) — runs a JQL query:

| Field        | Description               | Default |
|--------------|---------------------------|---------|
| `jql`        | JQL query string          | required|
| `max_results`| Max number of results     | `50`    |
| `fields`     | List of fields to extract | `key`, `summary`, `status`, `assignee` |

**GitHub** (`type: github`) — searches issues and pull requests:

| Field        | Description                      | Default |
|--------------|----------------------------------|---------|
| `query`      | GitHub search query              | required|
| `max_results`| Max number of results            | `50`    |
| `fields`     | List of fields to extract        | `number`, `title`, `state`, `author` |

### Variables

The `vars` block defines variables substituted into data source queries using `{{var_name}}` syntax. Variables can be overridden from the CLI with `--var KEY=VALUE`.

## Jinja2 layout templates

The `layout` field in the config points to a Jinja2 template file (`.md.j2`). The template receives all fetched data sources as variables, plus `title`, `author`, `date`, and any `vars`.

### Example template (`weekly-report.md.j2`)

```jinja
# {{ title }}

**Author:** {{ author }}
**Date:** {{ date }}

## Recent OCP Daily Jobs

| Name | Status | Date | Duration | Link |
| ---- | ------ | ---- | -------- | ---- |
{% for job in daily_jobs %}
| {{ job.name }} | {{ job.status }} | {{ job.created_at | date }} | {{ job.duration | duration }} | [View](https://www.distributed-ci.io/jobs/{{ job.id }}) |
{% endfor %}

{% if open_tickets %}
## Open Jira Tickets

{% for t in open_tickets %}
- [{{ t.key }}](https://redhat.atlassian.net/browse/{{ t.key }}) — {{ t.summary }} ({{ t.status }})
{% endfor %}
{% endif %}
```

### Custom filters

The following Jinja2 filters are available in templates:

| Filter          | Description                                | Example                          |
|-----------------|--------------------------------------------|----------------------------------|
| `duration`      | Convert seconds to `Xh Ym Zs`             | `{{ job.duration \| duration }}` |
| `date`          | Format ISO timestamp as `YYYY-MM-DD HH:MM`| `{{ job.created_at \| date }}`   |
| `jira_link`     | Render a Jira ticket key as a Markdown link| `{{ key \| jira_link }}`         |
| `github_link`   | Render a PR number as a Markdown link      | `{{ pr \| github_link }}`        |

### Template search paths

The engine searches for Jinja2 templates in this order:
1. The directory containing the YAML config file
2. The built-in templates directory (`src/dci_report_gen/templates/`)

This means you can place `.md.j2` files next to your config files in the lab config repo.

## Predefined templates

Templates are reusable YAML report definitions stored in the package. They declare parameters with defaults and bundle a Jinja2 layout.

### Using a template

Create a minimal config that references a template by name:

```yaml
template:
  type: daily-status
  params:
    date_start: "2025-06-01"
    limit: 10
```

### Writing a template

Templates are YAML files placed in `src/dci_report_gen/templates/` alongside their `.md.j2` layout file:

```yaml
description: "Daily CI job status report"

params:
  date_start:
    required: true
  limit:
    default: 50

report:
  title: "Daily CI Status — {{ date_start }}"
  author: "DCI Team"
  layout: daily-status.md.j2

data:
  daily_jobs:
    type: dci
    query: "..."
    limit: "{{limit}}"
```

List available templates with:

```bash
dci-report-gen --list-templates
```

## Output formats

The output format is determined by the file extension:

- `.md` — Markdown rendered by Jinja2
- `.pdf` — Markdown → HTML → PDF via WeasyPrint with CSS styling

### Customizing PDF styling

The PDF uses a default CSS stylesheet. You can override it by placing a `custom.css` file and adjusting the rendering pipeline (future feature).

## Legacy sections mode

For simple reports that don't need a Jinja2 template, you can use the original `sections` format:

```yaml
report:
  title: "Simple Report"

sections:
  - name: "OCP Jobs"
    source:
      type: dci
      query: "..."
      fields: ["id", "status"]
    render:
      style: table
      columns:
        - header: "Job ID"
          field: "id"
        - header: "Status"
          field: "status"
```

This mode is used when no `layout` field is present in the config.

## Project structure

```
src/dci_report_gen/
├── cli.py              # CLI entry point
├── config.py           # YAML config loading and dataclasses
├── engine.py           # Fetch → render pipeline
├── fetchers/
│   ├── dci.py          # DCI job search (dciclient)
│   ├── jira.py         # Jira JQL queries
│   └── github.py       # GitHub issue/PR search
├── renderers/
│   ├── jinja.py        # Jinja2 + WeasyPrint rendering
│   ├── markdown.py     # Markdown renderer (legacy sections mode)
│   ├── formatters.py   # Value formatting (date, duration, links)
│   └── default.css     # PDF stylesheet
└── templates/
    ├── registry.py     # Template discovery and expansion
    ├── daily-status.yaml
    └── daily-status.md.j2
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

Apache License 2.0
