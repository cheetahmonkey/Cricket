We are in the project directory:

`/home/mmm/code/Mom/Subaru`

Please build the first working version of **Cricket**, the Daily Used Subaru Crosstrek Search Agent, by reading and following the local spec file:

`cricket_spec.md`

Cricket is the human-facing name of the agent. Use `cricket` as the Python package name and CLI command namespace unless the existing project structure strongly suggests otherwise.

Start by inspecting the repo/project state:

```bash id="wtjruw"
pwd
ls -la
find . -maxdepth 3 -type f | sort
```

Then read the full spec carefully:

```bash id="v9anbp"
cat cricket_spec.md
```

Important implementation guidance:

1. Treat `cricket_spec.md` as the source of truth.
2. The human-facing agent name is **Cricket**.
3. Use `cricket` for package/module names where practical.
4. Implement the initial version using Tier 1 sources only:

   * Carter Subaru Shoreline used inventory
   * Carter Subaru Ballard / Carter Subaru group inventory, if separate
   * Subaru certified pre-owned inventory
   * Local Subaru dealership websites
5. Do not implement Tier 2 or Tier 3 sources yet.
6. Do not implement alerts yet.
7. Save the dealer contact script template for future use, but do not include it in the daily report unless the spec requires it.
8. Add a manual run option so I can trigger a search immediately from the command line.
9. The manual command should be simple, preferably:

```bash id="jwnjw1"
python -m cricket run --manual
```

or, if you choose a script entry point:

```bash id="7zgcn3"
python scripts/run_search.py --manual
```

10. The manual run should:

* Search Tier 1 sources
* Normalize found listings
* Apply hard filters
* Score listings
* Save raw/normalized snapshots
* Compare against any prior run if history exists
* Generate today’s Markdown report under `reports/`
* Print the report path and a short terminal summary using the name Cricket, for example:

  * `Cricket found 3 promising Crosstreks today.`
  * `Cricket found no qualifying listings today.`
  * `Cricket generated report: reports/YYYY-MM-DD_crosstrek_search_report.md`

Suggested initial structure, but adjust if the repo already has a structure:

```text id="q280bf"
config/
  search_config.yaml
data/
  listings_raw/
  listings_normalized/
  listings_history.sqlite
reports/
src/
  cricket/
    __init__.py
    __main__.py
    cli.py
    config.py
    models.py
    scoring.py
    normalize.py
    report.py
    storage.py
    sources/
      __init__.py
      base.py
      carter.py
      subaru_cpo.py
scripts/
  run_search.py
tests/
```

Build this in small, testable steps:

1. Create the project structure.
2. Create config from the spec.
3. Create the normalized listing model.
4. Create scoring logic, including:

   * safety feature confidence
   * price/value placeholder scoring if market data is unavailable
   * mileage
   * year/trim
   * seller quality
   * distance/convenience
   * vehicle history
   * Mom-fit extras
   * color scoring
5. Create source adapter interfaces.
6. Implement Tier 1 source adapters conservatively.
7. If live source fetching is blocked or unreliable, implement a graceful fallback that records the failure and still allows report generation from any available data.
8. Create Markdown report generation in the simplified report format:

   * 2–3 sentence summary
   * Top Opportunities
   * New / Rejected / Price Drop Listings
9. Add SQLite or JSON-backed history so later runs can detect new listings and price changes.
10. Add a manual command and document exactly how to run it.

Report language should use Cricket naturally, for example:

```text id="n2l0kl"
Cricket found 2 promising Crosstreks today.
Cricket found one Carter listing worth verifying.
Cricket rejected 4 listings today because they were over mileage, wrong trim, or missing RAB evidence.
Cricket says: verify RAB before visiting.
```

After implementation, run the manual search once now and show:

* the exact command used
* any errors or source-access limitations
* the generated report path
* a concise summary of top results or “Cricket found no qualifying listings today”
* the next most useful improvement

Do not make broad architecture changes beyond this initial MVP. Prioritize a working manual run today.
