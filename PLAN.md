# PLAN.md — Living Plan & History

> Running log of what was planned, what's done, and what's next.
> Updated every time the plan changes. Read this first when resuming work on the repo.

## Current status (as of 2026-07-18)

**v1 is done and pushed.** The repo has a working prototype: sample data, scoring engine, static dashboard.

**v1.1 importer is DONE; pipeline verified end-to-end** (phone export → Drive → import → dashboard; 235 dates imported). **Waiting overnight to confirm the Fittr sync fix**: Sweta re-enabled Fittr → Health Connect sync on 2026-07-18, but the same-day re-export still contained no new Fittr data (sleep still ends 2026-04-02) — likely because Fittr only writes going forward. Tomorrow morning's export is the real test.

**Tomorrow (2026-07-19): re-run `python import_health_connect.py` then `python build_dashboard.py`** on the fresh export. If last night's sleep appears → sync fixed, readiness score goes live. If not → debug on phone: HC → Browse data → Sleep; Fittr app HC toggle; HC → App permissions → Fittr.

## What to do next (v1.1)

**Route decision (2026-07-17):** use Health Connect's built-in scheduled export — it writes a `Health Connect.zip` (containing an unencrypted SQLite database) to Google Drive on a schedule. Free, no third-party app. Python stdlib (`zipfile` + `sqlite3`) reads it directly. The paid Health Sync CSV route is the documented fallback if the SQLite schema proves too unstable. Known risk (accepted): the DB schema is internal/undocumented and may change with HC updates — the adapter must fail loudly, never guess.

Phase 0 — phone/PC setup (Sweta, one-time):
1. Health Connect → Settings → Data export/backup → schedule daily export to Google Drive.
2. In Health Connect → Browse data, check which metrics Fittr writes (does HRV / stress appear, or only steps/HR/sleep?).
3. Install Google Drive for Desktop on the PC; note the local path where `Health Connect.zip` lands.
4. Share one real `Health Connect.zip` (adapter is built against a real file only).

Phase 1 (blocked): inspect the real backup, dump SQLite table schemas, map tables to metrics, and document the verified mapping in `data/samples/SCHEMA_NOTES.md`.

Phase 2 (in progress): the adapter shell supports read-only ZIP/SQLite inspection, exact mapping validation, fail-loud errors, and non-clobbering CSV merge. After Phase 1, implement verified daily aggregation and import summary. Scoring/rendering remain untouched.

Phase 3: README usage docs; later (v3) a Windows scheduled task automates import+rebuild.

Interim option: manually add a row to `data/log.csv` from the Fittr app's numbers and run `python build_dashboard.py` to get real scores today.

## Waiting on / open questions

- [x] Health Connect scheduled export set up on phone → Drive (`G:\My Drive\Faitttr\Health Connect.zip`)
- [x] Real backup obtained; schema verified and documented in `data/samples/SCHEMA_NOTES.md`
- [x] What Fittr writes to HC: sleep, HR, steps, SpO₂ — but sync mostly stopped Jan–Apr 2026. **HRV never written; stress has no HC record type; sleep_quality not derivable.**
- [x] Read-only adapter with verified mapping, non-clobbering merge, idempotent reruns
- [ ] **Confirm Fittr sync fix worked**: re-run import on 2026-07-19 morning export; last night's sleep should appear (Sweta re-enabled sync 2026-07-18; same-day export had no new Fittr data yet)
- [ ] Decide fallback for HRV/stress: they will never come via Health Connect — accept a 3-metric score (weights auto-redistribute), or screenshot-logging path (PRD P1 #6)
- [ ] Garmin export file for history import (v2)

## Roadmap (from PRD §8)

- **v1 — DONE (2026-07-16)**: CSV schema, scoring engine, static dashboard with sample data.
- **v1.1 - IN PROGRESS**: native Health Connect backup adapter shell complete; real schema inspection and metric extraction pending the backup.
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


### 2026-07-17 - v1.1 adapter shell added
- Added `import_health_connect.py` with ZIP/SQLite read-only handling, schema inspection, explicit fail-loud behavior, and safe CSV merge support.
- Added `data/samples/SCHEMA_NOTES.md` as the Phase 1 evidence record.
- No Health Connect mapping was invented; importing remains blocked until a real backup is supplied.


### 2026-07-18 — v1.1 importer completed against real backup
- Inspected real `Health Connect.zip`: SQLite DB, 78 tables; verified mapping documented in `data/samples/SCHEMA_NOTES.md`.
- Implemented `extract_daily`: sleep = merged session intervals per wake-date (Fittr writes 60-second micro-sessions); resting HR direct; steps = per-app daily sums with max-across-apps (dedupe). Wiped fake sample data from `data/log.csv` (recoverable in git history); imported 234 real dates. Re-run verified idempotent; source zip untouched.
- Dashboard now handles a no-scorable-metrics day (grey "–" score) — latest days only have steps.
- **Finding: Fittr stopped syncing to Health Connect** (HR ended 2026-01-20, steps 2026-01-22, SpO₂ 2026-01-03, sleep 2026-04-02). Only Google Fit steps are current. HRV table empty; no stress record type exists in HC. → New blockers logged above.

### 2026-07-18 (later) — sync fix awaiting overnight confirmation
- Sweta re-enabled Fittr → Health Connect sync and triggered a fresh export (14:51).
- Import ran clean (1 new date: steps only), but the fresh backup still had no new Fittr data — sleep still ends 2026-04-02, Fittr HR 2026-01-20. Hypothesis: Fittr writes going forward only, so tonight's sleep is the first real test.
- Next session: re-run import + rebuild on the morning export; if sleep appears, v1.1 is fully live. If not, debug phone-side (HC → Browse data / Fittr toggle / HC permissions).

### 2026-07-18 - plan updated
- Confirmed the repository has no real Health Connect ZIP/SQLite backup yet.
- Kept Phase 1 explicitly blocked; no table or column mapping will be inferred.
- Next action: complete Phase 0 phone/Drive setup and provide one real backup, then run `python import_health_connect.py <path> --inspect`.
