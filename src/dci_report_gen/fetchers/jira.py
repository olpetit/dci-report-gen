from __future__ import annotations

import os

from jira import JIRA

from dci_report_gen.config import SourceConfig

_FIELD_MAP = {
    "key": lambda issue: issue.key,
    "summary": lambda issue: issue.fields.summary,
    "status": lambda issue: str(issue.fields.status),
    "assignee": lambda issue: str(issue.fields.assignee) if issue.fields.assignee else "",
    "reporter": lambda issue: str(issue.fields.reporter) if issue.fields.reporter else "",
    "priority": lambda issue: str(issue.fields.priority) if issue.fields.priority else "",
    "issue_type": lambda issue: str(issue.fields.issuetype),
    "created": lambda issue: issue.fields.created,
    "updated": lambda issue: issue.fields.updated,
    "labels": lambda issue: ", ".join(issue.fields.labels),
    "components": lambda issue: ", ".join(str(c) for c in issue.fields.components),
    "fix_versions": lambda issue: ", ".join(str(v) for v in issue.fields.fixVersions),
}

_DEFAULT_FIELDS = ["key", "summary", "status", "assignee"]


def _get_client():
    url = os.environ.get("JIRA_URL", "https://redhat.atlassian.net")
    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        raise RuntimeError("JIRA_API_TOKEN environment variable is required")
    return JIRA(server=url, token_auth=token)


def _extract_field(issue, field_name: str) -> str:
    if field_name in _FIELD_MAP:
        return _FIELD_MAP[field_name](issue)
    attr = getattr(issue.fields, field_name, None)
    if attr is not None:
        return str(attr)
    return ""


class JiraFetcher:
    def fetch(self, source: SourceConfig) -> list[dict]:
        if not source.jql:
            return []

        client = _get_client()
        issues = client.search_issues(
            source.jql,
            maxResults=source.max_results,
        )

        fields = source.fields or _DEFAULT_FIELDS
        rows = []
        for issue in issues:
            row = {f: _extract_field(issue, f) for f in fields}
            rows.append(row)

        return rows
