"""Clean Netflix viewing events (17 Aug - 16 Nov 2026) and split into train/holdout.

Usage: python clean_events.py EVENTS_CSV CATALOG_CSV OUT_DIR
"""
import sys, os
import pandas as pd

EXPECTED = {"window": 4965, "orphans": 4788, "pre_release": 4761, "dedup": 4754,
            "train": 4376, "holdout": 378}
WINDOW_START, WINDOW_END = "2026-08-17", "2026-11-15"
HOLDOUT_START = "2026-11-09"
MAX_VALID_WATCH = 3600

events_path, catalog_path, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
ev = pd.read_csv(events_path, dtype=str, keep_default_na=False)
cat = pd.read_csv(catalog_path, dtype=str, keep_default_na=False)
log, counts = [], [("raw", len(ev))]

def record(rows, rule, col=None, new=None):
    for _, r in rows.iterrows():
        log.append({"event_id": r["event_id"], "rule": rule,
                    "column": col or "", "old_value": r[col] if col else "",
                    "new_value": "" if new is None else new})

def check(step, df):
    counts.append((step, len(df)))
    if step in EXPECTED and len(df) != EXPECTED[step]:
        sys.exit(f"STOP: {step} has {len(df)} rows, expected {EXPECTED[step]}")
    print(f"{step:12s} {len(df):5d}")

# 1. Date window
ev = ev.rename(columns={"event_datetime": "event_date"})
out_win = ev[(ev.event_date < WINDOW_START) | (ev.event_date > WINDOW_END)]
record(out_win, "dropped_outside_window")
ev = ev.drop(out_win.index); check("window", ev)

# 2. Orphan titles
orph = ev[~ev.title_id.isin(cat.title_id)]
record(orph, "dropped_orphan_title")
orph.to_csv(f"{out}/quarantine_orphan_titles.csv", index=False)
ev = ev.drop(orph.index); check("orphans", ev)

# 3. Types
ev["completed"] = ev.completed.map({"True": True, "False": False}).astype("boolean")
ev["watch_seconds"] = pd.to_numeric(ev.watch_seconds.replace("", None)).astype("Int64")

# 4. Impossible durations
bad = ev[ev.watch_seconds > MAX_VALID_WATCH]
record(bad, "duration_invalid_nulled", "watch_seconds", "")
ev["duration_invalid"] = ev.event_id.isin(bad.event_id)
ev.loc[ev.duration_invalid, "watch_seconds"] = pd.NA
print(f"{'durations':12s} {len(bad):5d} nulled")

# 5. Join catalog
ev = ev.merge(cat[["title_id", "title_type", "release_date", "runtime_minutes",
                   "maturity_rating"]], on="title_id", how="left", validate="m:1")
ev["runtime_minutes"] = pd.to_numeric(ev.runtime_minutes.replace("", None)).astype("Int64")

# 6. Pre-release events
pre = ev[ev.event_date < ev.release_date]
record(pre, "dropped_pre_release")
ev = ev.drop(pre.index); check("pre_release", ev)

# 7. Duplicates: keep non-null watch, then the higher value
key = ["member_id", "title_id", "event_date"]
ev = ev.assign(_has=ev.watch_seconds.notna(), _w=ev.watch_seconds.fillna(-1))
ev = ev.sort_values(key + ["_has", "_w", "event_id"], ascending=[True]*3 + [False, False, True])
dups = ev[ev.duplicated(key, keep="first")]
record(dups, "dropped_duplicate")
ev = ev.drop(dups.index).drop(columns=["_has", "_w"]); check("dedup", ev)

# 8. completed: keep raw, add ratio and conflict flag
ev = ev.rename(columns={"completed": "completed_raw"})
ev["watch_ratio"] = (ev.watch_seconds.astype("Float64") /
                     (ev.runtime_minutes.astype("Float64") * 60)).round(4)
ev["completed_conflict"] = (ev.completed_raw == True) & (
    ev.watch_seconds.isna() | (ev.watch_seconds < 60))
ev["completed_conflict"] = ev.completed_conflict.fillna(False).astype(bool)

# 9. Blank categories
for col in ["device_type", "country"]:
    blank = ev[ev[col] == ""]
    record(blank, "blank_to_unknown", col, "unknown")
    ev.loc[ev[col] == "", col] = "unknown"

# 10. Kids profile on mature titles
ev["kids_mature"] = (ev.profile_type == "kids") & ev.maturity_rating.isin(["R", "TV-MA"])

# Split
ev = ev.sort_values("event_id")
train, hold = ev[ev.event_date < HOLDOUT_START], ev[ev.event_date >= HOLDOUT_START]
check("train", train); check("holdout", hold)
train.to_csv(f"{out}/train.csv", index=False)
hold.to_csv(f"{out}/holdout.csv", index=False)
pd.DataFrame(log).to_csv(f"{out}/changes_log.csv", index=False)

flags = {f: int(ev[f].sum()) for f in ["duration_invalid", "completed_conflict", "kids_mature"]}
flags["watch_ratio_null"] = int(ev.watch_ratio.isna().sum())
with open(f"{out}/summary.md", "w") as f:
    f.write("# Cleaning summary\n\n| step | rows |\n|---|---|\n")
    f.writelines(f"| {s} | {n} |\n" for s, n in counts)
    f.write("\n| flag | rows |\n|---|---|\n")
    f.writelines(f"| {k} | {v} |\n" for k, v in flags.items())
    f.write("\n| rule | rows |\n|---|---|\n")
    f.writelines(f"| {k} | {v} |\n" for k, v in pd.DataFrame(log).rule.value_counts().items())
print(flags)
