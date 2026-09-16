"""Validation.

The important property: this file contains no model call. A model grading its
own output is not verification, it is the same distribution twice. Every check
here is arithmetic on strings, so a failure is a fact rather than an opinion.

Checks, in order of how often they actually catch something:

  1. Excerpt grounding  - is the quoted excerpt genuinely present in the text we
                          fetched from that URL? Catches fabricated quotes.
  2. URL grounding      - is the cited URL one we actually fetched?
  3. Coverage           - does every scored field have at least one evidence
                          entry claiming to support it?
  4. Enum conformance   - is every value inside the closed vocabulary?
  5. Internal coherence - do verdict, access_tier and blocker agree with each
                          other? e.g. verdict=build_now with
                          blocker=partnership_required is self-contradictory.
"""

from __future__ import annotations

import re

from . import schema

_NORM = re.compile(r"[^a-z0-9]+")


def _norm(s: str) -> str:
    return _NORM.sub(" ", s.lower()).strip()


def _contains(haystack: str, needle: str) -> bool:
    """Whitespace/punctuation-insensitive containment, plus a token-overlap
    fallback so that a legitimate quote spanning a markdown table or a line
    break is not failed on formatting alone."""
    h, n = _norm(haystack), _norm(needle)
    if not n:
        return False
    if n in h:
        return True
    toks = n.split()
    if len(toks) < 6:
        return False
    # Require a long contiguous run of the excerpt to be present.
    for size in (12, 9, 7):
        if len(toks) >= size:
            for i in range(len(toks) - size + 1):
                if " ".join(toks[i:i + size]) in h:
                    return True
    return False


COHERENCE = [
    (lambda r: r["verdict"] == "build_now" and r["blocker"] not in ("none", "rate_or_quota_gated"),
     "verdict=build_now but a blocker is recorded"),
    (lambda r: r["verdict"] == "build_now" and r["access_tier"] in
     ("partner_gated", "no_public_api", "app_review"),
     "verdict=build_now contradicts access_tier"),
    (lambda r: r["verdict"] == "needs_outreach" and r["access_tier"].startswith("self_serve"),
     "verdict=needs_outreach contradicts a self-serve access tier"),
    (lambda r: r["access_tier"] == "no_public_api" and r["api_types"] not in ([], ["none"], ["unknown"]),
     "access_tier=no_public_api but an API type is claimed"),
    (lambda r: r["verdict"] == "not_buildable" and r["access_tier"] != "no_public_api",
     "verdict=not_buildable but a public API access tier is recorded"),
    (lambda r: r["confidence"] == "high" and len(r.get("evidence", [])) < 2,
     "confidence=high with fewer than two pieces of evidence"),
]


def validate(rec: dict, corpus: list[dict]) -> dict:
    """Attach and return rec['validation'] = {ok, errors, grounded, ungrounded}."""
    errors: list[str] = []
    by_url = {d["url"]: d["text"] for d in corpus}

    errors.extend(schema.validate_enums(rec))

    grounded, ungrounded = [], []
    for ev in rec.get("evidence", []):
        url, excerpt = ev.get("url", ""), ev.get("excerpt", "")
        if url not in by_url:
            ungrounded.append(ev)
            errors.append(f"evidence cites a URL that was never fetched: {url}")
            continue
        if _contains(by_url[url], excerpt):
            grounded.append(ev)
            ev["grounded"] = True
        else:
            ungrounded.append(ev)
            ev["grounded"] = False
            errors.append(f"excerpt not found in the page at {url}: {excerpt[:70]!r}")

    supported = {f for ev in grounded for f in ev.get("supports", [])}
    for field in schema.SCORED_FIELDS:
        if rec.get(field) in ("unknown", ["unknown"]):
            continue
        if field not in supported:
            errors.append(f"{field}={rec.get(field)!r} asserted with no grounded evidence")

    for test, message in COHERENCE:
        try:
            if test(rec):
                errors.append(message)
        except Exception:
            pass

    rec["validation"] = {
        "ok": not errors,
        "errors": errors,
        "grounded": len(grounded),
        "ungrounded": len(ungrounded),
    }
    return rec["validation"]


def repair_queries(rec: dict) -> list[str]:
    """Turn validation errors into targeted follow-up searches for pass 2."""
    app = rec["app"]
    qs = []
    blob = " ".join(rec["validation"]["errors"]).lower()
    if "auth" in blob:
        qs.append(f"{app} API authentication OAuth token docs")
    if "access_tier" in blob or "partner" in blob:
        qs.append(f"{app} API access requirements free tier partner program")
    if "api_types" in blob or "api_breadth" in blob:
        qs.append(f"{app} API reference list of endpoints")
    if "mcp" in blob:
        qs.append(f"{app} MCP server model context protocol")
    if not qs:
        qs.append(f"{app} developer documentation getting started API")
    return qs
