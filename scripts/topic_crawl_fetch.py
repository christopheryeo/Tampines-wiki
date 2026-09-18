#!/usr/bin/env python3
"""Fetch one bounded NewsAPI.ai Set A page without exposing its credential."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

from local_env import load_local_env
import os


API_URL = "https://eventregistry.org/api/v1/article/getArticles"
UTC = ZoneInfo("UTC")


def provider_window(date_start: str, date_end: str, timezone: str | None) -> tuple[str, str]:
    """Map a local inclusive date range onto the UTC days the provider indexes.

    NewsAPI.ai selects ``dateStart``/``dateEnd`` as UTC days, while the plan's
    boundaries are days in the invocation timezone. Submitting local dates
    verbatim crawls the wrong window -- for Asia/Singapore it silently drops the
    00:00-08:00 local slice, and a same-day crawl run before 08:00 local asks
    for a UTC day that has not begun and returns zero for every keyword. The
    caller still applies the local date gate to the returned articles; this only
    widens the query so the local window is fully covered.
    """
    if not timezone:
        return date_start, date_end
    tz = ZoneInfo(timezone)
    start = datetime.fromisoformat(date_start).replace(tzinfo=tz)
    end = datetime.fromisoformat(date_end).replace(tzinfo=tz) + timedelta(days=1)
    return (start.astimezone(UTC).date().isoformat(),
            (end.astimezone(UTC) - timedelta(seconds=1)).date().isoformat())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--date-start", required=True)
    parser.add_argument("--date-end", required=True)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument(
        "--timezone",
        help="invocation timezone of --date-start/--date-end (e.g. Asia/Singapore); "
             "converts them to the overlapping provider UTC days",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.page < 1:
        raise SystemExit("--page must be positive")
    date_start, date_end = provider_window(args.date_start, args.date_end, args.timezone)
    load_local_env()
    key = os.environ.get("NEWSAPI_AI_API_KEY")
    if not key:
        raise SystemExit("NEWSAPI_AI_API_KEY is unavailable")
    payload = {
        "action": "getArticles", "keyword": args.keyword, "lang": ["eng"],
        "dateStart": date_start, "dateEnd": date_end, "articlesSortBy": "date",
        "articleBodyLen": -1, "dataType": ["news"], "isDuplicateFilter": "keepAll",
        "resultType": "articles", "articlesCount": 100, "articlesPage": args.page, "apiKey": key,
    }
    request = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status = response.status
            content_type = response.headers.get_content_type()
            raw = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"ERROR: provider request failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if status != 200 or content_type != "application/json":
        print(f"ERROR: unexpected provider response status={status} contentType={content_type}", file=sys.stderr)
        return 2
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: provider response is not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(result.get("articles"), dict):
        print("ERROR: provider response lacks articles object", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    articles = result["articles"]
    print(json.dumps({"status": status, "page": articles.get("page"), "pages": articles.get("pages"),
                      "count": articles.get("count"), "totalResults": articles.get("totalResults"),
                      "requestedWindow": [args.date_start, args.date_end],
                      "providerWindowUTC": [date_start, date_end],
                      "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
