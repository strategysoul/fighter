"""Read-only Health Connect backup inspector/importer.

The database schema is internal and undocumented. The verified mapping is
intentionally empty until a real backup has been inspected; imports fail
loudly rather than guessing.
"""
import argparse
import csv
import datetime as dt
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "log.csv"
DEFAULT_BACKUP_PATH = Path(r"G:\My Drive\Faitttr\Health Connect.zip")
METRICS = ("sleep_hours", "sleep_quality", "hrv_ms", "resting_hr", "steps", "stress")
# Verified against the real backup of 2026-07-17 — see data/samples/SCHEMA_NOTES.md.
# Timestamps are epoch ms UTC; *_zone_offset is seconds; hrv/stress/sleep_quality
# are absent from this backup (empty table / no HC record type / not derivable).
SCHEMA_MAPPING = {
    "sleep_hours": {"table": "sleep_session_record_table", "date_column": "end_time", "value_column": "start_time"},
    "resting_hr": {"table": "resting_heart_rate_record_table", "date_column": "time", "value_column": "beats_per_minute"},
    "steps": {"table": "steps_record_table", "date_column": "start_time", "value_column": "count"},
}


class ImportErrorWithContext(RuntimeError):
    pass


def _quote(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def _open_database(source):
    path = Path(source).expanduser()
    if not path.exists():
        raise ImportErrorWithContext(f"Health Connect backup not found: {path}")
    temp_dir = tempfile.TemporaryDirectory(prefix="health-connect-")
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            candidates = [m for m in archive.infolist() if not m.is_dir() and Path(m.filename).suffix.lower() in {".db", ".sqlite", ".sqlite3"}]
            if len(candidates) != 1:
                names = ", ".join(m.filename for m in candidates) or "none"
                temp_dir.cleanup()
                raise ImportErrorWithContext(f"Expected exactly one SQLite database in {path}; found {len(candidates)} ({names}).")
            db_path = Path(temp_dir.name) / Path(candidates[0].filename).name
            with archive.open(candidates[0]) as source_file, db_path.open("wb") as dest:
                shutil.copyfileobj(source_file, dest)
    else:
        db_path = path
    try:
        connection = sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        temp_dir.cleanup()
        raise ImportErrorWithContext(f"Could not open SQLite database read-only: {exc}") from exc
    return connection, temp_dir


def inspect_schema(connection):
    tables = {}
    for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"):
        columns = connection.execute(f"PRAGMA table_info({_quote(name)})").fetchall()
        tables[name] = [(row[1], row[2], bool(row[3]), row[4]) for row in columns]
    return tables


def print_schema(connection):
    tables = inspect_schema(connection)
    if not tables:
        print("No SQLite tables found.")
    for name, columns in tables.items():
        print(f"TABLE {name}")
        for column, kind, required, default in columns:
            print(f"  {column}: {kind or 'unspecified'}" + (" NOT NULL" if required else ""))
        print("  SAMPLE")
        for row in connection.execute(f"SELECT * FROM {_quote(name)} LIMIT 3"):
            print(f"    {row!r}")
    return tables


def _validate_mapping(connection):
    tables = inspect_schema(connection)
    if not SCHEMA_MAPPING:
        raise ImportErrorWithContext("No verified Health Connect schema mapping is configured. Run --inspect on the real backup, document exact mappings in data/samples/SCHEMA_NOTES.md, then populate SCHEMA_MAPPING. Found tables: " + (", ".join(tables) or "none"))
    for metric, spec in SCHEMA_MAPPING.items():
        table = spec.get("table")
        if metric not in METRICS or table not in tables:
            raise ImportErrorWithContext(f"Schema mapping for {metric!r} refers to missing table {table!r}. Found tables: {', '.join(tables) or 'none'}")
        columns = {column for column, *_ in tables[table]}
        required = {spec.get("date_column"), spec.get("value_column")} - {None}
        missing = sorted(required - columns)
        if missing:
            raise ImportErrorWithContext(f"Schema drift in table {table!r}: missing columns {missing}. Found columns: {', '.join(sorted(columns)) or 'none'}")


def _local_dt(epoch_ms, offset_seconds):
    tz = dt.timezone(dt.timedelta(seconds=offset_seconds or 0))
    return dt.datetime.fromtimestamp(epoch_ms / 1000, tz)


def extract_daily(connection):
    _validate_mapping(connection)
    daily = {}

    def put(date, metric, value):
        daily.setdefault(date.isoformat(), {})[metric] = value

    # sleep: merge overlapping/adjacent session intervals per wake-date
    # (Fittr writes 60-second micro-sessions; naive summing double-counts).
    # Wake-date rule: local end before 18:00 -> that date, else next date.
    intervals_by_date = {}
    for start, end, offset in connection.execute(
        "SELECT start_time, end_time, end_zone_offset FROM sleep_session_record_table"
    ):
        local_end = _local_dt(end, offset)
        wake = local_end.date() if local_end.hour < 18 else local_end.date() + dt.timedelta(days=1)
        intervals_by_date.setdefault(wake, []).append((start, end))
    for wake, intervals in intervals_by_date.items():
        intervals.sort()
        total_ms = 0
        cur_start, cur_end = intervals[0]
        for start, end in intervals[1:]:
            if start <= cur_end:
                cur_end = max(cur_end, end)
            else:
                total_ms += cur_end - cur_start
                cur_start, cur_end = start, end
        total_ms += cur_end - cur_start
        put(wake, "sleep_hours", round(total_ms / 3_600_000, 2))

    for time_ms, offset, bpm in connection.execute(
        "SELECT time, zone_offset, beats_per_minute FROM resting_heart_rate_record_table"
    ):
        put(_local_dt(time_ms, offset).date(), "resting_hr", bpm)

    # steps: sum per app per local date, then take the max across apps —
    # apps mirror each other's data, so summing across apps double-counts.
    per_app = {}
    for start, offset, count, app in connection.execute(
        "SELECT start_time, start_zone_offset, count, app_info_id FROM steps_record_table"
    ):
        day = _local_dt(start, offset).date()
        per_app[(day, app)] = per_app.get((day, app), 0) + (count or 0)
    best = {}
    for (day, _app), total in per_app.items():
        best[day] = max(best.get(day, 0), total)
    for day, total in best.items():
        put(day, "steps", total)

    return daily


def merge_log(daily, log_path=LOG_PATH):
    """Merge daily values, filling blanks only and preserving manual entries."""
    with log_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames, rows = reader.fieldnames or [], list(reader)
    expected = ["date", *METRICS, "notes"]
    if fieldnames != expected:
        raise ImportErrorWithContext(f"Unexpected log.csv header: {fieldnames!r}; expected {expected!r}")
    by_date = {row["date"]: row for row in rows}
    existing = set(by_date)
    added = updated = 0
    for date, values in sorted(daily.items()):
        dt.date.fromisoformat(date)
        row = by_date.get(date)
        if row is None:
            row = {field: "" for field in fieldnames}
            row["date"] = date
            by_date[date] = row
            added += 1
        changed = False
        for metric, value in values.items():
            if metric in METRICS and value is not None and not row[metric].strip():
                row[metric] = str(value)
                changed = True
        if changed and date in existing:
            updated += 1
    with log_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(by_date.values(), key=lambda row: row["date"]))
    return added, updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", nargs="?", type=Path, default=DEFAULT_BACKUP_PATH)
    parser.add_argument("--inspect", action="store_true", help="dump actual tables, columns, and sample rows")
    args = parser.parse_args()
    connection, temp_dir = _open_database(args.zip_path)
    try:
        if args.inspect:
            print_schema(connection)
            return
        daily = extract_daily(connection)
        added, updated = merge_log(daily)
        found = sorted({metric for values in daily.values() for metric in values})
        print(f"Dates added: {added}; existing dates updated: {updated}")
        print(f"Metrics found: {', '.join(found) or 'none'}")
        print(f"Metrics missing: {', '.join(m for m in METRICS if m not in found) or 'none'}")
    finally:
        connection.close()
        temp_dir.cleanup()


if __name__ == "__main__":
    try:
        main()
    except (ImportErrorWithContext, sqlite3.Error, zipfile.BadZipFile) as exc:
        raise SystemExit(f"Health Connect import failed: {exc}")
