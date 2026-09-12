#!/usr/bin/env python3
"""Hold same-source inputs whose computed cascade output already exists."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from ingest_cascade import article_filename, canonical_field, parse_frontmatter, yaml_scalar


ROOT = Path(__file__).resolve().parents[1]
ARTICLE_ROOT = ROOT / "entities" / "article"


class CascadeConflictError(RuntimeError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(frontmatter: dict) -> tuple[str, str]:
    source_id = yaml_scalar(canonical_field(frontmatter, "id", "sourceId", "articleId"))
    source_url = yaml_scalar(canonical_field(frontmatter, "url", "sourceUrl"))
    return source_id, source_url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--hold-dir", type=Path, required=True)
    parser.add_argument("--hold-output", type=Path, required=True)
    parser.add_argument("--cascade-manifest", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    entries = [line.strip() for line in args.manifest.resolve().read_text(encoding="utf-8").splitlines() if line.strip()]
    ready: list[str] = []
    already_processed: list[str] = []
    holds: list[dict] = []
    conflicts: list[dict] = []
    for entry in entries:
        source = ROOT / entry
        if not source.exists():
            already_processed.append(entry)
            continue
        source_text = source.read_text(encoding="utf-8")
        source_frontmatter, _ = parse_frontmatter(source_text)
        target = ARTICLE_ROOT / source.parent.name / article_filename(source_frontmatter, source)
        if not target.exists():
            ready.append(entry)
            continue
        target_frontmatter, _ = parse_frontmatter(target.read_text(encoding="utf-8"))
        source_id, source_url = identity(source_frontmatter)
        target_id, target_url = identity(target_frontmatter)
        if not source_id or source_id != target_id or not source_url or source_url != target_url:
            conflicts.append({
                "sourcePath": entry,
                "compiledPath": str(target.relative_to(ROOT)),
                "sourceId": source_id,
                "compiledSourceId": target_id,
                "sourceUrl": source_url,
                "compiledSourceUrl": target_url,
            })
            continue
        hold_path = args.hold_dir.resolve() / source.name
        holds.append({
            "articleId": source_id,
            "sourcePath": entry,
            "compiledPath": str(target.relative_to(ROOT)),
            "holdPath": str(hold_path.relative_to(ROOT)),
            "sha256": digest(source),
            "canonicalUrl": source_url,
            "holdReason": "verified same-source computed cascade output already compiled",
        })

    if conflicts:
        raise CascadeConflictError(f"{len(conflicts)} computed output collision(s) require review")
    if args.write:
        args.hold_dir.resolve().mkdir(parents=True, exist_ok=True)
        for row in holds:
            source = ROOT / row["sourcePath"]
            target = ROOT / row["holdPath"]
            if target.exists():
                raise CascadeConflictError(f"hold target already exists: {target}")
            source.replace(target)
            if digest(target) != row["sha256"]:
                raise CascadeConflictError(f"hash changed while moving hold: {target}")

    payload = {
        "schemaVersion": "cascade-output-conflict-holds.v1",
        "createdAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": "write" if args.write else "dry-run",
        "manifestCount": len(entries),
        "alreadyProcessedCount": len(already_processed),
        "cascadeReadyCount": len(ready),
        "holdCount": len(holds),
        "conflictCount": 0,
        "alreadyProcessed": already_processed,
        "holds": holds,
    }
    args.hold_output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.cascade_manifest.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.hold_output.resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.cascade_manifest.resolve().write_text("\n".join(ready) + ("\n" if ready else ""), encoding="utf-8")
    print(json.dumps({key: payload[key] for key in [
        "mode", "manifestCount", "alreadyProcessedCount", "cascadeReadyCount", "holdCount", "conflictCount"
    ]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
