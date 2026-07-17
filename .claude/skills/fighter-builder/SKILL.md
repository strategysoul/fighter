---
name: fighter-builder
description: Working rules for building the HART ring readiness dashboard in this repo — use whenever planning, writing, or changing code here
---

# Fighter Builder — Working Rules

Follow these whenever building or changing anything in this repo.

## 1. Never invent facts
- Do not guess file formats, API behavior, or metric availability. The Fittr/Health Sync/Health Connect landscape is full of unknowns — treat anything unverified as an open question, not an assumption.
- Never fabricate health data, baselines, or numbers. Sample data must be clearly labeled as sample data.
- If a claim can't be verified from the repo, a real file, or a check Sweta can run, say "unverified" and add it to PLAN.md's open questions.

## 2. When in doubt, ask first — then execute
- Ambiguous requirement, missing input file, or a decision with more than one reasonable path → ask Sweta before writing code.
- Don't ask about things with an obvious conventional default; pick it and state the choice.

## 3. Respect the architecture (PRD §6)
- Ingestion is an adapter layer: every data source (Health Sync CSV, Garmin export, manual entry) normalizes into the `data/log.csv` schema. Never let source-specific logic leak into scoring or rendering.
- Python stdlib only. No third-party dependencies, no server, no cloud. Output stays a single self-contained `dashboard.html`.
- Plain CSV storage — never switch to a database or binary format.

## 4. Verify before claiming done
- Run `python build_dashboard.py` after every change; open/inspect the output.
- Check score math against hand-computed values and test the missing-data path (blank a metric, rebuild).
- Report failures honestly — never say "done" for untested code.

## 5. Keep the paper trail
- Update `PLAN.md` (status, next steps, history) whenever a plan is made, changed, or a milestone lands — same commit as the work.
- Build parsers against real sample files only; when one arrives, commit an anonymized copy under `data/samples/`.

## 6. Scope discipline
- This is a single-user, local, free tool. Reject scope creep toward accounts, hosting, mobile apps, or real-time data (PRD non-goals).
- Habit guidance only — never produce medical/diagnostic claims or alarming health language.
- Prefer the smallest change that satisfies the PRD story being worked on; ship in the PRD's phase order (v1.1 → v2 → v3).
