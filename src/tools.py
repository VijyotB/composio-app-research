"""Search / fetch / MCP-registry layer.

Composio is the preferred path (it is the product this assignment is for, and
it gives one auth surface over Firecrawl, Exa and Tavily). If COMPOSIO_API_KEY
is absent the module falls back to direct HTTP so the pipeline stays runnable
for a reviewer who has no Composio account.

Everything here is deterministic. No model is called in this file. That
separation is the point: the evidence corpus is gathered by code, and the model
only ever gets to summarise text that was really fetched.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import httpx

CACHE = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
USER_AGENT = "composio-app-research/1.0 (take-home research pipeline)"

_composio = None


def composio():
    """Lazily build a Composio client. Returns None when not configured."""
    global _composio
    if _composio is not None:
        return _composio or None
    if not COMPOSIO_API_KEY:
        _composio = False
        return None
    try:
        from composio import Composio  # composio>=0.7
        _composio = Composio(api_key=COMPOSIO_API_KEY)
    except Exception as exc:  # pragma: no cover
        print(f"[tools] Composio unavailable ({exc}); falling back to direct HTTP")
        _composio = False
        return None
    return _composio


def _cache_path(kind: str, key: str) -> Path:
    h = hashlib.sha256(key.encode()).hexdigest()[:20]
    return CACHE / f"{kind}-{h}.json"


def _cached(kind: str, key: str):
    p = _cache_path(kind, key)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None


def _store(kind: str, key: str, value):
    _cache_path(kind, key).write_text(json.dumps(value))
    return value


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

def search(query: str, k: int = 6) -> list[dict]:
    """Return [{title, url, snippet}]. Cached on disk so reruns are free."""
    hit = _cached("search", f"{query}|{k}")
    if hit is not None:
        return hit

    results: list[dict] = []
    c = composio()
    if c is not None:
        try:
            r = c.tools.execute(
                "COMPOSIO_SEARCH_TAVILY_SEARCH",
                arguments={"query": query, "max_results": k},
                user_id=os.getenv("COMPOSIO_USER_ID", "default"),
            )
            payload = r.get("data", r) if isinstance(r, dict) else {}
            for item in (payload.get("results") or payload.get("response_data", {}).get("results", []))[:k]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", "")[:600],
                })
        except Exception as exc:
            print(f"[search] composio failed for {query!r}: {exc}")

    if not results and TAVILY_API_KEY:
        try:
            r = httpx.post(
                "https://api.tavily.com/search",
                json={"api_key": TAVILY_API_KEY, "query": query, "max_results": k},
                timeout=30,
            )
            for item in r.json().get("results", [])[:k]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", "")[:600],
                })
        except Exception as exc:
            print(f"[search] tavily failed for {query!r}: {exc}")

    return _store("search", f"{query}|{k}", results)


# --------------------------------------------------------------------------
# Fetch
# --------------------------------------------------------------------------

_TAG_RE = re.compile(r"<(script|style|nav|footer|svg)[^>]*>.*?</\1>", re.S | re.I)
_ANY_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")


def _to_text(html: str) -> str:
    html = _TAG_RE.sub(" ", html)
    text = _ANY_TAG.sub(" ", html)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
                .replace("&#39;", "'"))
    text = _WS.sub(" ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch(url: str, limit: int = 24000) -> dict:
    """Fetch a page and return {url, ok, text}. Cached. Never raises."""
    hit = _cached("fetch", url)
    if hit is not None:
        return hit

    out = {"url": url, "ok": False, "text": "", "error": None}
    c = composio()
    if c is not None:
        try:
            r = c.tools.execute(
                "FIRECRAWL_SCRAPE_EXTRACT_DATA_LLM",
                arguments={"url": url, "formats": ["markdown"]},
                user_id=os.getenv("COMPOSIO_USER_ID", "default"),
            )
            data = r.get("data", {}) if isinstance(r, dict) else {}
            md = data.get("markdown") or data.get("content") or ""
            if md:
                out = {"url": url, "ok": True, "text": md[:limit], "error": None}
        except Exception as exc:
            out["error"] = f"composio/firecrawl: {exc}"

    if not out["ok"]:
        try:
            r = httpx.get(url, timeout=30, follow_redirects=True,
                          headers={"User-Agent": USER_AGENT})
            if r.status_code < 400:
                out = {"url": url, "ok": True, "text": _to_text(r.text)[:limit], "error": None}
            else:
                out["error"] = f"http {r.status_code}"
        except Exception as exc:
            out["error"] = str(exc)
        time.sleep(0.4)

    return _store("fetch", url, out)


# --------------------------------------------------------------------------
# MCP status — checked against registries, never guessed by the model
# --------------------------------------------------------------------------

def mcp_lookup(app: str) -> dict:
    """Query public MCP registries for a server matching this app.

    Model knowledge about MCP is the single least reliable thing in this whole
    problem: the ecosystem went from a few hundred servers to tens of thousands
    inside a year. So this is a deterministic registry lookup, and the model is
    told the answer rather than asked for it.
    """
    hit = _cached("mcp", app)
    if hit is not None:
        return hit

    out = {"app": app, "status": "unknown", "url": None, "source": None, "candidates": []}
    try:
        r = httpx.get("https://glama.ai/api/mcp/v1/servers",
                      params={"query": app, "first": 10},
                      timeout=30, headers={"User-Agent": USER_AGENT})
        if r.status_code < 400:
            servers = r.json().get("servers", [])
            for s in servers:
                name = (s.get("name") or "")
                desc = (s.get("description") or "")
                blob = f"{name} {desc}".lower()
                if app.split()[0].lower() in blob:
                    out["candidates"].append({
                        "name": name,
                        "url": s.get("url") or s.get("repository", {}).get("url"),
                        "description": desc[:200],
                    })
    except Exception as exc:
        out["source"] = f"glama error: {exc}"

    if out["candidates"]:
        first = out["candidates"][0]
        blob = f"{first['name']} {first['description']}".lower()
        out["status"] = "official" if "official" in blob else "community"
        out["url"] = first["url"]
        out["source"] = "glama.ai registry"
    else:
        # Registry silence is not proof of absence — fall through to a search
        # and let the validator downgrade confidence.
        res = search(f"{app} official MCP server", k=4)
        for item in res:
            u = (item["url"] or "").lower()
            t = f"{item['title']} {item['snippet']}".lower()
            if "mcp" in t and app.split()[0].lower() in t:
                official = any(d in u for d in ("docs.", "developer.", "github.com"))
                out.update(status="official" if official and "official" in t else "community",
                           url=item["url"], source="search fallback")
                break
        else:
            out["status"] = "none"
            out["source"] = "registry + search both empty"

    return _store("mcp", app, out)
