# PLAN.md — Living Plan & History

> Running log of what was planned, what's done, and what's next.
> Updated every time the plan changes. Read this first when resuming work on the repo.

## Current status (as of 2026-07-17)

**v1 is done and pushed.** The repo has a working prototype: sample data, scoring engine, static dashboard.

**Next up: v1.1 — Health Connect native backup pipeline (free route).** Blocked on phone-side setup (see "Waiting on" below).

## What to do next (v1.1)

**Route decision (2026-07-17):** use Health Connect's built-in scheduled export — it writes a `Health Connect.zip` (containing an unencrypted SQLite database) to Google Drive on a schedule. Free, no third-party app. Python stdlib (`zipfile` + `sqlite3`) reads it directly. The paid Health Sync CSV route is the documented fallback if the SQLite schema proves too unstable. Known risk (accepted): the DB schema is internal/undocumented and may change with HC updates — the adapter must fail loudly, never guess.

Phase 0 — phone/PC setup (Sweta, one-time):
1. Health Connect → Settings → Data export/backup → schedule daily export to Google Drive.
2. In Health Connect → Browse data, check which metrics Fittr writes (does HRV / stress appear, or only steps/HR/sleep?).
3. Install Google Drive for Desktop on the PC; note the local path where `Health Connect.zip` lands.
4. Share one real `Health Connect.zip` (adapter is built against a real file only).

Phase 1 (Claude): inspect the real backup — dump SQLite table schemas, map tables → metrics, document in `data/samples/SCHEMA_NOTES.md`.

Phase 2 (Claude): build `import_health_connect.py` (stdlib only): open DB read-only, aggregate to daily granularity, merge into `data/log.csv` — add new dates, fill blanks, never overwrite a non-empty cell (manual entries win). Fail loudly on schema drift. Idempotent re-runs. Scoring/rendering untouched (adapter-layer, PRD §6).

Phase 3: README usage docs; later (v3) a Windows scheduled task automates import+rebuild.

Interim option: manually add a row to `data/log.csv` from the Fittr app's numbers and run `python build_dashboard.py` to get real scores today.

## Waiting on / open questions

- [ ] Health Connect scheduled export set up on phone → Drive (Sweta)
- [ ] One real `Health Connect.zip` to build the adapter against (Sweta)
- [ ] Does Fittr write all metrics to Health Connect, or a subset? (Sweta — HC → Browse data)
- [ ] Google Drive for Desktop installed; local path of the backup zip (Sweta)
- [ ] Garmin export file for history import (v2)

## Roadmap (from PRD §8)

- **v1 — DONE (2026-07-16)**: CSV schema, scoring engine, static dashboard with sample data.
- **v1.1 — NEXT**: Health Sync pipeline + CSV parser/adapter. Blocked on open questions above.
- **v2**: Garmin history import; tune readiness weights against real personal data.
- **v3**: Auto-rebuild on new data (Windows scheduled task), weekly summary, illness early-warning flag.

## History

### 2026-07-16 — Repo created, v1 built
- Created GitHub repo: https://github.com/strategysoul/fighter (empty folder → git init → push).
- Wrote PRD.md (readiness dashboard for Fittr HART ring data).
- Planned and built v1 from the PRD:
  - `data/log.csv` — schema `date, sleep_hours, sleep_quality, hrv_ms, resting_hr, steps, stress, notes` + 30 days sample data with gaps.
  - `build_dashboard.py` — stdlib-only; 7-day rolling baselines; readiness score weighted sleep 30 / HRV 25 / resting HR 20 / stress 15 / sleep quality 10; missing metrics' weight redistributed; top-3 actions tied to the worst metrics; renders self-contained `dashboard.html` (SVG charts with baseline lines + tooltips, sortable raw table).
  - Verified: score math checks out; redistribution works with missing metrics.
- Key architecture decision: ingestion is an adapter layer — every source normalizes to `log.csv`; scoring/rendering never change per source.

### 2026-07-17 — PLAN.md introduced
- Decision: keep this living plan file; update it whenever the plan changes so any future session can pick up from here.

### 2026-07-17 — v1.1 route decided: native Health Connect backup
- Researched feasible read-only export routes. Options found: (a) Health Sync app → daily CSVs in Drive (paid, cleanest format); (b) Health Connect's native scheduled export → zip with unencrypted SQLite DB in Drive (free, undocumented schema); (c) open-source exporter apps.
- **Decision (Sweta): route (b), the free native backup.** Health Sync kept as documented fallback.
- Planned v1.1: Phase 0 phone setup → Phase 1 schema inspection → Phase 2 `import_health_connect.py` adapter (read-only, idempotent, never overwrites non-empty cells) → Phase 3 docs. Blocked on a real `Health Connect.zip`.

### 2026-07-17 — fighter-builder skill added
- `.claude/skills/fighter-builder/SKILL.md`: working rules for Claude in this repo — never invent facts, ask when in doubt, respect the adapter-layer architecture, verify before claiming done, keep PLAN.md updated, scope discipline.
