"""The 100-app research set, exactly as given in the assignment brief.

Each entry: (name, category, hint) where hint is the website/doc pointer the
brief supplied. The hint is a *seed* for search, never treated as evidence.
"""

APPS = [
    # 1. CRM and Sales
    ("Salesforce", "CRM and Sales", "salesforce.com"),
    ("HubSpot", "CRM and Sales", "hubspot.com"),
    ("Pipedrive", "CRM and Sales", "pipedrive.com"),
    ("Attio", "CRM and Sales", "attio.com"),
    ("Twenty", "CRM and Sales", "twenty.com (open-source CRM)"),
    ("Podio", "CRM and Sales", "podio.com"),
    ("Zoho CRM", "CRM and Sales", "zoho.com/crm"),
    ("Close", "CRM and Sales", "close.com"),
    ("Copper", "CRM and Sales", "copper.com"),
    ("DealCloud", "CRM and Sales", "api.docs.dealcloud.com"),

    # 2. Support and Helpdesk
    ("Zendesk", "Support and Helpdesk", "zendesk.com"),
    ("Intercom", "Support and Helpdesk", "intercom.com"),
    ("Freshdesk", "Support and Helpdesk", "freshdesk.com"),
    ("Front", "Support and Helpdesk", "front.com"),
    ("Pylon", "Support and Helpdesk", "usepylon.com"),
    ("LiveAgent", "Support and Helpdesk", "liveagent.com"),
    ("Plain", "Support and Helpdesk", "plain.com"),
    ("Help Scout", "Support and Helpdesk", "helpscout.com"),
    ("Gorgias", "Support and Helpdesk", "gorgias.com"),
    ("Gladly", "Support and Helpdesk", "gladly.com"),

    # 3. Communications and Messaging
    ("Slack", "Communications and Messaging", "slack.com"),
    ("Twilio", "Communications and Messaging", "twilio.com"),
    ("Zoho Cliq", "Communications and Messaging", "zoho.com/cliq"),
    ("Lark (Larksuite)", "Communications and Messaging", "open.larksuite.com"),
    ("Pumble", "Communications and Messaging", "pumble.com"),
    ("Discord", "Communications and Messaging", "discord.com"),
    ("Telegram", "Communications and Messaging", "core.telegram.org"),
    ("WhatsApp Business", "Communications and Messaging", "developers.facebook.com/docs/whatsapp"),
    ("Aircall", "Communications and Messaging", "aircall.io"),
    ("Vonage", "Communications and Messaging", "developer.vonage.com"),

    # 4. Marketing, Ads, Email and Social
    ("Google Ads", "Marketing, Ads, Email and Social", "developers.google.com/google-ads"),
    ("Meta Ads", "Marketing, Ads, Email and Social", "developers.facebook.com/docs/marketing-apis"),
    ("LinkedIn Ads", "Marketing, Ads, Email and Social", "learn.microsoft.com/linkedin/marketing"),
    ("GoHighLevel", "Marketing, Ads, Email and Social", "highlevel.stoplight.io"),
    ("Mailchimp", "Marketing, Ads, Email and Social", "mailchimp.com/developer"),
    ("Klaviyo", "Marketing, Ads, Email and Social", "developers.klaviyo.com"),
    ("systeme.io", "Marketing, Ads, Email and Social", "systeme.io (funnel builder)"),
    ("Pinterest", "Marketing, Ads, Email and Social", "developers.pinterest.com"),
    ("Threads (Meta)", "Marketing, Ads, Email and Social", "developers.facebook.com/docs/threads"),
    ("SendGrid", "Marketing, Ads, Email and Social", "sendgrid.com"),

    # 5. Ecommerce
    ("Shopify", "Ecommerce", "shopify.dev"),
    ("WooCommerce", "Ecommerce", "woocommerce.com/document/woocommerce-rest-api"),
    ("BigCommerce", "Ecommerce", "developer.bigcommerce.com"),
    ("Salesforce Commerce Cloud", "Ecommerce", "developer.salesforce.com/docs/commerce"),
    ("Magento (Adobe Commerce)", "Ecommerce", "developer.adobe.com/commerce"),
    ("Squarespace", "Ecommerce", "developers.squarespace.com"),
    ("Ecwid", "Ecommerce", "api-docs.ecwid.com"),
    ("Gumroad", "Ecommerce", "gumroad.com/api"),
    ("Amazon Selling Partner", "Ecommerce", "developer-docs.amazon.com/sp-api"),
    ("fanbasis", "Ecommerce", "fanbasis.com"),

    # 6. Data, SEO and Scraping
    ("DataForSEO", "Data, SEO and Scraping", "docs.dataforseo.com"),
    ("SE Ranking", "Data, SEO and Scraping", "seranking.com/api"),
    ("Ahrefs", "Data, SEO and Scraping", "ahrefs.com/api"),
    ("MrScraper", "Data, SEO and Scraping", "docs.mrscraper.com"),
    ("Apify", "Data, SEO and Scraping", "docs.apify.com"),
    ("Firecrawl", "Data, SEO and Scraping", "firecrawl.dev"),
    ("Bright Data", "Data, SEO and Scraping", "brightdata.com"),
    ("Sherlock", "Data, SEO and Scraping", "github.com/sherlock-project/sherlock"),
    ("Waterfall.io", "Data, SEO and Scraping", "waterfall.io (contact/company intel)"),
    ("Clay", "Data, SEO and Scraping", "clay.com"),

    # 7. Developer, Infra and Data platforms
    ("GitHub", "Developer, Infra and Data platforms", "docs.github.com/rest"),
    ("Vercel", "Developer, Infra and Data platforms", "vercel.com/docs/rest-api"),
    ("Netlify", "Developer, Infra and Data platforms", "docs.netlify.com/api"),
    ("Cloudflare", "Developer, Infra and Data platforms", "developers.cloudflare.com/api"),
    ("Supabase", "Developer, Infra and Data platforms", "supabase.com/docs"),
    ("Neo4j", "Developer, Infra and Data platforms", "neo4j.com/docs/api"),
    ("Snowflake", "Developer, Infra and Data platforms", "docs.snowflake.com"),
    ("MongoDB Atlas", "Developer, Infra and Data platforms", "mongodb.com/docs/atlas/api"),
    ("Datadog", "Developer, Infra and Data platforms", "docs.datadoghq.com/api"),
    ("Sentry", "Developer, Infra and Data platforms", "docs.sentry.io/api"),

    # 8. Productivity and Project Management
    ("Notion", "Productivity and Project Management", "developers.notion.com"),
    ("Airtable", "Productivity and Project Management", "airtable.com/developers"),
    ("Linear", "Productivity and Project Management", "developers.linear.app"),
    ("Jira", "Productivity and Project Management", "developer.atlassian.com"),
    ("Asana", "Productivity and Project Management", "developers.asana.com"),
    ("Monday.com", "Productivity and Project Management", "developer.monday.com"),
    ("ClickUp", "Productivity and Project Management", "clickup.com/api"),
    ("Coda", "Productivity and Project Management", "coda.io/developers"),
    ("Smartsheet", "Productivity and Project Management", "smartsheet.com/developers"),
    ("Harvest", "Productivity and Project Management", "help.getharvest.com/api-v2"),

    # 9. Finance and Fintech
    ("Stripe", "Finance and Fintech", "stripe.com/docs/api"),
    ("Plaid", "Finance and Fintech", "plaid.com/docs"),
    ("Binance", "Finance and Fintech", "binance-docs.github.io"),
    ("Paygent Connect", "Finance and Fintech", "paygent (NMI-powered)"),
    ("iPayX", "Finance and Fintech", "ipayx.ai/docs"),
    ("QuickBooks", "Finance and Fintech", "developer.intuit.com"),
    ("Xero", "Finance and Fintech", "developer.xero.com"),
    ("Brex", "Finance and Fintech", "developer.brex.com"),
    ("Ramp", "Finance and Fintech", "docs.ramp.com"),
    ("PitchBook", "Finance and Fintech", "pitchbook.com (research API)"),

    # 10. AI, Research and Media-native
    ("NotebookLM", "AI, Research and Media-native", "cloud.google.com/gemini (Enterprise API)"),
    ("Otter AI", "AI, Research and Media-native", "help.otter.ai (MCP server)"),
    ("Fathom", "AI, Research and Media-native", "fathom.video"),
    ("Consensus", "AI, Research and Media-native", "consensus.app (OAuth requested)"),
    ("Reducto", "AI, Research and Media-native", "reducto.ai (document parsing)"),
    ("Devin", "AI, Research and Media-native", "docs.devin.ai (MCP)"),
    ("higgsfield", "AI, Research and Media-native", "higgsfield.ai/cli (content suite)"),
    ("Mermaid CLI", "AI, Research and Media-native", "github.com/mermaid-js/mermaid-cli"),
    ("YouTube Transcript", "AI, Research and Media-native", "transcriptapi.com"),
    ("Grain", "AI, Research and Media-native", "grain.com (meeting notes)"),
]

CATEGORIES = []
for _n, _c, _h in APPS:
    if _c not in CATEGORIES:
        CATEGORIES.append(_c)


def slug(name: str) -> str:
    out = []
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


assert len(APPS) == 100, f"expected 100 apps, got {len(APPS)}"
assert len(CATEGORIES) == 10
