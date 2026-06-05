from __future__ import annotations

import sys

from dci_report_gen.config import ReportConfig


class ReportEngine:
    def __init__(self):
        self._fetchers = {}

    def _get_fetcher(self, source_type: str):
        if source_type not in self._fetchers:
            if source_type == "dci":
                from dci_report_gen.fetchers.dci import DCIFetcher

                self._fetchers[source_type] = DCIFetcher()
            elif source_type == "jira":
                from dci_report_gen.fetchers.jira import JiraFetcher

                self._fetchers[source_type] = JiraFetcher()
            elif source_type == "github":
                from dci_report_gen.fetchers.github import GitHubFetcher

                self._fetchers[source_type] = GitHubFetcher()
            else:
                raise ValueError(f"Unknown source type: {source_type}")
        return self._fetchers[source_type]

    def _get_renderer(self, output_path: str):
        if output_path.endswith(".pdf"):
            from dci_report_gen.renderers.pdf import PDFRenderer

            return PDFRenderer()
        elif output_path.endswith(".md"):
            from dci_report_gen.renderers.markdown import MarkdownRenderer

            return MarkdownRenderer()
        else:
            raise ValueError(
                f"Unknown output format for {output_path}. Use .pdf or .md extension."
            )

    def generate(self, config: ReportConfig, output_path: str) -> None:
        renderer = self._get_renderer(output_path)
        renderer.begin(config.title, config.author, config.date)

        for section in config.sections:
            print(f"  Fetching: {section.name}...", file=sys.stderr)
            fetcher = self._get_fetcher(section.source.type)
            data = fetcher.fetch(section.source)
            print(f"  Got {len(data)} rows.", file=sys.stderr)
            renderer.add_section(section.name, data, section.render)

        renderer.finish(output_path)
        print(f"Report written to {output_path}", file=sys.stderr)
