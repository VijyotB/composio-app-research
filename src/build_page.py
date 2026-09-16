"""Inject data/bundle.json into the template and write index.html.

The page holds no hand-typed numbers. Everything it displays comes from the
bundle, which comes from the JSON checkpoints, which come from the run. If a
number on the page looks wrong, there is exactly one place to go and look.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "index.html"
TEMPLATE = ROOT / "page_template.html"
BUNDLE = ROOT.parent / "data" / "bundle.json"
SAMPLE = ROOT.parent / "data" / "bundle.sample.json"

# Fields the page never reads — dropped so the HTML stays small.
DROP = {"hint", "elapsed_s", "_corpus_urls", "human_checked", "pass"}


def slim(app: dict) -> dict:
    out = {k: v for k, v in app.items() if k not in DROP}
    val = out.get("validation") or {}
    out["validation"] = {"ok": val.get("ok"), "errors": (val.get("errors") or [])[:3]}
    out["evidence"] = [
        {"url": e.get("url"), "excerpt": (e.get("excerpt") or "")[:300],
         "supports": e.get("supports", [])}
        for e in (out.get("evidence") or [])[:4]
    ]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getenv("REPO_URL", "#"))
    ap.add_argument("--author", default=os.getenv("AUTHOR", ""))
    ap.add_argument("--allow-sample", action="store_true",
                    help="build from data/bundle.sample.json (synthetic, watermarked)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out_path = Path(args.out) if args.out else OUT
    src = SAMPLE if args.allow_sample else BUNDLE
    globals()["BUNDLE"] = src

    if not BUNDLE.exists():
        print(f"no {BUNDLE} yet — building the empty-state page")
        bundle = {"apps": [], "patterns": None, "accuracy": None, "validation": None}
    else:
        bundle = json.loads(BUNDLE.read_text())
        bundle["apps"] = [slim(a) for a in bundle.get("apps", [])]

    meta = {
        "repo": args.repo,
        "author": args.author,
        "built": dt.date.today().isoformat(),
        "sample": bool(bundle.get("sample")),
    }

    html = TEMPLATE.read_text()
    html = html.replace("/*__DATA__*/null", json.dumps(bundle, separators=(",", ":")))
    html = html.replace(
        '/*__META__*/{repo:"#", live:"#", author:"", built:""}',
        json.dumps(meta, separators=(",", ":")),
    )
    out_path.write_text(html)
    kb = out_path.stat().st_size / 1024
    print(f"wrote {out_path} ({kb:.0f} KB, {len(bundle.get('apps', []))} apps)"
          + (" [SYNTHETIC SAMPLE]" if meta["sample"] else ""))


if __name__ == "__main__":
    main()
