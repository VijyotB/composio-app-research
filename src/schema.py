"""Schema for one researched app.

Deliberately small and closed-vocabulary. Free text is only allowed in
`one_liner`, `blocker`, and evidence excerpts. Everything the patterns
section counts is an enum, so clustering is arithmetic, not another LLM call.
"""

AUTH_METHODS = [
    "oauth2",          # three-legged OAuth, user consents
    "api_key",         # static key/secret in a header or query param
    "bearer_token",    # long-lived personal / service token
    "basic",           # HTTP basic
    "jwt_service",     # signed assertion / service account / app-level JWT
    "hmac_signed",     # request signing (common in trading + commerce)
    "none",            # public, unauthenticated
    "unknown",
]

ACCESS_TIERS = [
    "self_serve_free",      # sign up, get credentials, free tier
    "self_serve_paid",      # sign up yourself but a paid plan is required
    "admin_approval",       # needs a workspace/org admin to enable
    "app_review",           # needs platform review before production scopes
    "partner_gated",        # partnership / contact-sales / allowlist
    "no_public_api",
    "unknown",
]

API_TYPES = ["rest", "graphql", "soap", "grpc", "websocket", "sdk_only", "none", "unknown"]

# Rough count of documented, distinct resource endpoints/operations.
API_BREADTH = ["none", "narrow", "moderate", "broad", "very_broad", "unknown"]
BREADTH_GUIDE = {
    "narrow": "<25 documented operations",
    "moderate": "25-100",
    "broad": "100-400",
    "very_broad": ">400",
}

MCP_STATUS = [
    "official",      # vendor ships/hosts an MCP server
    "community",     # third-party server exists in a registry
    "none",
    "unknown",
]

VERDICTS = [
    "build_now",        # self-serve creds + documented API, no gate
    "build_with_care",  # buildable but a real friction (app review, paid tier, odd auth)
    "needs_outreach",   # requires partnership/sales before a toolkit is possible
    "not_buildable",    # no public API at all
    "unknown",
]

BLOCKERS = [
    "none",
    "paid_plan_required",
    "admin_approval_required",
    "app_review_required",
    "partnership_required",
    "no_public_api",
    "docs_not_public",
    "sandbox_unavailable",
    "rate_or_quota_gated",
    "regional_restriction",
    "unknown",
]

CONFIDENCE = ["high", "medium", "low"]

# Fields the validator checks and the human sample is scored on.
SCORED_FIELDS = ["auth_methods", "access_tier", "api_types", "mcp_status", "verdict"]


def blank(name: str, category: str, hint: str) -> dict:
    return {
        "app": name,
        "slug": None,
        "category": category,
        "hint": hint,
        "one_liner": "",
        "auth_methods": ["unknown"],
        "access_tier": "unknown",
        "api_types": ["unknown"],
        "api_breadth": "unknown",
        "api_breadth_note": "",
        "mcp_status": "unknown",
        "mcp_url": None,
        "verdict": "unknown",
        "blocker": "unknown",
        "blocker_note": "",
        "confidence": "low",
        "evidence": [],        # [{"url":..., "excerpt":..., "supports":[field,...]}]
        "validation": {},      # filled by validate.py
        "pass": None,          # "v1" | "v2"
        "human_checked": False,
        "notes": "",
    }


def validate_enums(rec: dict) -> list:
    """Return a list of enum violations. Cheap structural gate before anything else."""
    errs = []
    for m in rec.get("auth_methods", []):
        if m not in AUTH_METHODS:
            errs.append(f"auth_methods: {m!r} not in vocabulary")
    for t in rec.get("api_types", []):
        if t not in API_TYPES:
            errs.append(f"api_types: {t!r} not in vocabulary")
    for field, vocab in [
        ("access_tier", ACCESS_TIERS),
        ("api_breadth", API_BREADTH),
        ("mcp_status", MCP_STATUS),
        ("verdict", VERDICTS),
        ("blocker", BLOCKERS),
        ("confidence", CONFIDENCE),
    ]:
        if rec.get(field) not in vocab:
            errs.append(f"{field}: {rec.get(field)!r} not in vocabulary")
    return errs
