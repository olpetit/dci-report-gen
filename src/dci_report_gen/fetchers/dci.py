from __future__ import annotations

from dciclient.v1.api import context as dci_context
from dciclient.v1.api import job as dci_job

from dci_report_gen.config import SourceConfig


def _get_context():
    return dci_context.build_signature_context()


def _extract_field(obj: dict, dotted_key: str):
    parts = dotted_key.split(".")
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, list):
            return ", ".join(
                str(_extract_field(item, ".".join([part] + parts[parts.index(part) + 1 :])))
                for item in current
                if item is not None
            )
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _flatten_row(hit: dict, fields: list[str] | None) -> dict:
    if fields:
        return {f: _extract_field(hit, f) for f in fields}
    return hit


class DCIFetcher:
    def fetch(self, source: SourceConfig) -> list[dict]:
        ctx = _get_context()

        if source.query:
            return self._search_jobs(ctx, source)
        return []

    def _search_jobs(self, ctx, source: SourceConfig) -> list[dict]:
        params = {"query": source.query, "limit": source.limit, "sort": source.sort}
        if source.fields:
            params["fields"] = ",".join(source.fields)
        if source.aggs:
            import json

            params["aggs"] = json.dumps(source.aggs)

        resp = dci_job.search(ctx, **params)
        if resp.status_code != 200:
            raise RuntimeError(f"DCI search failed ({resp.status_code}): {resp.text}")

        data = resp.json()

        if source.aggs and "aggregations" in data:
            return self._flatten_aggs(data["aggregations"])

        hits_obj = data.get("hits", {})
        hits = hits_obj.get("hits", []) if isinstance(hits_obj, dict) else hits_obj
        sources = [hit.get("_source", hit) for hit in hits]

        return [_flatten_row(src, source.fields) for src in sources]

    def _flatten_aggs(self, aggs: dict) -> list[dict]:
        rows = []
        for agg_name, agg_data in aggs.items():
            if "buckets" in agg_data:
                for bucket in agg_data["buckets"]:
                    rows.append({"key": bucket.get("key"), "count": bucket.get("doc_count")})
            elif "value" in agg_data:
                rows.append({"key": agg_name, "value": agg_data["value"]})
        return rows
