import os
import tempfile

from dci_report_gen.config import ColumnConfig, RenderConfig
from dci_report_gen.renderers.markdown import MarkdownRenderer


def test_markdown_table():
    renderer = MarkdownRenderer()
    renderer.begin("Test Report", "Author", "2024-06-01")

    data = [
        {"id": "abc123", "status": "success", "date": "2024-06-01T10:00:00"},
        {"id": "def456", "status": "failure", "date": "2024-06-01T11:00:00"},
    ]
    render = RenderConfig(
        style="table",
        columns=[
            ColumnConfig(header="ID", field="id"),
            ColumnConfig(header="Status", field="status"),
            ColumnConfig(header="Date", field="date", format="date"),
        ],
    )
    renderer.add_section("Jobs", data, render)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name

    try:
        renderer.finish(path)
        with open(path) as f:
            content = f.read()

        assert "# Test Report" in content
        assert "## Jobs" in content
        assert "| ID" in content
        assert "abc123" in content
        assert "success" in content
        assert "failure" in content
    finally:
        os.unlink(path)


def test_markdown_list():
    renderer = MarkdownRenderer()
    renderer.begin("Test", None, "2024-06-01")

    data = [{"name": "item1", "value": "10"}, {"name": "item2", "value": "20"}]
    render = RenderConfig(
        style="list",
        columns=[
            ColumnConfig(header="Name", field="name"),
            ColumnConfig(header="Value", field="value"),
        ],
    )
    renderer.add_section("Items", data, render)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name

    try:
        renderer.finish(path)
        with open(path) as f:
            content = f.read()

        assert "- **Name:** item1" in content
        assert "- **Name:** item2" in content
    finally:
        os.unlink(path)


def test_markdown_empty_data():
    renderer = MarkdownRenderer()
    renderer.begin("Test", None, "2024-06-01")

    render = RenderConfig(style="table")
    renderer.add_section("Empty", [], render)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name

    try:
        renderer.finish(path)
        with open(path) as f:
            content = f.read()

        assert "*No data.*" in content
    finally:
        os.unlink(path)


def test_pdf_table():
    from dci_report_gen.renderers.pdf import PDFRenderer

    renderer = PDFRenderer()
    renderer.begin("PDF Test", "Author", "2024-06-01")

    data = [
        {"id": "abc123", "status": "success"},
        {"id": "def456", "status": "failure"},
    ]
    render = RenderConfig(
        style="table",
        columns=[
            ColumnConfig(header="ID", field="id"),
            ColumnConfig(header="Status", field="status"),
        ],
    )
    renderer.add_section("Jobs", data, render)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = f.name

    try:
        renderer.finish(path)
        assert os.path.getsize(path) > 0
    finally:
        os.unlink(path)
