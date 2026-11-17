# Cleaning summary

| step | rows |
|---|---|
| raw | 5000 |
| window | 4965 |
| orphans | 4788 |
| pre_release | 4761 |
| dedup | 4754 |
| train | 4376 |
| holdout | 378 |

| flag | rows |
|---|---|
| duration_invalid | 46 |
| completed_conflict | 24 |
| kids_mature | 44 |
| watch_ratio_null | 213 |

| rule | rows |
|---|---|
| blank_to_unknown | 178 |
| dropped_orphan_title | 177 |
| duration_invalid_nulled | 46 |
| dropped_outside_window | 35 |
| dropped_pre_release | 27 |
| dropped_duplicate | 7 |
