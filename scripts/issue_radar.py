#!/usr/bin/env python3
"""
issue_radar.py — prototype early-warning issue radar over index/wiki.db.

Detects *percolating issues*: coverage clusters whose structure (recurrence,
breadth expansion, institutional attachment, acceleration, unfacilitated share)
indicates rising blow-up risk — before volume peaks.

Unit of analysis (prototype): normalised article tags, filtered to exclude
generic vault-wide tags. The production design clusters story-level topics into
issue objects via agent judgment; tags are the closest deterministic proxy.

Signals per issue, computed strictly from data on or before --asof:
  velocity/acceleration  articles in last 28d vs prior 28d
  breadth expansion      outlets/countries seen in last 28d but never before
  institutional attach.  share of recent coverage in institutional categories
                         (MINDEF, SAF, Parliament, COS Debate, National Service,
                         National Security, Chan Chun Sing, DSO/DSTA) + its rise
  recurrence             distinct coverage waves separated by >=2 silent weeks
  unfacilitated share    coverage NOT initiated by comms (eventType)
  opinionated share      tone == Opinionated

Every flag is explainable: the report lists which signals fired and why.

Usage:
  python3 issue_radar.py [--db path/to/wiki.db]     # as of latest article
  python3 issue_radar.py --asof 2026-02-02          # historical run (backtest)
  python3 issue_radar.py --issue "amos yee"         # weekly series for one issue
  python3 issue_radar.py --top 15 --min-tier WATCH

Read-only: never writes to the vault. Requires only stdlib.
"""
import argparse, collections, datetime, json, sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "index" / "wiki.db"

INSTITUTIONAL = {"MINDEF", "SAF", "Parliament", "COS Debate", "National Service",
                 "National Security", "Chan Chun Sing", "DSO/DSTA"}
# Tags too generic to be an "issue" (vault-wide framing vocabulary).
STOP = {"saf", "mindef", "defence", "defense", "security", "singapore", "military",
        "exercise", "training", "army", "navy", "air force", "rsaf", "rsn", "ns",
        "nsf", "nsmen", "soldier", "soldiers", "minister", "government", "asean",
        "china", "us", "usa", "united states", "war", "conflict", "sea", "camp"}
GENERIC_FRACTION = 0.03   # tags in >3% of corpus are framing, not issues
MIN_ARTICLES, MIN_WEEKS = 8, 3
WINDOW = 28               # days per comparison window

WEIGHTS = dict(accel=0.25, breadth=0.20, inst=0.25, recur=0.15, unfac=0.10, opin=0.05)
TIERS = [("HOT", 0.60, 8), ("WARM", 0.40, 4), ("WATCH", 0.25, 2)]  # (name, score, min recent vol)


def monday(d): return d - datetime.timedelta(days=d.weekday())


def load_articles(db):
    cur = sqlite3.connect(db).cursor()
    rows = cur.execute("""select articleTitle, publishedDate, category, tags,
                          outlets, countries, tone, eventType from article
                          where publishedDate is not null""").fetchall()
    arts = []
    for title, pd, cat, tags, outlets, countries, tone, etype in rows:
        try:
            d = datetime.datetime.fromisoformat(pd).date()
        except ValueError:
            continue
        arts.append(dict(
            title=title or "", date=d, cat=cat or "",
            tags={t.strip().lower() for t in (json.loads(tags) if tags else [])},
            outlets=set(json.loads(outlets) if outlets else []),
            countries=set(json.loads(countries) if countries else []),
            unfac=(etype == "Unfacilitated"), opin=(tone == "Opinionated")))
    return arts


def candidates(arts):
    freq = collections.Counter(t for a in arts for t in a["tags"])
    cap = len(arts) * GENERIC_FRACTION
    out = {}
    for tag, n in freq.items():
        if n < MIN_ARTICLES or n > cap or tag in STOP or len(tag) < 3:
            continue
        sel = [a for a in arts if tag in a["tags"]]
        if len({monday(a["date"]) for a in sel}) >= MIN_WEEKS:
            out[tag] = sel
    return out


def waves(dates, asof):
    """Count coverage waves: runs of active weeks separated by >=2 silent weeks."""
    wks = sorted({monday(d) for d in dates if d <= asof})
    if not wks:
        return 0
    n, prev = 1, wks[0]
    for w in wks[1:]:
        if (w - prev).days > 14:
            n += 1
        prev = w
    return n


def score_issue(sel, asof):
    hist = [a for a in sel if a["date"] <= asof]
    if not hist:
        return None
    r0, p0 = asof - datetime.timedelta(days=WINDOW), asof - datetime.timedelta(days=2 * WINDOW)
    recent = [a for a in hist if a["date"] > r0]
    prior = [a for a in hist if p0 < a["date"] <= r0]
    before = [a for a in hist if a["date"] <= r0]
    if not recent:
        return None

    v_r, v_p = len(recent), len(prior)
    accel = min(1.0, (v_r / max(v_p, 1)) / 4.0) if v_r >= 3 else 0.0

    seen_out = set().union(*[a["outlets"] for a in before]) if before else set()
    seen_cty = set().union(*[a["countries"] for a in before]) if before else set()
    new_out = set().union(*[a["outlets"] for a in recent]) - seen_out
    new_cty = set().union(*[a["countries"] for a in recent]) - seen_cty
    breadth = min(1.0, len(new_out) / 10.0 + len(new_cty) / 4.0) if before else 0.3

    inst_r = sum(a["cat"] in INSTITUTIONAL for a in recent) / v_r
    inst_b = (sum(a["cat"] in INSTITUTIONAL for a in before) / len(before)) if before else 0.0
    inst = min(1.0, inst_r * 0.6 + max(0.0, inst_r - inst_b) * 0.8)

    w = waves([a["date"] for a in hist], asof)
    recur = min(1.0, (w - 1) / 3.0)

    unfac = sum(a["unfac"] for a in recent) / v_r
    opin = sum(a["opin"] for a in recent) / v_r

    parts = dict(accel=accel, breadth=breadth, inst=inst, recur=recur, unfac=unfac, opin=opin)
    score = sum(WEIGHTS[k] * v for k, v in parts.items())

    tier = None
    for name, smin, vmin in TIERS:
        if score >= smin and v_r >= vmin:
            tier = name
            break
    why = []
    if accel > 0.3: why.append(f"volume {v_p}->{v_r} over two {WINDOW}d windows")
    if new_out: why.append(f"{len(new_out)} never-seen outlets")
    if new_cty: why.append(f"new countries: {', '.join(sorted(new_cty)[:4])}")
    if inst_r > 0.3: why.append(f"{inst_r:.0%} of recent coverage in institutional categories")
    if inst_r - inst_b > 0.2 and before: why.append(f"institutional share rose {inst_b:.0%}->{inst_r:.0%}")
    if w >= 2: why.append(f"{w} distinct coverage waves (recurring, not dying)")
    if unfac > 0.7: why.append(f"{unfac:.0%} unfacilitated (story running on its own)")
    if opin > 0.15: why.append(f"{opin:.0%} opinionated pieces")
    return dict(score=score, tier=tier, vol=v_r, parts=parts, why=why)


def series(sel, asof):
    wk = collections.defaultdict(lambda: [0, set(), set()])
    for a in sel:
        if a["date"] > asof:
            continue
        b = wk[monday(a["date"]).isoformat()]
        b[0] += 1; b[1] |= a["outlets"]; b[2] |= a["countries"]
    return {w: (n, len(o), len(c)) for w, (n, o, c) in sorted(wk.items())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--asof")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--issue")
    ap.add_argument("--min-tier", default="WATCH", choices=[t[0] for t in TIERS])
    args = ap.parse_args()

    arts = load_articles(args.db)
    asof = datetime.date.fromisoformat(args.asof) if args.asof else max(a["date"] for a in arts)

    if args.issue:
        sel = [a for a in arts if args.issue.lower() in a["tags"]
               or args.issue.lower() in (a["title"] + " ").lower()]
        print(f"# series for '{args.issue}' as of {asof}  ({len(sel)} articles)")
        for w, (n, o, c) in series(sel, asof).items():
            print(f"{w}  vol={n:<4} outlets={o:<4} countries={c}")
        r = score_issue(sel, asof)
        if r:
            print(f"\nscore={r['score']:.2f} tier={r['tier']}  " + "; ".join(r["why"]))
        return

    ranked = []
    for tag, sel in candidates(arts).items():
        r = score_issue(sel, asof)
        if r and r["tier"]:
            ranked.append((tag, r))
    order = {t[0]: i for i, t in enumerate(TIERS)}
    keep = order[args.min_tier]
    ranked = [x for x in ranked if order[x[1]["tier"]] <= keep]
    ranked.sort(key=lambda x: -x[1]["score"])

    print(f"# Issue radar as of {asof}  ({len(ranked)} flagged, showing top {args.top})\n")
    for tag, r in ranked[: args.top]:
        print(f"[{r['tier']:<5}] {r['score']:.2f}  {tag}  (vol {r['vol']}/28d)")
        for w in r["why"]:
            print(f"         - {w}")
    if not ranked:
        print("nothing flagged")


if __name__ == "__main__":
    main()
