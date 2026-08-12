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

The scheduled daily runner generates the daily report, refreshes `docs/index.html`, pushes the changed page to GitHub Pages, and uploads a PDF named `YYYY-MM-DD cricket report.pdf` to the configured family Google Drive folder:

```bash
/bin/bash /home/mmm/code/Mom/Subaru/scripts/run_daily_cricket_healthchecked.sh
```

The monitored wrapper reads its private Healthchecks.io ping URL from
`/home/mmm/.config/cricket/healthchecks_url` and delegates the actual workflow
to `scripts/run_daily_cricket.sh`.

## Scheduled Execution Path

```text
7:15 a.m. cron
      |
      v
run_daily_cricket_healthchecked.sh
      |
      +-- read private Healthchecks URL
      +-- send /start (a ping failure logs a warning but does not stop Cricket)
      |
      v
run_daily_cricket.sh
      |
      +-- search dealer inventory
      +-- filter and rank listings
      +-- save report, snapshots, and history
      +-- publish GitHub Pages
      +-- create PDF and copy it to Google Drive
      |
      v
all steps succeeded?
      |
      +-- yes --> send success ping --> Healthchecks UP
      |
      +-- no  --> send /<exit-code> --> Healthchecks DOWN
```

If cron never starts because WSL is asleep, Healthchecks receives no ping and
marks the check down after the configured grace period.

Generate a mobile-friendly HTML page from a report:

```bash
python3 scripts/render_web_report.py reports/YYYY-MM-DD_crosstrek_search_report.md
```

The generated `docs/index.html` is ready for GitHub Pages when Pages is configured to publish from the `main` branch's `/docs` folder.
