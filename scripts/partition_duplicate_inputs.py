#!/usr/bin/env python3
"""Partition exact same-source duplicate loose inputs before enrichment.

The frozen master manifest is authoritative. Source-empty stubs are left for the
source-empty partition. For source-bearing rows sharing an article ID, this
utility permits a mechanical hold only when URL, publisher domain, title, and
body are identical across the group. It keeps the longest filename (then
lexicographically first), records every held file and hash, and never overwrites
a hold target. Without ``--write`` it is a non-moving preview.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from enrich_radar_inputs import parse_frontmatter, split_note
from partition_source_empty_inputs import is_empty_raw_response


ROOT = Path(__file__).resolve().parents[1]


class DuplicatePartitionError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value: Any) -> str:
    return str(value or "").strip()


def load_row(row: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / normalized(row.get("path"))
    if not path.is_file():
        raise DuplicatePartitionError(f"manifest input missing: {path}")
    if sha256(path) != row.get("sha256"):
        raise DuplicatePartitionError(f"manifest hash drift: {path}")
    lines, body = split_note(path.read_text(encoding="utf-8"))
    data = parse_frontmatter(lines)
    article_id = normalized(data.get("articleId"))
    if not article_id:
        raise DuplicatePartitionError(f"missing article ID: {path}")
    source_empty = (
        not normalized(data.get("articleTitle"))
        and not normalized(data.get("publishedDate"))
        and not normalized(data.get("url"))
        and not body.strip()
        and is_empty_raw_response(data.get("rawNewsApiResponse"))
    )
    return {
        "manifest": row,
        "path": path,
        "articleId": article_id,
        "sourceEmpty": source_empty,
        "identity": {
            "url": normalized(data.get("url")),
            "publisherDomain": normalized(data.get("publisherDomain")).lower(),
            "articleTitle": normalized(data.get("articleTitle")),
            "bodySha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master-manifest", type=Path, required=True)
    parser.add_argument("--hold-dir", type=Path, required=True)
    parser.add_argument("--hold-output", type=Path, required=True)
    parser.add_argument("--reduced-manifest", type=Path, required=True)
    parser.add_argument("--reduced-evidence", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    master = json.loads(args.master_manifest.resolve().read_text(encoding="utf-8"))
    rows = master.get("articles")
    if not isinstance(rows, list) or master.get("articleCount") != len(rows):
        raise DuplicatePartitionError("invalid master manifest article count")

    loaded = [load_row(row) for row in rows]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in loaded:
        if not row["sourceEmpty"]:
            groups[row["articleId"]].append(row)

    holds: list[dict[str, Any]] = []
    held_paths: set[Path] = set()
    conflicts: list[dict[str, Any]] = []
    for article_id, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        identities = {json.dumps(row["identity"], sort_keys=True) for row in group}
        if len(identities) != 1:
            conflicts.append({
                "articleId": article_id,
                "paths": [str(row["path"].relative_to(ROOT)) for row in group],
                "identities": [row["identity"] for row in group],
            })
            continue
        keeper = sorted(group, key=lambda row: (-len(row["path"].name), row["path"].name))[0]
        for row in group:
            if row is keeper:
                continue
            target = args.hold_dir.resolve() / row["path"].name
            holds.append({
                "articleId": article_id,
                "sourcePath": str(row["path"].relative_to(ROOT)),
                "holdPath": str(target.relative_to(ROOT)),
                "keptPath": str(keeper["path"].relative_to(ROOT)),
                "sha256": row["manifest"]["sha256"],
                "identity": row["identity"],
                "holdReason": "verified same-source duplicate loose arrival",
            })
            held_paths.add(row["path"])

    if conflicts:
        raise DuplicatePartitionError(
            f"{len(conflicts)} duplicate article ID group(s) have non-identical saved identity"
        )

    if args.write:
        args.hold_dir.resolve().mkdir(parents=True, exist_ok=True)
        for row in holds:
            source = ROOT / row["sourcePath"]
            target = ROOT / row["holdPath"]
            if target.exists():
                raise DuplicatePartitionError(f"hold target already exists: {target}")
            source.replace(target)
            if sha256(target) != row["sha256"]:
                raise DuplicatePartitionError(f"hash changed while moving duplicate: {target}")

    reduced_rows = [row["manifest"] for row in loaded if row["path"] not in held_paths]
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    hold_payload = {
        "schemaVersion": "duplicate-input-holds.v1",
        "createdAt": now,
        "mode": "write" if args.write else "dry-run",
        "holdCount": len(holds),
        "conflictCount": 0,
        "holds": holds,
    }
    reduced_payload = {
        "schemaVersion": "loose-article-manifest.v1",
        "createdAt": now,
        "articleCount": len(reduced_rows),
        "articles": reduced_rows,
    }
    for path in (args.hold_output, args.reduced_manifest, args.reduced_evidence):
        path.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.hold_output.resolve().write_text(
        json.dumps(hold_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.reduced_manifest.resolve().write_text(
        "\n".join(str(row["path"]) for row in reduced_rows) + "\n", encoding="utf-8"
    )
    args.reduced_evidence.resolve().write_text(
        json.dumps(reduced_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "mode": hold_payload["mode"],
        "masterCount": len(rows),
        "duplicateHoldCount": len(holds),
        "reducedCount": len(reduced_rows),
        "conflictCount": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
