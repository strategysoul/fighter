# Health Connect backup — verified schema notes

Source: real `Health Connect.zip` (G:\My Drive\Faitttr\, exported 2026-07-17, 15MB).
Zip contains exactly one file: `health_connect_export.db` (SQLite, unencrypted). 78 tables.
All findings below were read from the actual file — nothing inferred.

## Conventions

- Timestamps: epoch **milliseconds UTC** (`start_time`, `end_time`, `time`).
- `*_zone_offset`: offset in **seconds** (observed 19800 = UTC+5:30, 14400 = UTC+4).
- `local_date`: epoch **day number** (days since 1970-01-01).
- `app_info_id` → `application_info_table.row_id`:
  | id | package |
  |----|---------|
  | 3 | com.garmin.android.apps.connectmobile |
  | 6 | com.google.android.apps.fitness |
  | 7 | **com.squats.fittr_hart** (the HART ring) |

## Metric mapping (verified 2026-07-18)

| log.csv column | Table | Value | Notes |
|---|---|---|---|
| sleep_hours | `sleep_session_record_table` (45,711 rows) | sum of merged `[start_time, end_time]` intervals per wake-date | Fittr writes 60-second micro-sessions; intervals must be merged to avoid double-counting. Wake-date rule: local end < 18:00 → that date; ≥ 18:00 → next date. Data range: 2025-12-19 → **2026-04-02 (stale!)** |
| resting_hr | `resting_heart_rate_record_table` (31 rows) | `beats_per_minute` at local date of `time` | Written by Google Fit (app 6), not Fittr. Range: 2025-11-26 → **2026-03-07 (stale)** |
| steps | `steps_record_table` (62,923 rows) | `count` summed per app per local date; daily value = **max across apps** (apps duplicate each other; summing across apps would double-count) | Google Fit current to 2026-07-17; Fittr stopped 2026-01-22 |
| hrv_ms | `heart_rate_variability_rmssd_record_table` | — | **Table exists but has 0 rows.** No app writes HRV. |
| stress | — | — | **Health Connect has no stress record type.** Never available via this route. |
| sleep_quality | — | — | Not derivable without inventing a formula; left blank. `sleep_stages_table` (stage_type per interval) exists if a defensible formula is ever wanted. |

Also present with data: `heart_rate_record_series_table` (18,787 samples, `beats_per_minute` + `epoch_millis`, parent `heart_rate_record_table`), `oxygen_saturation_record_table` (342 rows, Fittr, ended 2026-01-03), exercise sessions.

## Data-freshness problem (found 2026-07-18)

Fittr (app 7) largely stopped writing to Health Connect:
- heart rate: ended 2026-01-20 · steps: 2026-01-22 · SpO₂: 2026-01-03 · sleep: 2026-04-02
- Only Google Fit steps are current (to 2026-07-17).

→ Pipeline and importer work, but the phone-side Fittr → Health Connect sync needs fixing
(check Fittr app settings / Health Connect app permissions) before daily readiness is meaningful.
