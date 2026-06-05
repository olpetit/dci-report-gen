# dci-report-gen

A YAML-driven report generation engine for [DCI](https://docs.distributed-ci.io/) (Distributed CI), Jira, and GitHub data. Define your report in a YAML config file, and the engine fetches data from the APIs and produces PDF or Markdown output.

## Installation

```bash
pip install .
```

Or in development mode:

```bash
pip install -e ".[dev]"
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

A config file defines the report metadata, variables, and sections. Each section specifies a data source and how to render it.

```yaml
report:
  title: "Weekly CI Report"
  author: "DCI Team"          # optional
  date: auto                  # "auto" = today, or an explicit date

vars:
  date_start: "2025-06-01"

sections:
  - name: "Recent OCP Daily Jobs"
    source:
      type: dci
      query: "(((tags in ['daily']) and (components.type='ocp')) and (created_at>='{{date_start}}'))"
      fields: ["id", "name", "status", "created_at", "duration"]
      limit: 20
      sort: "-created_at"
    render:
      style: table
      columns:
        - header: "Job ID"
          field: "id"
        - header: "Status"
          field: "status"
        - header: "Date"
          field: "created_at"
          format: "date"
        - header: "Duration"
          field: "duration"
          format: "duration"
```

### Data sources

Each section's `source` block defines where data comes from.

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

### Render styles

Each section's `render` block controls the output layout.

| Style     | Description                                  |
|-----------|----------------------------------------------|
| `table`   | Rows and columns (default)                   |
| `list`    | Bullet points with key-value pairs           |
| `summary` | Key-value display (for aggregation results)  |
| `count`   | Just the total row count                     |

### Column formatting

Columns can specify a `format` hint for value display:

| Format           | Description                            |
|------------------|----------------------------------------|
| `date`           | Format ISO timestamps as `YYYY-MM-DD HH:MM` |
| `duration`       | Convert seconds to `Xh Ym Zs`         |
| `jira_link`      | Render as a Jira ticket link           |
| `github_pr_link` | Render as a GitHub PR link             |

### Variables

The `vars` block defines variables substituted into queries and section names using `{{var_name}}` syntax. Variables can be overridden from the CLI with `--var KEY=VALUE`.

## Templates

Templates are reusable YAML report definitions stored in the package. They declare parameters with defaults and use the same config format.

### Using a template

Create a minimal config that references a template by name:

```yaml
template:
  type: daily-status
  params:
    date: "2025-06-01"
    limit: 10
```

You can append additional sections after the template:

```yaml
template:
  type: daily-status
  params:
    date: "2025-06-01"

sections:
  - name: "Extra section"
    source:
      type: jira
      jql: "project = CILAB AND status = Open"
    render:
      style: table
```

### Writing a template

Templates are YAML files placed in `src/dci_report_gen/templates/`. A template file has the same structure as a config file, plus a `params` block and a `description`:

```yaml
description: "Daily CI job status report"

params:
  date:
    required: true
  limit:
    default: 50

report:
  title: "Daily CI Status — {{date}}"
  author: "DCI Team"

sections:
  - name: "Daily OCP Jobs (since {{date}})"
    source:
      type: dci
      query: "(((tags in ['daily']) and (components.type='ocp')) and (created_at>='{{date}}'))"
      fields: ["id", "name", "status", "created_at", "duration"]
      limit: "{{limit}}"
      sort: "-created_at"
    render:
      style: table
      columns:
        - header: "Job ID"
          field: "id"
        - header: "Name"
          field: "name"
        - header: "Status"
          field: "status"
        - header: "Date"
          field: "created_at"
          format: "date"
        - header: "Duration"
          field: "duration"
          format: "duration"
```

Parameters declared as `required: true` must be provided. Parameters with a `default` value are optional. All `{{param}}` placeholders are substituted before the YAML is parsed, so numeric values like `limit` resolve correctly.

List available templates with:

```bash
dci-report-gen --list-templates
```

## Output formats

The output format is determined by the file extension:

- `.md` — GitHub-flavored Markdown with pipe-delimited tables
- `.pdf` — PDF document using ReportLab with styled tables and headings

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
│   ├── pdf.py          # ReportLab PDF renderer
│   ├── markdown.py     # Markdown renderer
│   └── formatters.py   # Value formatting (date, duration, links)
└── templates/
    ├── registry.py     # Template discovery and expansion
    └── daily-status.yaml
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

Apache License 2.0
