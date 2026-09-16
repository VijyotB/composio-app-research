"""The research step for one app.

Shape of a pass:

  1. Deterministic evidence gathering. Five fixed queries per app, top results
     fetched, plus the doc hint from the brief. No model involved.
  2. MCP status resolved against a registry (tools.mcp_lookup).
  3. One constrained synthesis call. The model sees ONLY the fetched corpus and
     must return JSON matching schema.py, with an evidence excerpt copied
     verbatim from the corpus for every claim.

Step 3 cannot invent a URL, because it is only allowed to cite URLs that appear
in the corpus index it was handed. That is checked mechanically in validate.py.
"""

from __future__ import annotations

import json
import os
import re

from anthropic import Anthropic

from . import schema
from .app_list import slug
from .tools import fetch, mcp_lookup, search

MODEL = os.getenv("RESEARCH_MODEL", "claude-sonnet-4-6")
_client = None


def client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


QUERY_TEMPLATES = [
    "{app} API documentation authentication",
    "{app} developer API get API key access",
    "{app} REST API OR GraphQL API reference endpoints",
    "{app} API pricing plan required OR partner program OR contact sales",
    "{app} API app review OR OAuth scopes approval",
]


def gather(app: str, hint: str, extra_queries: list[str] | None = None) -> list[dict]:
    """Build the evidence corpus: a list of {url, text} actually fetched."""
    urls: list[str] = []

    if hint and "." in hint:
        base = hint.split()[0].strip("()")
        if not base.startswith("http"):
            base = "https://" + base
        urls.append(base)

    for tmpl in QUERY_TEMPLATES + (extra_queries or []):
        q = tmpl.format(app=app) if "{app}" in tmpl else tmpl
        for r in search(q, k=4):
            if r["url"] and r["url"] not in urls:
                urls.append(r["url"])

    # Prefer first-party docs. An answer sourced from a blog is weaker evidence
    # than the same answer sourced from the vendor's own reference.
    def rank(u: str) -> int:
        u = u.lower()
        if any(s in u for s in ("/docs", "docs.", "developer.", "developers.", "/api", "api.")):
            return 0
        if any(s in u for s in ("medium.com", "reddit.com", "youtube.com", "quora.com")):
            return 2
        return 1

    urls.sort(key=rank)
    corpus = []
    for u in urls[:10]:
        page = fetch(u)
        if page["ok"] and len(page["text"]) > 400:
            corpus.append({"url": page["url"], "text": page["text"]})
        if len(corpus) >= 7:
            break
    return corpus


SYSTEM = """You are a research analyst for an AI-agent integration platform. \
You classify third-party apps by how hard they would be to turn into a toolkit \
an AI agent can call.

Rules you must not break:
- Use ONLY the supplied source documents. No prior knowledge, no inference \
beyond what the text states.
- Every claim needs an evidence entry whose `excerpt` is copied VERBATIM from \
one of the documents (a contiguous span of 10-40 words) and whose `url` is one \
of the supplied document URLs.
- If the documents do not establish a field, return "unknown" and set \
confidence to "low". "unknown" with an honest note is a correct answer. A \
confident guess is a wrong answer.
- Return a single JSON object and nothing else. No prose, no code fences."""


def build_prompt(app: str, category: str, corpus: list[dict], mcp: dict,
                 repair: dict | None = None) -> str:
    docs = "\n\n".join(
        f"<document id=\"{i}\" url=\"{d['url']}\">\n{d['text'][:9000]}\n</document>"
        for i, d in enumerate(corpus)
    )
    vocab = {
        "auth_methods": schema.AUTH_METHODS,
        "access_tier": schema.ACCESS_TIERS,
        "api_types": schema.API_TYPES,
        "api_breadth": schema.API_BREADTH,
        "mcp_status": schema.MCP_STATUS,
        "verdict": schema.VERDICTS,
        "blocker": schema.BLOCKERS,
        "confidence": schema.CONFIDENCE,
    }
    repair_block = ""
    if repair:
        repair_block = (
            "\n\nA previous attempt at this record FAILED validation. Fix only "
            "these problems; keep everything else that was correct:\n"
            + "\n".join(f"- {e}" for e in repair["errors"])
            + f"\n\nPrevious attempt:\n{json.dumps(repair['record'], indent=2)[:3000]}"
        )

    return f"""App: {app}
Category: {category}

Registry lookup for MCP (authoritative — use this, do not second-guess it):
{json.dumps(mcp, indent=2)[:900]}

Breadth guide: {json.dumps(schema.BREADTH_GUIDE)}

Allowed values per field:
{json.dumps(vocab, indent=2)}

Source documents:
{docs}
{repair_block}

Return JSON with exactly these keys:
one_liner (<=18 words, what the app does),
auth_methods (list), access_tier, api_types (list), api_breadth,
api_breadth_note (<=15 words, cite the count you saw),
mcp_status, mcp_url (or null),
verdict, blocker, blocker_note (<=20 words),
confidence,
evidence (list of {{"url","excerpt","supports"}} where supports is a list of \
field names from: auth_methods, access_tier, api_types, api_breadth, \
mcp_status, verdict),
notes (<=25 words; anything a human should double-check)."""


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def research(app: str, category: str, hint: str, repair: dict | None = None,
             extra_queries: list[str] | None = None) -> dict:
    corpus = gather(app, hint, extra_queries)
    mcp = mcp_lookup(app)

    rec = schema.blank(app, category, hint)
    rec["slug"] = slug(app)
    rec["_corpus_urls"] = [d["url"] for d in corpus]

    if not corpus:
        rec.update(access_tier="unknown", verdict="unknown", blocker="docs_not_public",
                   confidence="low",
                   notes="No fetchable documentation found. Needs a human look.")
        return rec, corpus

    msg = client().messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(app, category, corpus, mcp, repair)}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text")
    try:
        parsed = _parse(raw)
    except Exception as exc:
        rec["notes"] = f"synthesis unparseable: {exc}"
        return rec, corpus

    for k, v in parsed.items():
        if k in rec:
            rec[k] = v

    # The registry wins over the model on MCP, always.
    if mcp["status"] != "unknown":
        rec["mcp_status"] = mcp["status"]
        rec["mcp_url"] = mcp["url"]
    return rec, corpus
