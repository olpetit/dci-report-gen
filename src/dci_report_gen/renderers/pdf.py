from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from dci_report_gen.config import RenderConfig
from dci_report_gen.renderers.formatters import format_value

_STYLES = getSampleStyleSheet()

STYLE_TITLE = ParagraphStyle(
    "ReportTitle",
    parent=_STYLES["Title"],
    fontSize=20,
    spaceAfter=6 * mm,
)

STYLE_META = ParagraphStyle(
    "ReportMeta",
    parent=_STYLES["Normal"],
    fontSize=10,
    textColor=colors.grey,
    spaceAfter=8 * mm,
)

STYLE_SECTION = ParagraphStyle(
    "SectionHeading",
    parent=_STYLES["Heading2"],
    spaceBefore=6 * mm,
    spaceAfter=3 * mm,
)

STYLE_BODY = ParagraphStyle(
    "Body",
    parent=_STYLES["Normal"],
    fontSize=9,
)

STYLE_CELL = ParagraphStyle(
    "Cell",
    parent=_STYLES["Normal"],
    fontSize=8,
    leading=10,
)

TABLE_STYLE = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
)


class PDFRenderer:
    def __init__(self):
        self._elements: list = []
        self._title = ""

    def begin(self, title: str, author: str | None, date: str) -> None:
        self._title = title
        self._elements.append(Paragraph(title, STYLE_TITLE))
        meta_parts = []
        if author:
            meta_parts.append(f"Author: {author}")
        meta_parts.append(f"Date: {date}")
        self._elements.append(Paragraph(" | ".join(meta_parts), STYLE_META))

    def add_section(self, name: str, data: list[dict], render: RenderConfig) -> None:
        self._elements.append(Paragraph(name, STYLE_SECTION))

        if render.title:
            self._elements.append(Paragraph(render.title, STYLE_BODY))
            self._elements.append(Spacer(1, 2 * mm))

        if not data:
            self._elements.append(Paragraph("<i>No data.</i>", STYLE_BODY))
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

    def finish(self, output_path: str) -> None:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            title=self._title,
        )
        doc.build(self._elements)

    def _render_table(self, data: list[dict], render: RenderConfig) -> None:
        if render.columns:
            headers = [c.header for c in render.columns]
            fields = [c.field for c in render.columns]
            formats = [c.format for c in render.columns]
        else:
            fields = list(data[0].keys())
            headers = fields
            formats = [None] * len(fields)

        table_data = [headers]
        for item in data:
            row = []
            for field, fmt in zip(fields, formats):
                val = format_value(item.get(field), fmt)
                cell = Paragraph(str(val), STYLE_CELL)
                row.append(cell)
            table_data.append(row)

        page_width = A4[0] - 30 * mm
        col_width = page_width / len(headers)
        col_widths = [col_width] * len(headers)

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TABLE_STYLE)
        self._elements.append(table)
        self._elements.append(Spacer(1, 4 * mm))

    def _render_list(self, data: list[dict], render: RenderConfig) -> None:
        if render.columns:
            for item in data:
                parts = []
                for col in render.columns:
                    val = format_value(item.get(col.field), col.format)
                    parts.append(f"<b>{col.header}:</b> {val}")
                self._elements.append(
                    Paragraph("&bull; " + ", ".join(parts), STYLE_BODY)
                )
        else:
            for item in data:
                parts = [f"<b>{k}:</b> {v}" for k, v in item.items()]
                self._elements.append(
                    Paragraph("&bull; " + ", ".join(parts), STYLE_BODY)
                )
        self._elements.append(Spacer(1, 4 * mm))

    def _render_summary(self, data: list[dict], render: RenderConfig) -> None:
        table_data = []
        for item in data:
            for k, v in item.items():
                table_data.append([
                    Paragraph(f"<b>{k}</b>", STYLE_CELL),
                    Paragraph(str(v), STYLE_CELL),
                ])

        if table_data:
            page_width = A4[0] - 30 * mm
            table = Table(table_data, colWidths=[page_width * 0.3, page_width * 0.7])
            table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            self._elements.append(table)
        self._elements.append(Spacer(1, 4 * mm))

    def _render_count(self, data: list[dict]) -> None:
        self._elements.append(
            Paragraph(f"<b>Total:</b> {len(data)}", STYLE_BODY)
        )
        self._elements.append(Spacer(1, 4 * mm))
