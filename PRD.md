# Product Requirements Document: HART Ring Actionable Health Dashboard

**Author**: Sweta
**Date**: 2026-07-16
**Status**: Draft
**Stakeholders**: Sweta (user, builder, sole customer)

### 1. Executive Summary

A personal, local-first dashboard that turns raw Fittr HART ring data (sleep, HRV, resting HR, steps, stress) into one daily readiness score and 2–3 concrete actions, so the data actually changes daily habits instead of sitting unread in the Fittr app. Data flows automatically from the ring via Health Connect → Health Sync → Google Drive → PC, with no manual logging.

### 2. Background & Context

- The Fittr HART ring collects rich metrics, but the app presents raw numbers with no personal baselines or guidance; the user reports not reading or acting on them.
- Fittr has **no public API**; community reports describe data as "trapped in the app." However, the user has verified the app **syncs to Health Connect** on Android, which unlocks an automated pipeline.
- Health Connect has no cloud API — data is on-device only — so a bridge app (Health Sync) exports daily CSVs to Google Drive, which sync to the PC via Google Drive for Desktop.
- Historical Garmin data exists and can be bulk-imported once from Garmin Connect's export to seed personal baselines.
- A prototype exists: `data/log.csv` + `build_dashboard.py` generating a static `dashboard.html` with a readiness score, action list, 30-day trend charts, and raw log table.

### 3. Objectives & Success Metrics

**Goals**:
1. Zero-touch daily data pipeline: ring data lands on the PC as CSV with no manual steps.
2. Every morning, one glance answers: "How recovered am I, and what 2–3 things should I do today?"
3. All metrics scored against the user's own 7-day/30-day baselines, not population averages.

**Non-Goals**:
1. No mobile app of our own (Health Sync covers device-side; avoids an Android dev project).
2. No cloud hosting, accounts, or multi-user support — single-user, local, free to run.
3. No medical diagnosis or clinical claims — habit guidance only.
4. No intraday/real-time metrics in v1 — daily granularity is sufficient for the push/rest decision.

**Success Metrics**:
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Manual effort per day | N/A (data unread) | 0 min (pipeline), <1 min (glance) | Self-report |
| Dashboard checked | ~0 days/week | ≥5 days/week for 4 weeks | Self-report / habit streak |
| Data freshness | — | Previous night's data visible by 9am | Timestamp check |
| Acted on a daily recommendation | 0 | ≥3 days/week | Notes column in log |

### 4. Target Users & Segments

Single user: Sweta — Fittr HART ring wearer, Android phone, Windows PC, former Garmin user, comfortable running a Python script but wants near-zero daily friction.

### 5. User Stories & Requirements

**P0 — Must Have**:
| # | User Story | Acceptance Criteria |
|---|-----------|-------------------|
| 1 | When I wake up, I want ring data on my PC automatically, so I never log data by hand | Health Sync exports CSV to Drive daily; Drive for Desktop syncs; parser ingests sleep, HR/resting HR, HRV, steps, stress without manual steps |
| 2 | When I open the dashboard, I want a single 0–100 readiness score, so I know whether to push or rest | Score computed from sleep duration/quality, HRV vs 7-day baseline, resting HR vs baseline, stress; color-coded (green/amber/red) |
| 3 | When my score is low, I want to know why and what to do, so I can act, not just observe | Top 3 actions shown, each tied to the metric that dragged the score (e.g., "HRV below baseline — keep today easy") |
| 4 | When I view trends, I want 30-day charts vs my baseline, so I see direction not noise | Line charts for sleep, HRV, resting HR, steps with hover tooltips |

**P1 — Should Have**:
| # | User Story | Acceptance Criteria |
|---|-----------|-------------------|
| 5 | As a former Garmin user, I want my history imported once, so baselines are meaningful from day one | One-time Garmin Connect export parsed into the same CSV schema |
| 6 | When a metric is missing from Health Sync export, I want a fallback, so the dashboard never goes blind | Screenshot-to-CSV logging path (prototyped) fills gaps |
| 7 | When I want detail, I want the raw log, so I can audit any number | Sortable raw table in dashboard; data stays in plain CSV |

**P2 — Nice to Have / Future**:
| # | User Story | Acceptance Criteria |
|---|-----------|-------------------|
| 8 | Weekly email/summary of trends and habit streaks | Weekly rollup view with week-over-week deltas |
| 9 | Illness early warning | Flag when resting HR + skin temp deviate together for 2+ days |
| 10 | Auto-rebuild on new data | Scheduled task rebuilds dashboard when new CSV lands in Drive folder |

### 6. Solution Overview

```
Fittr HART ring → Fittr app → Health Connect (on-device)
  → Health Sync (bridge app) → daily CSV in Google Drive
  → Google Drive for Desktop (PC folder)
  → build_dashboard.py (parse → normalize to log.csv → score → render)
  → dashboard.html (static, opens in browser)
```

Key decisions:
- **Plain CSV storage** — no lock-in, Excel-compatible, trivially portable.
- **Static HTML dashboard** — no server, no dependencies beyond Python stdlib.
- **Baseline-relative scoring** — readiness = weighted parts: sleep duration (30), HRV vs 7-day baseline (25), resting HR vs baseline (20), stress (15), sleep quality (10).
- **Ingestion is an adapter layer** — Health Sync CSV, Garmin export, and screenshot logging all normalize to the same `log.csv` schema, so the scoring/dashboard layers never change.

### 7. Open Questions

| Question | Owner | Deadline |
|----------|-------|----------|
| Does Health Sync export HRV and stress from Health Connect (or only steps/HR/sleep)? | Sweta — install & check | Before v1.1 build |
| Exact CSV format Health Sync produces (need a sample file to build the parser) | Sweta — share one export | Before v1.1 build |
| Does Fittr write *all* metrics to Health Connect, or a subset? (Check HC → Browse data) | Sweta | Before v1.1 build |
| Garmin export format for the history import | Claude — parse when provided | v2 |

### 8. Timeline & Phasing

- **v1 (done — prototype)**: CSV schema, scoring engine, static dashboard with sample data.
- **v1.1 (next)**: Health Sync pipeline — user sets up phone-side export + Drive for Desktop; Claude builds the CSV parser/adapter against a real sample file. *Blocked on the three open questions above.*
- **v2**: Garmin history import; tune readiness weights against real personal data.
- **v3**: Auto-rebuild on new data (Windows scheduled task), weekly summary, illness early-warning flag.
