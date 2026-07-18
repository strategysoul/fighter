# fighter — HART Ring Readiness Dashboard

Local-first dashboard that turns Fittr HART ring data (sleep, HRV, resting HR, steps, stress) into one daily 0–100 readiness score and 2–3 concrete actions. Plain CSV storage, static HTML output, Python stdlib only. See [PRD.md](PRD.md) for full requirements.

## Usage

```
python build_dashboard.py
```

Reads `data/log.csv`, writes `dashboard.html` — open it in any browser. Score is weighted (sleep 30, HRV-vs-baseline 25, resting-HR-vs-baseline 20, stress 15, sleep quality 10); missing metrics have their weight redistributed. Charts show 30-day trends against your own 7-day baseline.

`data/log.csv` schema: `date, sleep_hours, sleep_quality, hrv_ms, resting_hr, steps, stress, notes`. Any ingestion source (Health Sync export, Garmin import) should normalize into this schema.

## Health Connect native backup (v1.1)

Inspect the real scheduled backup before importing it:

```
python import_health_connect.py "C:\\path\\to\\Health Connect.zip" --inspect
```

The importer is read-only and stdlib-only. It refuses to import until the
exact schema from a real backup is documented in `data/samples/SCHEMA_NOTES.md`
and mapped in `import_health_connect.py`; this is deliberate because Health
Connect's database schema is internal and can change. Once verified:

```
python import_health_connect.py "C:\\path\\to\\Health Connect.zip"
python build_dashboard.py
```

Existing non-empty CSV cells are preserved and reruns are idempotent. Health
Sync CSV remains the fallback if the native schema proves too unstable.
