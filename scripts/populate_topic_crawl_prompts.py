#!/usr/bin/env python3
"""Populate and validate executable NewsAPI.ai Crawl Prompt sections."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
TOPIC_ROOT = ROOT / "entities" / "topic"
TAXONOMY = ROOT / "topics" / "canonical-topics.yaml"
SYSTEM_FILES = {"index.md", "catalog.md", "log.md", "_template.md"}

DEFENCE_CONTEXT = "(defence OR defense OR military OR armed forces OR national security OR national service OR MINDEF OR SAF)"
SINGAPORE_CONTEXT = "(Singapore OR MINDEF OR SAF)"
NS_CONTEXT = "(Singapore OR national service OR NS OR NSF OR NSmen)"
REGIONAL_CONTEXT = "(security OR defence OR defense OR military OR conflict OR armed forces)"

# These prompts require a contextual guard because at least one taxonomy keyword is broad in normal
# news. Narrow, already-specific topics use their taxonomy expressions without an extra clause.
CONTEXT_BY_TOPIC = {
    "singapore-army": SINGAPORE_CONTEXT,
    "republic-of-singapore-navy": SINGAPORE_CONTEXT,
    "republic-of-singapore-air-force": SINGAPORE_CONTEXT,
    "defence-leadership-personnel": DEFENCE_CONTEXT,
    "enlistment-compliance": NS_CONTEXT,
    "defence-recruitment-workforce": DEFENCE_CONTEXT,
    "defence-procurement": DEFENCE_CONTEXT,
    "defence-ai-autonomy": DEFENCE_CONTEXT,
    "unmanned-systems-drones": DEFENCE_CONTEXT,
    "c4isr-sensors": DEFENCE_CONTEXT,
    "air-capabilities": DEFENCE_CONTEXT,
    "naval-capabilities": DEFENCE_CONTEXT,
    "land-capabilities": DEFENCE_CONTEXT,
    "space-defence": DEFENCE_CONTEXT,
    "defence-research-innovation": DEFENCE_CONTEXT,
    "missiles-air-defence": DEFENCE_CONTEXT,
    "military-logistics": DEFENCE_CONTEXT,
    "military-exercises": DEFENCE_CONTEXT,
    "operational-readiness": DEFENCE_CONTEXT,
    "border-territorial-security": REGIONAL_CONTEXT,
    "peacekeeping-humanitarian": "(military OR armed forces OR peacekeeping OR United Nations OR conflict OR disaster)",
    "evacuation-repatriation": "(Singapore OR military OR armed forces OR conflict OR crisis OR disaster)",
    "military-safety-incidents": DEFENCE_CONTEXT,
    "bilateral-defence-relations": DEFENCE_CONTEXT,
    "multilateral-defence-diplomacy": DEFENCE_CONTEXT,
    "great-power-competition": REGIONAL_CONTEXT,
    "korean-peninsula": REGIONAL_CONTEXT,
    "south-asia-security": REGIONAL_CONTEXT,
    "southeast-asia-security": REGIONAL_CONTEXT,
    "indo-pacific-security": REGIONAL_CONTEXT,
    "euro-atlantic-security": REGIONAL_CONTEXT,
    "americas-security": REGIONAL_CONTEXT,
    "middle-east-security": REGIONAL_CONTEXT,
    "iran-regional-conflict": REGIONAL_CONTEXT,
    "nuclear-security": REGIONAL_CONTEXT,
    "espionage-foreign-interference": REGIONAL_CONTEXT,
    "supply-chain-energy-security": REGIONAL_CONTEXT,
    "climate-water-security": REGIONAL_CONTEXT,
    "military-law-justice": DEFENCE_CONTEXT,
    "public-confidence-reputation": DEFENCE_CONTEXT,
    "civil-military-relations": DEFENCE_CONTEXT,
    "international-law-rules-order": REGIONAL_CONTEXT,
    "defence-cooperation-agreements": DEFENCE_CONTEXT,
    "emerging-weapons-technology": DEFENCE_CONTEXT,
}

# Regex-oriented taxonomy tokens are expanded into NewsAPI.ai-compatible phrases here. All other
# expressions are converted mechanically by ``newsapi_term``.
TERM_OVERRIDES = {
    r"\bdefen[cs]e\b": ["defence", "defense"],
    r"armou?r": ["armor", "armour"],
    r"armou?red vehicle": ["armored vehicle", "armoured vehicle"],
    r"united states.*singapore": ["United States NEAR/15 Singapore"],
    r"american.*singapore": ["American NEAR/15 Singapore"],
    r"chinese.*singapore": ["Chinese NEAR/15 Singapore"],
    r"singapore.*china": ["Singapore NEAR/15 China"],
    r"indian.*singapore": ["Indian NEAR/15 Singapore"],
    r"singapore.*india": ["Singapore NEAR/15 India"],
    r"taiwan.*china": ["Taiwan NEAR/15 China"],
    r"china.*taiwan": ["China NEAR/15 Taiwan"],
    r"russia.*war": ["Russia NEAR/15 war"],
    r"parliament.*military": ["parliament NEAR/15 military"],
    r"government.*military": ["government NEAR/15 military"],
    r"armed forces.*public": ["armed forces NEAR/15 public"],
    r"national day.*saf": ["national day NEAR/15 SAF"],
    r"canada.*security": ["Canada NEAR/15 security"],
    "palestin": ["Palestine", "Palestinian"],
    "radicalis": ["radicalisation", "radicalization", "radicalised", "radicalized"],
    "extremis": ["extremism", "extremist", "extremists"],
}

PROMPT_OVERRIDES = {
    "general-defence-security": "(defence OR defense OR military OR armed forces OR national security)",
}


class PromptError(RuntimeError):
    pass


def load_topics() -> list[dict[str, Any]]:
    payload = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8"))
    topics = payload.get("topics") if isinstance(payload, dict) else None
    if not isinstance(topics, list):
        raise PromptError("canonical taxonomy has no topics list")
    return topics


def newsapi_term(value: str) -> list[str]:
    if value in TERM_OVERRIDES:
        return TERM_OVERRIDES[value]
    value = value.replace(r"\b", "").strip()
    if ".*" in value:
        left, right = value.split(".*", 1)
        value = f"{left.strip()} NEAR/15 {right.strip()}"
    if "?" in value or "\\" in value:
        raise PromptError(f"unconverted regex token: {value!r}")
    return [value]


def build_prompt(topic: dict[str, Any]) -> str:
    if topic["topicId"] in PROMPT_OVERRIDES:
        return PROMPT_OVERRIDES[topic["topicId"]]
    expressions = []
    for keyword in topic.get("keywords") or []:
        expressions.extend(newsapi_term(str(keyword)))
    # Preserve order while removing case-insensitive duplicates.
    unique = []
    seen = set()
    for expression in expressions:
        key = expression.casefold()
        if expression and key not in seen:
            seen.add(key)
            unique.append(expression)
    if not unique:
        raise PromptError(f"topic has no crawl terms: {topic['topicId']}")
    subject = "(" + " OR ".join(unique) + ")"
    context = CONTEXT_BY_TOPIC.get(topic["topicId"])
    return f"{subject} AND {context}" if context else subject


def replace_prompt(text: str, prompt: str) -> str:
    section = f"## Crawl Prompt\n```text\n{prompt}\n```\n"
    pattern = re.compile(r"(?ms)^## Crawl Prompt\s*\n.*?(?=^## |\Z)")
    matches = list(pattern.finditer(text))
    if len(matches) > 1:
        raise PromptError("note contains duplicate Crawl Prompt sections")
    if matches:
        return pattern.sub(lambda _: section + "\n", text, count=1).rstrip() + "\n"
    coverage = re.search(r"(?m)^## Coverage\s*$", text)
    if not coverage:
        raise PromptError("note lacks Coverage section")
    return (text[:coverage.start()].rstrip() + "\n\n" + section + "\n" + text[coverage.start():]).rstrip() + "\n"


def topic_paths() -> list[Path]:
    return sorted(path for path in TOPIC_ROOT.glob("*.md") if path.name not in SYSTEM_FILES)


def validate_prompt(prompt: str) -> None:
    if not prompt or "\\b" in prompt or ".*" in prompt or "?" in prompt:
        raise PromptError(f"prompt contains regex or is empty: {prompt!r}")
    if prompt.count("(") != prompt.count(")"):
        raise PromptError(f"prompt parentheses are unbalanced: {prompt!r}")
    if len(prompt) > 2_000:
        raise PromptError("prompt exceeds the 2,000-character safety limit")


def apply_prompts(dry_run: bool) -> dict[str, Any]:
    topics = load_topics()
    by_id = {row["topicId"]: row for row in topics}
    paths = topic_paths()
    ids = {path.stem for path in paths}
    if ids != set(by_id):
        raise PromptError(f"active topic IDs differ from taxonomy: missing={sorted(set(by_id)-ids)}, extra={sorted(ids-set(by_id))}")
    changed = 0
    changed_topics = []
    for path in paths:
        prompt = build_prompt(by_id[path.stem])
        validate_prompt(prompt)
        before = path.read_text(encoding="utf-8")
        after = replace_prompt(before, prompt)
        if after != before:
            changed += 1
            changed_topics.append((path.stem, by_id[path.stem]["displayName"]))
            if not dry_run:
                path.write_text(after, encoding="utf-8")
    if changed_topics and not dry_run:
        timestamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        with (TOPIC_ROOT / "log.md").open("a", encoding="utf-8") as handle:
            for topic_id, display_name in changed_topics:
                handle.write(
                    f"- {timestamp} | source: [[add-newsapi-crawl-prompts-to-canonical-topics]] | "
                    f"entity: [[{topic_id}|{display_name}]] | action: added — executable NewsAPI.ai "
                    "`## Crawl Prompt` derived from the accepted canonical taxonomy | reasoning: "
                    "make each topic a self-contained crawler definition.\n"
                )
    return {"topics": len(paths), "changed": changed, "dryRun": dry_run}


def check() -> dict[str, Any]:
    topics = load_topics()
    expected = {row["topicId"]: build_prompt(row) for row in topics}
    failures = []
    for path in topic_paths():
        text = path.read_text(encoding="utf-8")
        matches = re.findall(r"(?ms)^## Crawl Prompt\s*\n```text\n(.*?)\n```\s*(?=^## |\Z)", text)
        if len(matches) != 1:
            failures.append(f"{path.name}: expected one fenced Crawl Prompt, found {len(matches)}")
            continue
        try:
            validate_prompt(matches[0])
        except PromptError as exc:
            failures.append(f"{path.name}: {exc}")
        if matches[0] != expected.get(path.stem):
            failures.append(f"{path.name}: Crawl Prompt differs from canonical derivation")
    if len(topic_paths()) != len(expected):
        failures.append("active topic count differs from canonical taxonomy")
    if failures:
        raise PromptError("; ".join(failures[:20]))
    return {"topics": len(expected), "validPrompts": len(expected), "failures": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.apply:
            print(json.dumps(apply_prompts(dry_run=False), indent=2))
        elif args.check:
            print(json.dumps(check(), indent=2))
        else:
            print(json.dumps(apply_prompts(dry_run=True), indent=2))
        return 0
    except (PromptError, OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
