# fighter — HART Ring Readiness Dashboard

Local-first dashboard that turns Fittr HART ring data (sleep, HRV, resting HR, steps, stress) into one daily 0–100 readiness score and 2–3 concrete actions. Plain CSV storage, static HTML output, Python stdlib only. See [PRD.md](PRD.md) for full requirements.

## Usage

```
python build_dashboard.py
```

Reads `data/log.csv`, writes `dashboard.html` — open it in any browser. Score is weighted (sleep 30, HRV-vs-baseline 25, resting-HR-vs-baseline 20, stress 15, sleep quality 10); missing metrics have their weight redistributed. Charts show 30-day trends against your own 7-day baseline.

`data/log.csv` schema: `date, sleep_hours, sleep_quality, hrv_ms, resting_hr, steps, stress, notes`. Any ingestion source (Health Sync export, Garmin import) should normalize into this schema.
