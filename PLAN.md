# PLAN.md — Living Plan & History

> Running log of what was planned, what's done, and what's next.
> Updated every time the plan changes. Read this first when resuming work on the repo.

## Current status (as of 2026-07-17)

**v1 is done and pushed.** The repo has a working prototype: sample data, scoring engine, static dashboard.

**Next up: v1.1 — Health Sync pipeline.** Blocked on phone-side setup (see "Waiting on" below).

## What to do next (v1.1)

Phone/PC setup (Sweta):
1. Install Health Sync on Android; configure export from Health Connect → Google Drive as daily CSVs.
2. In Health Connect → Browse data, check which metrics Fittr writes (does HRV / stress appear, or only steps/HR/sleep?).
3. Install Google Drive for Desktop on the PC so the export folder syncs locally.
4. Share one real Health Sync CSV export.

Then (Claude): build the parser/adapter that converts the Health Sync CSV into the `data/log.csv` schema. Scoring/rendering don't change (adapter-layer design, PRD §6).

Interim option: manually add a row to `data/log.csv` from the Fittr app's numbers and run `python build_dashboard.py` to get real scores today.

## Waiting on / open questions (from PRD §7)

- [ ] Does Health Sync export HRV and stress from Health Connect? (Sweta)
- [ ] Sample Health Sync CSV file to build the parser against (Sweta)
- [ ] Does Fittr write all metrics to Health Connect, or a subset? (Sweta)
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
