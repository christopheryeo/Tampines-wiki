#!/usr/bin/env python3
"""Require exact source-ID article, tag, and coverage parity before radar scoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def normalise(values):
    return sorted(str(value).casefold().strip() for value in values if str(value).strip())


def by_id(rows):
    return {int(row["articleId"]): {
        "publishedDate": str(row["publishedDate"])[:10],
        "tags": normalise(row.get("tags", [])),
        "outlets": normalise(row.get("outlets", [])),
        "countries": normalise(row.get("countries", [])),
    } for row in rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uat-manifest", required=True, type=Path)
    parser.add_argument("--markdown-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    uat = json.loads(args.uat_manifest.read_text(encoding="utf-8"))
    markdown = json.loads(args.markdown_manifest.read_text(encoding="utf-8"))
    failures = []
    if uat.get("asOf") != markdown.get("asOf"):
        failures.append({"failure": "asOf mismatch", "uat": uat.get("asOf"), "markdown": markdown.get("asOf")})
    uat_rows, markdown_rows = by_id(uat["articles"]), by_id(markdown["articles"])
    for article_id in sorted(set(uat_rows) | set(markdown_rows)):
        if article_id not in uat_rows:
            failures.append({"articleId": article_id, "failure": "missing from UAT"})
        elif article_id not in markdown_rows:
            failures.append({"articleId": article_id, "failure": "missing from Markdown"})
        elif uat_rows[article_id] != markdown_rows[article_id]:
            failures.append({"articleId": article_id, "failure": "article/tag/coverage mismatch"})
    report = {
        "schemaVersion": "issue-radar-parity.v1", "asOf": uat.get("asOf"),
        "uatArticleCount": len(uat_rows), "markdownArticleCount": len(markdown_rows),
        "failureCount": len(failures), "failures": failures,
        "result": "PASS" if not failures else "FAIL",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
