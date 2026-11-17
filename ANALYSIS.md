# Analysis record

Issues found while profiling the events export and the title catalog, and the decision taken for each.

## Events file: no problems with

All 5,000 event IDs are unique and in the right format. There are no exact duplicates, every date parses
and falls inside 17 Aug–16 Nov 2026, and there's no stray whitespace or mixed casing.

## Issues and decisions

| # | Issue | Rows | Decision |
|---|---|---|---|
| 1 | `watch_seconds` 32,887–85,372s with nothing between 3,598 and 32,887. All below 86,400, so likely seconds since midnight | 46 | Set to null, `duration_invalid=True` |
| 2 | Blank `watch_seconds` (10 of them marked completed) | 74 | Keep null |
| 3 | Marked completed after under 60s, or with no watch time | 24 after cleaning | Flag `completed_conflict`, don't change |
| 4 | Blank `device_type` / `country` | 135 / 49 | Set to `"unknown"` |
| 5 | Same member + title + date | 7 extra rows | Keep non-null, then the longest watch |
| 6 | `event_datetime` holds a date only | all | Renamed to `event_date` |
| 7 | `country` varies per event for 590 of 599 members | — | Not used as a member attribute |
| 8 | `profile_type` varies within 178 members; no `profile_id` | — | Not used as a member attribute |
| 9 | `completed` stored as text | all | Converted to boolean |
| 10 | title_ids not in the catalog: TT-0347, TT-0412, TT-0588, spread evenly across the window | 180 (177 after the date cut) | Drop and quarantine. No date cutoff applies |
| 11 | Events dated before the title's release (TT-0163, TT-0195, TT-0258) | 27 | Drop |
| 12 | Last day (16 Nov) is incomplete: 35 events vs 35–70 on other days | 35 | Window ends 15 Nov |
| 13 | Kids profile watching R / TV-MA titles | 44 | Flag `kids_mature`, keep |

## Catalog notes

- 10 titles have a blank `runtime_minutes` (104 events). `watch_ratio` is null for these.
- Two pairs of different titles share a name (The Quiet Ward, Dead Air Frequency), so always join on `title_id`.
- TT-0300 releases 2026-11-20, after the window, and has no events.

## Why `completed` isn't rebuilt

The raw flag doesn't line up with watch time: 14% of watches under 25% of runtime are marked completed,
and only about 74% of near-full watches are. The planned rule (completed when watch ≥ 90% of runtime)
was tested against the catalog and dropped:

- **Films:** no valid watch reaches 70% of runtime, so all 1,858 film events would become `False`.
- **Series:** runtime is per episode and events have no episode ID. 875 series events run longer than one episode.

Kept: `completed_raw`, plus `watch_ratio` and `completed_conflict`.

**Open decision:** use `completed_raw` as the label, predict watch time / `watch_ratio` instead, or
find out how the source system sets the completed flag.

## Split

- Train: 2026-08-17 to 2026-11-08 (4,376)
- Holdout: Monday 2026-11-09 to Sunday 2026-11-15 (378), a full week the model never sees
