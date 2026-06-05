from __future__ import annotations

from dci_report_gen.config import RenderConfig
from dci_report_gen.renderers.formatters import format_value


class MarkdownRenderer:
    def __init__(self):
        self._lines: list[str] = []

    def begin(self, title: str, author: str | None, date: str) -> None:
        self._lines.append(f"# {title}\n")
        meta = []
        if author:
            meta.append(f"**Author:** {author}")
        meta.append(f"**Date:** {date}")
        self._lines.append("  \n".join(meta))
        self._lines.append("")

    def add_section(self, name: str, data: list[dict], render: RenderConfig) -> None:
        self._lines.append(f"## {name}\n")

        if render.title:
            self._lines.append(f"### {render.title}\n")

        if not data:
            self._lines.append("*No data.*\n")
            return

        if render.style == "table":
            self._render_table(data, render)
        elif render.style == "list":
            self._render_list(data, render)
        elif render.style == "summary":
            self._render_summary(data, render)
        elif render.style == "count":
            self._render_count(data)
        else:
            self._render_table(data, render)

        self._lines.append("")

    def finish(self, output_path: str) -> None:
        with open(output_path, "w") as f:
            f.write("\n".join(self._lines))

    def _render_table(self, data: list[dict], render: RenderConfig) -> None:
        if render.columns:
            headers = [c.header for c in render.columns]
            fields = [c.field for c in render.columns]
            formats = [c.format for c in render.columns]
        else:
            fields = list(data[0].keys())
            headers = fields
            formats = [None] * len(fields)

        col_widths = [len(h) for h in headers]
        rows = []
        for item in data:
            row = []
            for field, fmt in zip(fields, formats):
                val = str(format_value(item.get(field), fmt))
                row.append(val)
            rows.append(row)

        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(val))

        def pad_row(cells):
            return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, col_widths)) + " |"

        self._lines.append(pad_row(headers))
        self._lines.append(
            "| " + " | ".join("-" * w for w in col_widths) + " |"
        )
        for row in rows:
            self._lines.append(pad_row(row))

    def _render_list(self, data: list[dict], render: RenderConfig) -> None:
        if render.columns:
            for item in data:
                parts = []
                for col in render.columns:
                    val = format_value(item.get(col.field), col.format)
                    parts.append(f"**{col.header}:** {val}")
                self._lines.append(f"- {', '.join(parts)}")
        else:
            for item in data:
                parts = [f"**{k}:** {v}" for k, v in item.items()]
                self._lines.append(f"- {', '.join(parts)}")

    def _render_summary(self, data: list[dict], render: RenderConfig) -> None:
        for item in data:
            for k, v in item.items():
                self._lines.append(f"- **{k}:** {v}")

    def _render_count(self, data: list[dict]) -> None:
        self._lines.append(f"**Total:** {len(data)}")
