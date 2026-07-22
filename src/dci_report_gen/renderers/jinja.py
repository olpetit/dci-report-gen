from __future__ import annotations

from pathlib import Path

import markdown as md
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from dci_report_gen.renderers.formatters import _format_date, _format_duration

DEFAULT_CSS = Path(__file__).parent / "default.css"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _build_env(search_paths: list[str | Path]) -> Environment:
    env = Environment(
        loader=FileSystemLoader([str(p) for p in search_paths]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["duration"] = _filter_duration
    env.filters["date"] = _filter_date
    env.filters["jira_link"] = _filter_jira_link
    env.filters["github_link"] = _filter_github_link
    return env


def _filter_duration(value):
    if value is None:
        return ""
    return _format_duration(value)


def _filter_date(value):
    if value is None:
        return ""
    return _format_date(value)


def _filter_jira_link(key, base_url="https://redhat.atlassian.net"):
    if not key:
        return ""
    return f"[{key}]({base_url}/browse/{key})"


def _filter_github_link(number, repo=""):
    if not number:
        return ""
    if repo:
        return f"[#{number}](https://github.com/{repo}/pull/{number})"
    return f"#{number}"


def render_markdown(
    template_name: str,
    search_paths: list[str | Path],
    context: dict,
) -> str:
    env = _build_env(search_paths)
    template = env.get_template(template_name)
    return template.render(**context)


def markdown_to_pdf(
    md_text: str,
    output_path: str,
    css_path: str | Path | None = None,
) -> None:
    html_body = md.markdown(
        md_text,
        extensions=["tables", "fenced_code"],
    )
    css_file = Path(css_path) if css_path else DEFAULT_CSS
    css_content = css_file.read_text() if css_file.exists() else ""

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{css_content}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    HTML(string=html_doc).write_pdf(output_path)
