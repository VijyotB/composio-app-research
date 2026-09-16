"""Clustering, pattern extraction, and accuracy scoring.

Two jobs:

  analyze()  - count everything the page needs. Pure arithmetic over the enums,
               so a pattern on the page is reproducible, not a model's opinion
               about its own output.

  score()    - compare v1 and v2 against data/human_sample.json, the rows a
               human checked by hand. Per-field agreement, reported honestly
               including the fields where the repair loop made things worse.

Run:
    python -m src.analyze
    python -m src.analyze --make-sample 20     # emit the stratified sample to check
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from .app_list import APPS, CATEGORIES, slug
from .schema import SCORED_FIELDS

ROOT = Path(__file__).resolve().parent
V1, V2 = ROOT / "results" / "v1", ROOT / "results" / "v2"
DATA = ROOT.parent / "data"
DATA.mkdir(exist_ok=True)
SAMPLE = DATA / "human_sample.json"


def load(d: Path) -> dict:
    out = {}
    for p in sorted(d.glob("*.json")):
        try:
            r = json.loads(p.read_text())
            out[r["app"]] = r
        except Exception:
            pass
    return out


# --------------------------------------------------------------------------

def analyze(recs: dict) -> dict:
    rows = list(recs.values())
    n = len(rows) or 1

    auth = Counter(m for r in rows for m in r.get("auth_methods", []))
    tier = Counter(r.get("access_tier") for r in rows)
    verdict = Counter(r.get("verdict") for r in rows)
    blocker = Counter(r.get("blocker") for r in rows)
    mcp = Counter(r.get("mcp_status") for r in rows)
    api = Counter(t for r in rows for t in r.get("api_types", []))
    breadth = Counter(r.get("api_breadth") for r in rows)

    by_cat = defaultdict(lambda: {"n": 0, "self_serve": 0, "gated": 0,
                                  "build_now": 0, "needs_outreach": 0,
                                  "mcp": 0, "auth": Counter()})
    for r in rows:
        c = by_cat[r["category"]]
        c["n"] += 1
        if str(r.get("access_tier", "")).startswith("self_serve"):
            c["self_serve"] += 1
        if r.get("access_tier") in ("partner_gated", "app_review", "admin_approval", "no_public_api"):
            c["gated"] += 1
        if r.get("verdict") == "build_now":
            c["build_now"] += 1
        if r.get("verdict") == "needs_outreach":
            c["needs_outreach"] += 1
        if r.get("mcp_status") in ("official", "community"):
            c["mcp"] += 1
        for m in r.get("auth_methods", []):
            c["auth"][m] += 1

    cats = []
    for name in CATEGORIES:
        c = by_cat.get(name)
        if not c:
            continue
        cats.append({
            "category": name,
            "n": c["n"],
            "self_serve": c["self_serve"],
            "gated": c["gated"],
            "build_now": c["build_now"],
            "needs_outreach": c["needs_outreach"],
            "mcp": c["mcp"],
            "self_serve_pct": round(100 * c["self_serve"] / c["n"]),
            "dominant_auth": c["auth"].most_common(1)[0][0] if c["auth"] else "unknown",
        })

    # Cross-tab: does auth method predict gating?
    auth_vs_gate = defaultdict(lambda: {"self_serve": 0, "gated": 0})
    for r in rows:
        bucket = "self_serve" if str(r.get("access_tier", "")).startswith("self_serve") else "gated"
        for m in r.get("auth_methods", []):
            auth_vs_gate[m][bucket] += 1

    return {
        "n": len(rows),
        "auth": auth.most_common(),
        "access_tier": tier.most_common(),
        "verdict": verdict.most_common(),
        "blocker": blocker.most_common(),
        "mcp": mcp.most_common(),
        "api_types": api.most_common(),
        "api_breadth": breadth.most_common(),
        "categories": cats,
        "auth_vs_gate": {k: v for k, v in auth_vs_gate.items()},
        "pct": {
            "self_serve": round(100 * sum(1 for r in rows if str(r.get("access_tier", "")).startswith("self_serve")) / n),
            "build_now": round(100 * verdict.get("build_now", 0) / n),
            "needs_outreach": round(100 * verdict.get("needs_outreach", 0) / n),
            "any_mcp": round(100 * (mcp.get("official", 0) + mcp.get("community", 0)) / n),
            "official_mcp": round(100 * mcp.get("official", 0) / n),
        },
    }


# --------------------------------------------------------------------------

def make_sample(k: int = 20, seed: int = 7) -> list:
    """Stratified: two per category, so the accuracy number is not dominated by
    whichever category happened to be easiest."""
    rng = random.Random(seed)
    per = max(1, k // len(CATEGORIES))
    chosen = []
    for cat in CATEGORIES:
        pool = [a for a in APPS if a[1] == cat]
        chosen += rng.sample(pool, min(per, len(pool)))
    rows = [{"app": n, "category": c, "slug": slug(n),
             "truth": {f: None for f in SCORED_FIELDS},
             "source_url": "", "checked_by": "", "note": ""}
            for n, c, _h in chosen]
    SAMPLE.write_text(json.dumps(rows, indent=2))
    print(f"wrote {len(rows)} rows to {SAMPLE}")
    print("Fill in `truth` for each row by reading the real docs, then rerun analyze.")
    return rows


def _agree(truth, got) -> bool:
    if truth is None:
        return None
    if isinstance(truth, list) or isinstance(got, list):
        return set(truth or []) == set(got or [])
    return truth == got


def score(v1: dict, v2: dict) -> dict:
    if not SAMPLE.exists():
        return {"available": False}
    sample = json.loads(SAMPLE.read_text())
    out = {"available": True, "n_sampled": len(sample), "fields": {}, "rows": []}
    tally = {f: {"v1": [0, 0], "v2": [0, 0]} for f in SCORED_FIELDS}

    for row in sample:
        app = row["app"]
        r1, r2 = v1.get(app), v2.get(app)
        row_out = {"app": app, "category": row["category"], "fields": {},
                   "source_url": row.get("source_url", ""), "note": row.get("note", "")}
        for f in SCORED_FIELDS:
            truth = row["truth"].get(f)
            if truth is None:
                continue
            a1 = _agree(truth, (r1 or {}).get(f))
            a2 = _agree(truth, (r2 or {}).get(f))
            tally[f]["v1"][1] += 1
            tally[f]["v2"][1] += 1
            tally[f]["v1"][0] += int(bool(a1))
            tally[f]["v2"][0] += int(bool(a2))
            row_out["fields"][f] = {
                "truth": truth,
                "v1": (r1 or {}).get(f), "v1_ok": a1,
                "v2": (r2 or {}).get(f), "v2_ok": a2,
                "regressed": bool(a1) and not bool(a2),
            }
        if row_out["fields"]:
            out["rows"].append(row_out)

    tot1 = tot2 = den = 0
    for f, t in tally.items():
        if t["v1"][1] == 0:
            continue
        out["fields"][f] = {
            "n": t["v1"][1],
            "v1_pct": round(100 * t["v1"][0] / t["v1"][1]),
            "v2_pct": round(100 * t["v2"][0] / t["v2"][1]),
        }
        tot1 += t["v1"][0]; tot2 += t["v2"][0]; den += t["v1"][1]
    if den:
        out["overall"] = {"n": den,
                          "v1_pct": round(100 * tot1 / den),
                          "v2_pct": round(100 * tot2 / den),
                          "delta": round(100 * (tot2 - tot1) / den)}
    out["regressions"] = [
        {"app": r["app"], "field": f}
        for r in out["rows"] for f, d in r["fields"].items() if d["regressed"]
    ]
    return out


def validation_stats(v1: dict, v2: dict) -> dict:
    def ok(d):
        vals = [r.get("validation", {}).get("ok") for r in d.values()]
        return round(100 * sum(1 for v in vals if v) / max(1, len(vals)))
    err = Counter()
    for r in v1.values():
        for e in r.get("validation", {}).get("errors", []):
            key = e.split(":")[0].split(" not found")[0].strip()
            err[key] += 1
    return {
        "v1_clean_pct": ok(v1),
        "v2_clean_pct": ok(v2),
        "repairs_run": sum(r.get("repair_attempts", 0) for r in v2.values()),
        "top_v1_errors": err.most_common(8),
        "still_failing": [r["app"] for r in v2.values() if not r.get("validation", {}).get("ok")],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-sample", type=int, default=0)
    args = ap.parse_args()
    if args.make_sample:
        make_sample(args.make_sample)
        return

    v1, v2 = load(V1), load(V2)
    bundle = {
        "patterns": analyze(v2),
        "accuracy": score(v1, v2),
        "validation": validation_stats(v1, v2),
        "apps": sorted(v2.values(), key=lambda r: (r["category"], r["app"])),
    }
    (DATA / "bundle.json").write_text(json.dumps(bundle, indent=2))
    print(json.dumps({k: v for k, v in bundle.items() if k != "apps"}, indent=2)[:3000])
    print(f"\nwrote {DATA/'bundle.json'} ({len(bundle['apps'])} apps)")


if __name__ == "__main__":
    main()
