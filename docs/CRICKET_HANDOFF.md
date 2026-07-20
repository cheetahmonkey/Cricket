# Cricket Handoff

## What Cricket Is

Cricket is the daily used Subaru Crosstrek search agent for Mom. The repository
is `/home/mmm/code/Mom/Subaru`; the Python package and CLI namespace are
`cricket`.

The daily report is Markdown-first. HTML for GitHub Pages and the family PDF are
derived from the same Markdown report, not maintained as separate reports.

## Current Buyer Requirements

- Subaru Crosstrek, model year 2020 or newer, automatic/CVT, AWD.
- Mileage under 45,000.
- Limited trim is preferred. Sport or Premium can stay visible only when safety
  evidence supports them.
- Safety is the first gate: rear camera, Blind Spot Detection (BSD), Rear
  Cross-Traffic Alert (RCTA), and especially Reverse Automatic Braking (RAB).
- Preferred colors: blue/teal, then burgundy/green, then white. Black, silver,
  and gray are lower preference but are not disqualifiers.
- Carter Shoreline and Carter Ballard are preferred sellers; other Subaru
  dealers remain valuable local sources.

The authoritative configuration is `config/search_config.yaml`. Do not change
the buyer rules based only on this handoff.

## Active Sources

| Dealer/source | Status | Inventory discovery | Vehicle detail path |
| --- | --- | --- | --- |
| Carter Subaru Shoreline | Active | Carter inventory sitemaps | Jina text mirror, with direct fallback for missing price |
| Carter Subaru Ballard | Active | Carter inventory sitemaps | Jina text mirror, with direct fallback for missing price |
| Renton Subaru | Active | Public sitemap through Jina's Markdown sitemap view | Direct public detail HTML via `curl -Ls` |
| Subaru of Puyallup | Active | Public sitemap through Jina's Markdown sitemap view | Direct public detail HTML via `curl -Ls` |
| Subaru Certified Pre-Owned | Active as a supplemental source | Subaru CPO landing page | Often returns no individual listings; not a dealership row |

As of the July 20, 2026 report, Renton had 7 in-scope vehicles fully detailed
and Puyallup had 10. The higher discovery counts include pre-2020 vehicles,
which intentionally do not receive detail enrichment.

### Important Source Rules

- Renton and Puyallup have **no per-run detail cap**. This was deliberately
  removed at the user's request. Keep `minimum_detail_year: 2020`, but do not
  reintroduce `max_detail_enrichments` for these sources without discussion.
- Their raw sitemap candidates are retained in `data/listings_raw/`, while only
  detail-enriched candidates enter the normalized snapshot/report. This keeps
  unknown placeholder records out of the family-facing tables.
- Standard dealer pages carry useful fields in embedded HTML/JSON. The parser
  reads `internetPrice`, asking-price text, odometer, quick specs, HTML title,
  and embedded `title` metadata. Do not assume that a missing visible text field
  means the page has no data.
- One Puyallup vehicle had no actual price on its public page; placeholder
  `internetPrice` strings do not count as a price. Leave such prices unknown.
- Safety evidence must come from listing detail text. The parser recognizes the
  Carter wording `Automatic emergency braking (rear)` for RAB, along with BSD,
  RCTA, and rear-camera wording.
- Do not hammer dealer sites. Use the published sitemap once per source and one
  detail fetch per in-scope listing in a run. Avoid retry loops and parallel
  detail crawls.
- Tacoma Subaru is not currently active because direct inventory access is
  Cloudflare-blocked from this machine. Its public `/llm/inventory/` endpoint
  exists but is blocked too. Do not bypass Cloudflare. Marysville did not expose
  current individual inventory URLs through its sitemap during prior discovery.

## Source Implementation Map

- `cricket/sources/base.py`: common HTTP fetcher. A source may opt into
  `fetch_via_curl: true`; this is required for Renton and Puyallup direct HTML.
- `cricket/sources/carter.py`: Carter sitemap adapter, standard dealer sitemap
  adapter (`LocalSubaruSource`), and shared detail parser.
- `cricket/sources/subaru_cpo.py`: supplemental Subaru CPO source.
- `cricket/normalize.py`: raw-to-`Listing` normalization.
- `cricket/scoring.py`: hard filters, feature inference, and ranking.
- `cricket/storage.py`: raw/normalized snapshots and SQLite history.
- `cricket/report.py`: canonical Markdown report.

## Reporting Requirements

The report must remain practical for Mom and family, not a technical run log.

- The canonical report is `reports/YYYY-MM-DD_crosstrek_search_report.md`.
- Keep the short event-driven Morning Note. Do not repeat a generic daily
  statement when nothing meaningful changed.
- Top Opportunities and Other Listings tables both use this order at the left:
  rank/number, score or concern, direct linked color, year, trim, safety,
  feature confidence, miles, price, estimated OTD, seller, visit check, and
  `Date Added` at the far right.
- The color text itself links directly to the dealer detail page. Do not use
  footnote-style links.
- Safety column shows only confirmed RAB, BSD, and RCTA. `Feature Confidence`
  remains visible. `Check Before Visiting` contains a direct CARFAX link when
  available, plus the relevant safety/OTD check.
- Do not include misleading CARFAX narrative claims such as unknown accident or
  title status. Keep the CARFAX link for manual review.
- At the bottom, keep `Dealership Sourcing Status` showing Active/Partial/Access
  issue plus discovered and detailed counts for each configured dealership.
- Keep the family-readable `Scoring Key` after the sourcing table.
- Keep `Report Details` and any `Search Notes` near the end.

### Pricing and Scoring

Estimated OTD is:

`listed price + 11% Washington sales tax + $200 document fee + $700 registration/licensing`

Use the configured values; the document-fee label remains Carter-oriented in
the report, although the estimate is used consistently across local dealers.

The intended score is out of 100:

- safety 25
- price/value 20
- mileage 15
- year/trim 10
- seller 10
- distance 10
- history 5
- Mom-fit extras 5

Market data is not implemented. The code currently gives price/value a 10-point
placeholder when market value is unavailable, so the practical maximum is 90
until market pricing is added. Keep the report's 100-point scoring key accurate
about this placeholder.

## History and Date Added

`Date Added` is `Listing.first_seen_date`, not the date a car happened to enter
Top Opportunities. `storage.save_history()` preserves the earliest date across
both qualified and rejected listings. This behavior has a regression test in
`tests/test_storage.py`.

## Daily Operation

Manual run:

```bash
cd /home/mmm/code/Mom/Subaru
python3 -B -m cricket run --manual
```

Test suite:

```bash
python3 -m unittest discover -s tests -v
```

The daily runner is `scripts/run_daily_cricket.sh`. It:

1. Runs Cricket and syncs the report/raw/normalized files to the Windows data
   store configured at `/mnt/c/MMM/data/Mom/Cricket`.
2. Renders the newest Markdown report into `docs/index.html`.
3. Commits and pushes a changed `docs/index.html` to `main` for GitHub Pages.
4. Creates `YYYY-MM-DD cricket report.pdf` and copies it to the configured
   family Google Drive folder through `rclone`.

The intended cron schedule is 7:15 a.m. Pacific. Logs are in `logs/`.

Useful manual publication commands:

```bash
python3 scripts/render_web_report.py reports/YYYY-MM-DD_crosstrek_search_report.md
python3 scripts/publish_drive_report.py reports/YYYY-MM-DD_crosstrek_search_report.md
```

Use the newest dated report when rendering `docs/index.html`. A cron commit can
occur while working; check `git log` and do not accidentally render yesterday's
report over the latest GitHub Pages report.

## Repository and Publishing

- Remote: `origin` is `git@github-cm:cheetahmonkey/Cricket.git`.
- GitHub Pages deploys `main` from `/docs`.
- Public page: `https://cheetahmonkey.github.io/Cricket/`.
- The repository Git identity is `cm <cheetahmonkey77@gmail.com>`.
- SSH authentication uses the local `github-cm` host alias. Do not place keys,
  tokens, or other credentials in this repository or this handoff.

Code/config changes require an explicit normal commit and push. The daily runner
only auto-commits the rendered GitHub Pages file.

## Useful Verification

After a run, inspect source coverage without re-fetching pages:

```bash
python3 -c 'import json; data=json.load(open("data/listings_raw/YYYY-MM-DD.json")); [print("%s: found=%d detailed=%d errors=%d" % (item["source_name"], len(item["raw_items"]), sum(bool(raw.get("detail_text_fetched")) for raw in item["raw_items"]), len(item["errors"]))) for item in data]'
```

If an execution tool session returns no Cricket summary, do not assume the run
failed or succeeded. Check modification times on the raw snapshot, normalized
snapshot, and report. Some sessions have completed successfully without showing
stdout. Do not launch duplicate full runs until checking those files.

## Current Baseline

The latest source/report implementation before this handoff was committed through:

```text
b63c4b2 Publish Cricket report for 2026-07-20
d25823f Fully enrich local Subaru inventory
```

Before making changes in a new session:

1. `git status --short`
2. `git log -5 --oneline`
3. Read `config/search_config.yaml`, this handoff, and the newest report.
4. Preserve user changes and check whether cron has already generated a newer
   report before manually rendering or publishing.
