from __future__ import annotations

import os

from github import Github

from dci_report_gen.config import SourceConfig

_DEFAULT_FIELDS = ["number", "title", "state", "author"]


def _get_client():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable is required")
    return Github(token)


def _extract_field(issue, field_name: str):
    if field_name == "number":
        return issue.number
    if field_name == "title":
        return issue.title
    if field_name == "state":
        return issue.state
    if field_name == "author":
        return issue.user.login if issue.user else ""
    if field_name == "created_at":
        return issue.created_at.isoformat() if issue.created_at else ""
    if field_name == "updated_at":
        return issue.updated_at.isoformat() if issue.updated_at else ""
    if field_name == "labels":
        return ", ".join(label.name for label in issue.labels)
    if field_name == "assignees":
        return ", ".join(a.login for a in issue.assignees)
    if field_name == "url":
        return issue.html_url
    return getattr(issue, field_name, "")


class GitHubFetcher:
    def fetch(self, source: SourceConfig) -> list[dict]:
        if not source.query:
            return []

        client = _get_client()
        results = client.search_issues(source.query)

        fields = source.fields or _DEFAULT_FIELDS
        rows = []
        count = 0
        for issue in results:
            if count >= source.max_results:
                break
            row = {f: _extract_field(issue, f) for f in fields}
            rows.append(row)
            count += 1

        return rows
