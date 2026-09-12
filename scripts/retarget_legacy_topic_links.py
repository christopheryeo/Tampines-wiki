#!/usr/bin/env python3
"""Repoint entity-note wikilinks that still name a retired pre-consolidation topic.

Background
----------
``entities/decisions/consolidate-topics-to-ai-controlled-taxonomy.md`` replaced
the 8,895-note mechanical Topic Entity with a bounded canonical vocabulary and
moved every retired note to ``archive/topic-legacy/<bundle>/``. Article notes
were migrated, but entity notes in the other domains still carry links written
by the pre-consolidation cascade — overwhelmingly the trailing
``Related topic: [[defence]]`` line the cascade appended to almost every note.

Those links are not "broken" (check_links.py resolves them against the archive)
but they point out of the active vocabulary, so a reader following them lands in
a frozen archive rather than the canonical topic that now owns the coverage.

What this does
--------------
Rewrites each listed legacy target to its canonical successor in the piped
``[[topic/<canonical>|Display Name]]`` form the vault standardises on. Only the
targets in MAPPING are touched; anything else is left exactly as it is. Article
notes are skipped (already migrated, and their audit blocks are frozen
evidence), as are append-only ``log.md`` ledgers.

Every mapping below is the canonical topic the consolidation assigned to that
strand's own articles, or — where the retired note was an event/programme rather
than a theme — the canonical theme that now carries it.

Usage:
  python3 scripts/retarget_legacy_topic_links.py --dry-run
  python3 scripts/retarget_legacy_topic_links.py
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTITIES = ROOT / "entities"

# retired topicId -> (canonical topicId, canonical displayName)
MAPPING: dict[str, tuple[str, str]] = {
    "defence": ("general-defence-security", "General Defence and Security"),
    "ai-in-defence": ("defence-ai-autonomy", "Defence AI and Autonomy"),
    "defence-collective-festival": ("national-resilience-total-defence", "National Resilience and Total Defence"),
    "ex-cope-tiger": ("military-exercises", "Military Exercises"),
    "ex-panzer-strike": ("military-exercises", "Military Exercises"),
    "ex-wallaby-2025": ("military-exercises", "Military Exercises"),
    "navy-vivo-2025": ("military-exercises", "Military Exercises"),
    "operation-epic-fury": ("military-exercises", "Military Exercises"),
    "operation-thunderbolt": ("counterterrorism-operations", "Counterterrorism Operations"),
    "home-affairs": ("mindef-governance", "MINDEF Governance"),
    "imdex-asia-2025": ("defence-industry", "Defence Industry"),
    "sa26": ("singapore-airshow", "Singapore Airshow"),
    "iran-war": ("iran-regional-conflict", "Iran and Regional Conflict"),
    "medical-classification-system": ("ns-safety-wellbeing", "NS Safety and Wellbeing"),
    "ns-bullying-harassment": ("ns-safety-wellbeing", "NS Safety and Wellbeing"),
    "ns-allowance-debate": ("national-service-policy", "National Service Policy"),
    "ns-enlistment-evasion": ("enlistment-compliance", "Enlistment Compliance"),
    "pofma": ("disinformation-information-warfare", "Disinformation and Information Warfare"),
    "sgsecure": ("national-resilience-total-defence", "National Resilience and Total Defence"),
    "rmaf": ("air-capabilities", "Air Capabilities"),
    "uav": ("unmanned-systems-drones", "Unmanned Systems and Drones"),
}

# Domains whose notes the pre-consolidation cascade wrote topic links into.
# entities/article is excluded: its topic links were migrated by the
# consolidation and its audit blocks are preserved source evidence.
DOMAINS = (
    "appointments", "country", "decisions", "issues",
    "organisations", "outlet", "people", "place", "search", "topic",
)

LINK = re.compile(r"\[\[([^|\]\n]+)(?:\|([^\]\n]*))?\]\]")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    canonical_exists = {
        target for target, _ in MAPPING.values()
        if (ENTITIES / "topic" / f"{target}.md").exists()
    }
    unknown = {t for t, _ in MAPPING.values()} - canonical_exists
    if unknown:
        print(f"ERROR: canonical topic notes missing: {sorted(unknown)}")
        return 2

    files = 0
    rewrites = 0
    for domain in DOMAINS:
        for path in sorted((ENTITIES / domain).rglob("*.md")):
            # log.md is an append-only ledger; index.md is the hand-maintained
            # operating manual and its wikilinks are format EXAMPLES, not real
            # references (e.g. "[[ex-wallaby-2025|Ex Wallaby 2025]]" illustrating
            # the piped form). Rewriting either would be wrong.
            if path.name in {"log.md", "index.md"}:
                continue
            original = path.read_text(encoding="utf-8")
            changed = 0

            def repl(match: re.Match) -> str:
                nonlocal changed
                target = match.group(1).strip()
                if target not in MAPPING:
                    return match.group(0)
                canonical, display = MAPPING[target]
                changed += 1
                return f"[[topic/{canonical}|{match.group(2) or display}]]"

            text = LINK.sub(repl, original)
            if not changed:
                continue
            files += 1
            rewrites += changed
            print(f"{path.relative_to(ROOT)}: {changed}")
            if not args.dry_run:
                path.write_text(text, encoding="utf-8")

    label = "DRY RUN -- nothing written" if args.dry_run else "APPLIED"
    print(f"\n=== {label} === files={files} rewrites={rewrites}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
