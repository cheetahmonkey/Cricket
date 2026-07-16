# Cricket

Cricket is the Daily Used Subaru Crosstrek Search Agent for Mom's replacement car search.

Run a manual search:

```bash
python3 -B -m cricket run --manual
```

Generated reports and snapshots are runtime data. Cricket syncs them to the Windows data store configured in `config/search_config.yaml`:

```text
/mnt/c/MMM/data/Mom/Cricket
```

The scheduled daily runner is:

```bash
/bin/bash /home/mmm/code/Mom/Subaru/scripts/run_daily_cricket.sh
```

Generate a mobile-friendly HTML page from a report:

```bash
python3 scripts/render_web_report.py reports/YYYY-MM-DD_crosstrek_search_report.md
```

The generated `docs/index.html` is ready for GitHub Pages when Pages is configured to publish from the `main` branch's `/docs` folder.
