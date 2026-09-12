#!/usr/bin/env python3
"""Hold loose arrivals whose compiled same-source article already exists.

Consumes a dry-route JSON report. A conflict is mechanically holdable only when
the loose and compiled copies have the same non-empty canonical URL and no
publisher-domain disagreement. Other route errors or identity differences are
reported as conflicts and block writes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from enrich_radar_inputs import parse_frontmatter, split_note


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "compiled article already exists: "


class CompiledConflictError(RuntimeError):
    pass


def metadata(path: Path) -> dict:
    lines, _ = split_note(path.read_text(encoding="utf-8"))
    return parse_frontmatter(lines)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value(data: dict, *keys: str) -> str:
    for key in keys:
        item = str(data.get(key) or "").strip()
        if item:
            return item
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-report", type=Path, required=True)
    parser.add_argument("--hold-dir", type=Path, required=True)
    parser.add_argument("--hold-output", type=Path, required=True)
    parser.add_argument("--routable-manifest", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    report = json.loads(args.route_report.resolve().read_text(encoding="utf-8"))
    holds = []
    conflicts = []
    for row in report.get("errors", []):
        error = str(row.get("error") or "")
        if not error.startswith(PREFIX):
            conflicts.append(row)
            continue
        loose = Path(str(row["source"])).resolve()
        compiled = Path(error[len(PREFIX):]).resolve()
        if not loose.is_file() or not compiled.is_file():
            conflicts.append({**row, "identityError": "loose or compiled file is missing"})
            continue
        loose_data = metadata(loose)
        compiled_data = metadata(compiled)
        loose_url = value(loose_data, "url", "sourceUrl")
        compiled_url = value(compiled_data, "sourceUrl", "url")
        loose_publisher = value(loose_data, "publisherDomain").lower()
        compiled_publisher = value(compiled_data, "publisherDomain").lower()
        publisher_agrees = not compiled_publisher or loose_publisher == compiled_publisher
        if not loose_url or loose_url != compiled_url or not publisher_agrees:
            conflicts.append({
                **row,
                "identityError": "saved URL or publisher domain does not prove a same-source repeat",
                "looseUrl": loose_url,
                "compiledUrl": compiled_url,
                "loosePublisherDomain": loose_publisher,
                "compiledPublisherDomain": compiled_publisher,
            })
            continue
        target = args.hold_dir.resolve() / loose.name
        holds.append({
            "articleId": value(loose_data, "articleId"),
            "sourcePath": str(loose.relative_to(ROOT)),
            "compiledPath": str(compiled.relative_to(ROOT)),
            "holdPath": str(target.relative_to(ROOT)),
            "sha256": sha256(loose),
            "canonicalUrl": loose_url,
            "publisherDomain": loose_publisher,
            "holdReason": "verified same-source arrival already compiled",
        })

    if conflicts:
        raise CompiledConflictError(f"{len(conflicts)} route conflict(s) require review")

    if args.write:
        args.hold_dir.resolve().mkdir(parents=True, exist_ok=True)
        for row in holds:
            source = ROOT / row["sourcePath"]
            target = ROOT / row["holdPath"]
            if target.exists():
                raise CompiledConflictError(f"hold target already exists: {target}")
            source.replace(target)
            if sha256(target) != row["sha256"]:
                raise CompiledConflictError(f"hash changed while moving hold: {target}")

    routable = [str(Path(row["source"]).resolve().relative_to(ROOT)) for row in report.get("routes", [])]
    payload = {
        "schemaVersion": "compiled-input-holds.v1",
        "createdAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": "write" if args.write else "dry-run",
        "holdCount": len(holds),
        "conflictCount": 0,
        "holds": holds,
    }
    args.hold_output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.routable_manifest.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.hold_output.resolve().write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.routable_manifest.resolve().write_text("\n".join(routable) + "\n", encoding="utf-8")
    print(json.dumps({
        "mode": payload["mode"],
        "routableCount": len(routable),
        "holdCount": len(holds),
        "conflictCount": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
