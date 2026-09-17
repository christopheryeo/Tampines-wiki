#!/usr/bin/env python3
"""Run the approved NewsAPI.ai extraction fallback for one publisher URL."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

from local_env import load_local_env


API_URL = "https://analytics.eventregistry.org/api/v1/extractArticleInfo"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load_local_env()
    key = os.environ.get("NEWSAPI_AI_API_KEY")
    if not key:
        raise SystemExit("NEWSAPI_AI_API_KEY is unavailable")
    request = urllib.request.Request(f"{API_URL}?{urllib.parse.urlencode({'url': args.url, 'apiKey': key})}", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status, content_type, raw = response.status, response.headers.get_content_type(), response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"ERROR: extraction request failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if status != 200 or content_type != "application/json":
        print(f"ERROR: unexpected extraction response status={status} contentType={content_type}", file=sys.stderr)
        return 2
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: extraction response is not valid JSON: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(json.dumps({"status": status, "topLevelKeys": sorted(value) if isinstance(value, dict) else [], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
