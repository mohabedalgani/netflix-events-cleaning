# Netflix viewing events: cleaning and train/holdout split

Cleans `Netflix_viewing_events_export_17_Aug_to_16_Nov_2026.csv` (5,000 events) against
`Netflix_title_catalog_November_2026.csv` (300 titles), then splits the result by date for model training.

```
python scripts/clean_events.py EVENTS_CSV CATALOG_CSV output
```

The script stops if any step's row count differs from the expected value.

## Result

| step | rows |
|---|---|
| raw | 5,000 |
| window 2026-08-17 to 2026-11-15 | 4,965 |
| drop orphan title_ids (TT-0347, TT-0412, TT-0588) | 4,788 |
| drop pre-release events | 4,761 |
| dedupe member + title + date | 4,754 |
| **train** (event_date ≤ 2026-11-08) | **4,376** |
| **holdout** (2026-11-09 to 2026-11-15) | **378** |

## Outputs (`output/`)

- `train.csv`, `holdout.csv`: cleaned events with catalog fields joined in
- `changes_log.csv`: every dropped or changed row, with the rule that applied
- `quarantine_orphan_titles.csv`: events whose title_id isn't in the catalog
- `summary.md`: counts per step, flag and rule

## Notes

- `completed` is **not** rebuilt from runtime. It is kept as `completed_raw`. Film runtimes are
  84–134 min, but valid watch times never go past ~60 min, and series runtime is per episode while
  events have no episode ID. `watch_ratio` is added as a separate column (values above 1 for series mean multi-episode sessions).
- Compute member- and title-level aggregates on train only, then join them onto holdout.
- Join titles on `title_id`, never `title_name`: two pairs of different titles share a name.
- Open decision: what the model's completion label should be. See `ANALYSIS.md`.
