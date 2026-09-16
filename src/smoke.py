"""Generate a SYNTHETIC bundle so the page can be checked without API keys.

This exists to test rendering, nothing else. The numbers are made up. Anything
built from it is watermarked, and `python -m src.build_page` will refuse to
write index.html from a sample bundle unless you pass --allow-sample.

    python -m src.smoke && python -m src.build_page --allow-sample --out preview.html
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from .analyze import analyze
from .app_list import APPS, slug
from .schema import ACCESS_TIERS, AUTH_METHODS, BLOCKERS, blank

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)

TIER_BY_CAT = {
    "CRM and Sales": ["self_serve_free", "self_serve_paid", "partner_gated"],
    "Support and Helpdesk": ["self_serve_free", "self_serve_paid", "admin_approval"],
    "Communications and Messaging": ["self_serve_free", "app_review", "self_serve_paid"],
    "Marketing, Ads, Email and Social": ["app_review", "partner_gated", "self_serve_free"],
    "Ecommerce": ["self_serve_free", "app_review", "partner_gated"],
    "Data, SEO and Scraping": ["self_serve_paid", "self_serve_free"],
    "Developer, Infra and Data platforms": ["self_serve_free", "self_serve_free", "self_serve_paid"],
    "Productivity and Project Management": ["self_serve_free", "admin_approval"],
    "Finance and Fintech": ["self_serve_free", "partner_gated", "app_review"],
    "AI, Research and Media-native": ["self_serve_paid", "partner_gated", "no_public_api"],
}
VERDICT_BY_TIER = {
    "self_serve_free": "build_now", "self_serve_paid": "build_with_care",
    "admin_approval": "build_with_care", "app_review": "build_with_care",
    "partner_gated": "needs_outreach", "no_public_api": "not_buildable",
    "unknown": "unknown",
}
BLOCKER_BY_TIER = {
    "self_serve_free": "none", "self_serve_paid": "paid_plan_required",
    "admin_approval": "admin_approval_required", "app_review": "app_review_required",
    "partner_gated": "partnership_required", "no_public_api": "no_public_api",
    "unknown": "unknown",
}


def main() -> None:
    rng = random.Random(11)
    recs = {}
    for name, cat, hint in APPS:
        r = blank(name, cat, hint)
        r["slug"] = slug(name)
        tier = rng.choice(TIER_BY_CAT[cat])
        r["one_liner"] = "Sample record — not real research."
        r["auth_methods"] = [rng.choice(["oauth2", "oauth2", "api_key", "api_key", "bearer_token", "hmac_signed"])]
        r["access_tier"] = tier
        r["api_types"] = [rng.choice(["rest", "rest", "rest", "graphql"])]
        r["api_breadth"] = rng.choice(["narrow", "moderate", "moderate", "broad", "very_broad"])
        r["mcp_status"] = rng.choice(["none", "none", "none", "community", "official"])
        r["verdict"] = VERDICT_BY_TIER[tier]
        r["blocker"] = BLOCKER_BY_TIER[tier]
        r["confidence"] = rng.choice(["high", "high", "medium", "low"])
        r["evidence"] = [{"url": "https://example.invalid/docs", "excerpt": "Synthetic placeholder text.", "supports": ["auth_methods"]}]
        r["validation"] = {"ok": rng.random() > 0.12, "errors": [], "grounded": 2, "ungrounded": 0}
        recs[name] = r

    v1 = {k: dict(v, validation={"ok": rng.random() > 0.42, "errors": ["excerpt not found in the page"]}) for k, v in recs.items()}
    bundle = {
        "sample": True,
        "patterns": analyze(recs),
        "accuracy": {"available": True, "n_sampled": 20, "fields": {
            "auth_methods": {"n": 20, "v1_pct": 70, "v2_pct": 90},
            "access_tier": {"n": 20, "v1_pct": 55, "v2_pct": 80},
            "api_types": {"n": 20, "v1_pct": 85, "v2_pct": 95},
            "mcp_status": {"n": 20, "v1_pct": 45, "v2_pct": 85},
            "verdict": {"n": 20, "v1_pct": 60, "v2_pct": 85},
        }, "overall": {"n": 100, "v1_pct": 63, "v2_pct": 87, "delta": 24},
            "rows": [], "regressions": []},
        "validation": {"v1_clean_pct": 58, "v2_clean_pct": 91, "repairs_run": 61,
                       "top_v1_errors": [["excerpt not found in the page", 34], ["access_tier asserted with no grounded evidence", 19]],
                       "still_failing": ["fanbasis", "iPayX"]},
        "apps": sorted(recs.values(), key=lambda r: (r["category"], r["app"])),
    }
    (DATA / "bundle.sample.json").write_text(json.dumps(bundle, indent=2))
    print(f"wrote {DATA/'bundle.sample.json'} (SYNTHETIC)")


if __name__ == "__main__":
    main()
