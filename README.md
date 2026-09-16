# 100 apps, graded for agent buildability

Research pipeline for the Composio AI Product Ops take-home. It researches 100 apps,
grades each on how buildable it is as an agent toolkit, and emits a single
self-contained HTML case study.

**Live case study:** _(add your deployed URL)_

---

## Run it

```bash
git clone <your-repo> && cd composio-app-research
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

export ANTHROPIC_API_KEY=...        # synthesis
export COMPOSIO_API_KEY=...         # search + fetch (optional)
export TAVILY_API_KEY=...           # fallback search if no Composio
```

```bash
python -m src.orchestrate --limit 5        # smoke test, ~2 min
python -m src.orchestrate                  # all 100, ~25 min at 4 workers
python -m src.analyze --make-sample 20     # emit the human-check worksheet
#   ... fill in data/human_sample.json by reading the real docs ...
python -m src.analyze                      # patterns + accuracy -> data/bundle.json
python -m src.build_page --repo <url> --author "<you>"
```

`index.html` is the deliverable. It is fully self-contained — open it from disk,
or drop it on GitHub Pages / Netlify as-is.

To check the layout without any API keys:

```bash
python -m src.smoke && python -m src.build_page --allow-sample --out preview.html
```

That builds from invented data and carries a red banner saying so.

---

## What it does

Per app, in order:

| # | Step | Model involved? |
|---|------|-----------------|
| 1 | Five fixed search queries + the brief's doc hint | no |
| 2 | Fetch up to 7 pages, first-party docs ranked above blogs, cached to disk | no |
| 3 | Resolve MCP status against the Glama registry | no |
| 4 | One constrained synthesis call over the fetched corpus | **yes** |
| 5 | Mechanical validation of the result | no |
| 6 | Targeted repair research on whatever failed | **yes** |

Output lands in `src/results/v1/<slug>.json` and `src/results/v2/<slug>.json`.

### Three decisions worth defending

**Closed vocabulary.** Every field the patterns section counts is an enum
(`src/schema.py`). Clustering is then arithmetic over those enums, not a second
model call asked to summarise the first one. A pattern on the page is
reproducible from the JSON.

**The validator contains no model.** A model grading its own output is the same
distribution sampled twice. So validation is string work: is the quoted excerpt
genuinely present in the text we fetched from that URL; is the URL one we
actually fetched; does every asserted field have grounded evidence behind it;
do `verdict`, `access_tier` and `blocker` contradict each other. A failure is a
fact, not an opinion.

**MCP status is looked up, not asked.** Model knowledge about which vendors ship
MCP servers is the least reliable thing in this problem — the ecosystem went
from hundreds of servers to tens of thousands inside a year. The registry is
queried first and the model is *told* the answer.

### Both passes are kept

`v1/` holds the first answer, before any repair. `v2/` holds the answer after
validation and targeted repair. The assignment asks for accuracy moving from a
lower first pass to a higher one, and that is unmeasurable if the repair loop
overwrites what you would measure against. Repairs are only accepted if the
record comes back strictly less broken, and are bounded at two attempts.

### Where a human was needed

1. **The obscure tail.** Apps with thin or no public documentation. The model's
   instinct is to fill the gap with something plausible; a person has to open
   the site and say "there is nothing here". These are the rows most worth
   reading before you trust the page.
2. **The accuracy sample.** Twenty apps, two per category, read by hand against
   live docs and scored field by field. Stratified so the number is not
   dominated by whichever category happened to be easiest.

---

## Layout

```
src/
  app_list.py        the 100 apps, verbatim from the brief
  schema.py          closed vocabulary + coherence rules
  tools.py           search / fetch / MCP registry (Composio, with fallbacks)
  research.py        evidence gathering + one constrained synthesis call
  validate.py        mechanical checks, no model
  orchestrate.py     v1 -> validate -> repair -> v2, checkpointed
  analyze.py         pattern counts + v1/v2 accuracy scoring
  build_page.py      injects data into the template
  page_template.html the case study
  smoke.py           synthetic data for layout checks
  results/v1, v2/    per-app JSON checkpoints
data/
  cache/             search + fetch cache (gitignored)
  human_sample.json  the hand-checked rows
  bundle.json        everything the page reads
index.html           the deliverable
```

## Known limits

- Access tier is read off public documentation. A vendor can document a free
  tier and gate in practice. Anything marked *build now* still needs one real
  credential test before it goes on a roadmap.
- Registry silence is not proof that no MCP server exists; `none` means the
  registry and a follow-up search both came back empty.
- Fetching is best-effort. Docs behind JS-only rendering or a login return
  nothing, and the record is marked `unknown` rather than guessed.
