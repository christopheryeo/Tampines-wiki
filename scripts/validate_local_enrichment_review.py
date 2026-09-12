#!/usr/bin/env python3
"""Validate saved-evidence-only local enrichment review artifacts.

This validator is deliberately read-only.  It binds a review artifact to a
frozen eligible-manifest record and to the exact routed input bytes, then
checks that every quoted evidence excerpt occurs literally in those bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from input_article_contract import (
    EVENT_VALUES,
    INSTITUTIONAL_CATEGORIES,
    SENTIMENT_VALUES,
    TONE_VALUES,
)
from tag_registry import TAG_ROOT, active_inventory


ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = ROOT / "Inputs" / "articles"
REVIEW_SCHEMA = "local-codex-enrichment-review.v1"
CLASSIFICATION_FIELDS = {
    "tone",
    "tone_confidence",
    "tone_evidence",
    "tone_sentiment",
    "sentiment_confidence",
    "sentiment_evidence",
    "event_type",
    "event_confidence",
    "event_trigger",
    "event_evidence",
    "issue_tags",
    "outlet_name",
    "outlet_country",
    "institutional_category",
    "metadata_confidence",
    "review_required",
    "review_reason",
}


class ValidationError(RuntimeError):
    """Raised when an artifact is not safe to reconcile or apply."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read valid JSON object from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"JSON root must be an object: {path}")
    return value


def repository_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValidationError(f"path is outside repository: {path}") from exc


def display_path(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def locate_routed_input(filename: str, input_root: Path) -> Path:
    matches = sorted(input_root.glob(f"????-??/{filename}"))
    if len(matches) != 1:
        raise ValidationError(
            f"expected exactly one routed input for {filename!r}, found {len(matches)}"
        )
    return matches[0]


def load_frozen_inputs(
    eligible_path: Path,
    routable_path: Path,
    *,
    root: Path = ROOT,
    input_root: Path = INPUT_ROOT,
    expected_count: int,
) -> dict[str, dict[str, Any]]:
    eligible = load_object(eligible_path)
    articles = eligible.get("articles")
    if not isinstance(articles, list) or eligible.get("articleCount") != len(articles):
        raise ValidationError("eligible manifest articleCount is invalid")

    eligible_by_filename: dict[str, dict[str, Any]] = {}
    for item in articles:
        if not isinstance(item, dict):
            raise ValidationError("eligible manifest article entry must be an object")
        filename = str(item.get("filename") or "")
        article_id = str(item.get("articleId") or "")
        expected_sha = str(item.get("sha256") or "")
        if not filename or not article_id or len(expected_sha) != 64:
            raise ValidationError(f"invalid eligible manifest entry: {item!r}")
        if filename in eligible_by_filename:
            raise ValidationError(f"duplicate eligible filename: {filename}")
        eligible_by_filename[filename] = item

    try:
        route_lines = [
            line.strip()
            for line in routable_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"cannot read routable manifest {routable_path}: {exc}") from exc
    filenames = [Path(line).name for line in route_lines]
    if len(filenames) != expected_count:
        raise ValidationError(
            f"routable manifest count {len(filenames)} does not equal expected {expected_count}"
        )
    if len(set(filenames)) != len(filenames):
        raise ValidationError("routable manifest has duplicate filenames")

    frozen_by_id: dict[str, dict[str, Any]] = {}
    for filename in filenames:
        if filename not in eligible_by_filename:
            raise ValidationError(f"routable file is absent from eligible manifest: {filename}")
        eligible_item = eligible_by_filename[filename]
        article_id = str(eligible_item["articleId"])
        if article_id in frozen_by_id:
            raise ValidationError(f"duplicate routable articleId: {article_id}")
        actual_path = locate_routed_input(filename, input_root)
        raw = actual_path.read_bytes()
        actual_sha = sha256_bytes(raw)
        expected_sha = str(eligible_item["sha256"])
        if actual_sha != expected_sha:
            raise ValidationError(
                f"{article_id}: routed input SHA-256 {actual_sha} does not match frozen {expected_sha}"
            )
        frozen_by_id[article_id] = {
            "filename": filename,
            "path": repository_path(actual_path, root),
            "sha256": expected_sha,
            "text": raw.decode("utf-8"),
        }
    return frozen_by_id


def require_string(article_id: str, value: Any, field: str, *, nonempty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{article_id}: {field} must be a string")
    if nonempty and not value.strip():
        raise ValidationError(f"{article_id}: {field} must be non-empty")
    return value


def require_confidence(article_id: str, value: Any, field: str) -> None:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not 0 <= value <= 1
    ):
        raise ValidationError(f"{article_id}: {field} must be a number from 0 through 1")


def validate_string_list(
    article_id: str,
    value: Any,
    field: str,
    *,
    maximum: int,
) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(f"{article_id}: {field} must be a list")
    if len(value) > maximum:
        raise ValidationError(f"{article_id}: {field} has {len(value)} items; maximum is {maximum}")
    for index, item in enumerate(value):
        require_string(article_id, item, f"{field}[{index}]", nonempty=True)
    return value


def validate_classification(
    article_id: str,
    value: Any,
    *,
    source_text: str,
    active_tags: set[str],
) -> None:
    if not isinstance(value, dict):
        raise ValidationError(f"{article_id}: classification must be an object")
    missing = sorted(CLASSIFICATION_FIELDS - set(value))
    extra = sorted(set(value) - CLASSIFICATION_FIELDS)
    if missing or extra:
        raise ValidationError(
            f"{article_id}: classification schema mismatch; missing={missing}, extra={extra}"
        )

    for field, allowed in {
        "tone": set(TONE_VALUES),
        "tone_sentiment": set(SENTIMENT_VALUES),
        "event_type": set(EVENT_VALUES),
        "institutional_category": set(INSTITUTIONAL_CATEGORIES),
    }.items():
        if value[field] not in allowed:
            raise ValidationError(f"{article_id}: invalid {field}={value[field]!r}")
    for field in (
        "tone_confidence",
        "sentiment_confidence",
        "event_confidence",
        "metadata_confidence",
    ):
        require_confidence(article_id, value[field], field)

    for field in ("tone_evidence", "sentiment_evidence", "event_evidence"):
        excerpts = validate_string_list(article_id, value[field], field, maximum=3)
        for excerpt in excerpts:
            if excerpt not in source_text:
                raise ValidationError(
                    f"{article_id}: {field} excerpt is not a literal substring of the frozen input: "
                    f"{excerpt[:120]!r}"
                )

    tags = validate_string_list(article_id, value["issue_tags"], "issue_tags", maximum=8)
    unknown_tags = sorted(set(tags) - active_tags, key=str.casefold)
    if unknown_tags:
        raise ValidationError(f"{article_id}: issue_tags are not active Tag entities: {unknown_tags}")

    require_string(article_id, value["event_trigger"], "event_trigger", nonempty=True)
    require_string(article_id, value["outlet_name"], "outlet_name", nonempty=True)
    require_string(article_id, value["outlet_country"], "outlet_country")
    require_string(article_id, value["review_reason"], "review_reason")
    if not isinstance(value["review_required"], bool):
        raise ValidationError(f"{article_id}: review_required must be boolean")


def validate_review(
    review_path: Path,
    frozen_by_id: dict[str, dict[str, Any]],
    *,
    active_tags: set[str],
    eligible_path: Path | None = None,
) -> dict[str, Any]:
    payload = load_object(review_path)
    if payload.get("schemaVersion") != REVIEW_SCHEMA:
        raise ValidationError(
            f"{review_path}: schemaVersion must be {REVIEW_SCHEMA!r}"
        )
    rows = payload.get("assessments")
    if not isinstance(rows, list):
        raise ValidationError(f"{review_path}: assessments must be a list")
    expected_count = len(frozen_by_id)
    for field in ("inputCount", "assessedCount"):
        if payload.get(field) != expected_count:
            raise ValidationError(
                f"{review_path}: {field}={payload.get(field)!r}; expected {expected_count}"
            )
    if len(rows) != expected_count:
        raise ValidationError(
            f"{review_path}: assessment list has {len(rows)} rows; expected {expected_count}"
        )
    if eligible_path is not None and "manifestSha256" in payload:
        actual_manifest_sha = sha256_bytes(eligible_path.read_bytes())
        if payload["manifestSha256"] != actual_manifest_sha:
            raise ValidationError(f"{review_path}: manifestSha256 does not match eligible manifest")

    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValidationError(f"{review_path}: assessment row must be an object")
        article_id = require_string("assessment", row.get("articleId"), "articleId", nonempty=True)
        if article_id in seen:
            raise ValidationError(f"{review_path}: duplicate articleId {article_id}")
        seen.add(article_id)
        frozen = frozen_by_id.get(article_id)
        if frozen is None:
            raise ValidationError(f"{review_path}: unexpected articleId {article_id}")
        row_path = require_string(article_id, row.get("path"), "path", nonempty=True)
        if row_path != frozen["path"]:
            raise ValidationError(
                f"{article_id}: assessment path {row_path!r} does not match {frozen['path']!r}"
            )
        if "inputSha256" in row and row["inputSha256"] != frozen["sha256"]:
            raise ValidationError(f"{article_id}: assessment inputSha256 does not match frozen input")
        validate_classification(
            article_id,
            row.get("classification"),
            source_text=frozen["text"],
            active_tags=active_tags,
        )

    missing = sorted(set(frozen_by_id) - seen)
    if missing:
        raise ValidationError(f"{review_path}: missing article IDs: {missing[:10]}")
    return {
        "review": display_path(review_path),
        "valid": True,
        "articleCount": expected_count,
        "evidencePolicy": "literal-substring-of-sha256-verified-routed-input",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eligible-manifest", type=Path, required=True)
    parser.add_argument("--routable-manifest", type=Path, required=True)
    parser.add_argument("--review", type=Path, action="append", required=True)
    parser.add_argument("--expected-count", type=int, required=True)
    args = parser.parse_args()
    if args.expected_count <= 0:
        parser.error("--expected-count must be positive")

    eligible_path = args.eligible_manifest.resolve()
    frozen = load_frozen_inputs(
        eligible_path,
        args.routable_manifest.resolve(),
        expected_count=args.expected_count,
    )
    active_tags = {source for source, _radar, _count in active_inventory(TAG_ROOT)}
    if not active_tags:
        raise ValidationError("active Tag inventory is empty")
    results = [
        validate_review(path.resolve(), frozen, active_tags=active_tags, eligible_path=eligible_path)
        for path in args.review
    ]
    print(json.dumps({"valid": True, "expectedCount": args.expected_count, "reviews": results}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        raise SystemExit(1)
