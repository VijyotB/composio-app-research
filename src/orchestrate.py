"""Orchestrator.

Run:
    python -m src.orchestrate --limit 5          # smoke test
    python -m src.orchestrate                    # all 100
    python -m src.orchestrate --app Stripe --app Ramp

Both passes are written to disk under separate directories:

    src/results/v1/<slug>.json   first-pass answer, before any repair
    src/results/v2/<slug>.json   answer after validation + targeted repair

Keeping v1 is not bookkeeping. The assignment asks us to show accuracy moving
from a lower first pass to a higher one, and you cannot show that if the repair
loop has already overwritten the thing you would be measuring against. This is
the one decision in the pipeline that is easy to get wrong and impossible to
fix afterwards.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .app_list import APPS, slug
from .research import research
from .validate import repair_queries, validate

ROOT = Path(__file__).resolve().parent
V1 = ROOT / "results" / "v1"
V2 = ROOT / "results" / "v2"
for d in (V1, V2):
    d.mkdir(parents=True, exist_ok=True)

MAX_REPAIRS = 2


def run_one(name: str, category: str, hint: str, force: bool = False) -> dict:
    s = slug(name)
    if not force and (V2 / f"{s}.json").exists():
        return json.loads((V2 / f"{s}.json").read_text())

    t0 = time.time()

    # ---- pass 1 -----------------------------------------------------------
    rec, corpus = research(name, category, hint)
    validate(rec, corpus)
    rec["pass"] = "v1"
    rec["elapsed_s"] = round(time.time() - t0, 1)
    (V1 / f"{s}.json").write_text(json.dumps(rec, indent=2))
    first_ok = rec["validation"]["ok"]

    # ---- pass 2: targeted repair -----------------------------------------
    attempt = 0
    while not rec["validation"]["ok"] and attempt < MAX_REPAIRS:
        attempt += 1
        extra = repair_queries(rec)
        repaired, corpus2 = research(
            name, category, hint,
            repair={"errors": rec["validation"]["errors"], "record": rec},
            extra_queries=extra,
        )
        corpus = {d["url"]: d for d in corpus + corpus2}.values()
        corpus = list(corpus)
        validate(repaired, corpus)
        # Only accept the repair if it is strictly less broken.
        if len(repaired["validation"]["errors"]) < len(rec["validation"]["errors"]):
            rec = repaired
        if rec["validation"]["ok"]:
            break

    rec["pass"] = "v2"
    rec["repair_attempts"] = attempt
    rec["first_pass_valid"] = first_ok
    rec["elapsed_s"] = round(time.time() - t0, 1)
    rec.pop("_corpus_urls", None)
    (V2 / f"{s}.json").write_text(json.dumps(rec, indent=2))

    flag = "ok " if rec["validation"]["ok"] else "FAIL"
    print(f"[{flag}] {name:<28} repairs={attempt} "
          f"errors={len(rec['validation']['errors'])} {rec['elapsed_s']}s")
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", action="append", default=[])
    ap.add_argument("--category", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    targets = APPS
    if args.app:
        wanted = {a.lower() for a in args.app}
        targets = [t for t in targets if t[0].lower() in wanted]
    if args.category:
        targets = [t for t in targets if args.category.lower() in t[1].lower()]
    if args.limit:
        targets = targets[: args.limit]

    print(f"researching {len(targets)} apps with {args.workers} workers\n")
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, n, c, h, args.force): n for n, c, h in targets}
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as exc:
                print(f"[ERR ] {futures[fut]}: {exc}")
            done += 1
            if done % 10 == 0:
                print(f"  ... {done}/{len(targets)}")

    print("\ndone. next: python -m src.analyze && python -m src.build_page")


if __name__ == "__main__":
    main()
