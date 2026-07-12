# Population Aerotaxis Analysis Guide

## Overview

This guide covers the temporal (non-spatial) analysis of the aerotaxis pipeline:
behavioural state changes locked to **global plate-level gas shifts**. There are
no gradients, no odor positions and no chemotaxis index — behaviour is described
purely as a function of gas state and time relative to each gas shift.

Two entry points, both built on the **same tidy table**:

- **`toolscripts/utils/aerotaxis_analysis.py`** — reusable functions (import in a
  notebook/script, or run as a CLI). This is where the analysis logic lives.
- **`Aerotaxis_population_grouped.ipynb`** — a thin notebook that imports the
  module and shows the standard plots interactively.

## Input: the tidy results table

Produced by `create_results_dict_server.py` from all per-crop
`temporal_features.csv` files:

```
aerotaxis_results.{parquet,csv,pkl}
```

| Column | Meaning |
|---|---|
| `Condition` | top-level folder (e.g. genotype / paradigm) |
| `Recording` | recording folder |
| `Crop_ID` | per-worm track id |
| `Frame` | frame index (0-based) |
| `Time_Seconds` | `t0_offset_s + Frame / fps` |
| `O2_State` | gas state from the `aerotaxis:` protocol (e.g. `7pct_O2`, `21pct_O2`) |
| `Forward_Velocity` | signed speed (mm/s); negative during reversals |
| `Reversal_Active` | 1 while reversing, else 0 |
| `Turn_Active` | 1 during a turn/coil, else 0 |

Assumptions: one row per frame; `Reversal_Active`/`Turn_Active` are 0/1 so their
means are fractions of time.

## Quick start (CLI)

```bash
# from the dataset folder, after create_results_dict_server.py
python /path/to/toolscripts/utils/aerotaxis_analysis.py aerotaxis_results.parquet --outdir analysis
```

Writes to `analysis/`:
- `per_state_summary.csv` + `.png` — mean speed, reversal fraction, turn fraction per `O2_State` × `Condition`
- `transition_triggered_forward_velocity.csv` + `.png` — feature aligned to each gas shift

## The analysis primitives (`aerotaxis_analysis.py`)

- **`load_results(path)`** — load a combined results file, or scan a dataset
  folder for `*/output/temporal_features.csv` and concatenate.
- **`per_state_summary(df, by=("Condition","O2_State"))`** — mean
  `Forward_Velocity`, `reversal_fraction`, `turn_fraction`, frame/crop counts.
- **`find_transitions(df)`** — one row per gas shift per crop
  (`from_state`, `to_state`, `Frame`, `Time_Seconds`).
- **`transition_triggered_average(df, feature, pre_s, post_s, fps, transition=None)`**
  — long tidy frame with a `rel_time_s` axis (t=0 at the shift); feed straight to
  `seaborn.lineplot` for mean ± 95% CI across crops. `transition="7pct_O2->21pct_O2"`
  filters to one shift type (e.g. the O2-up pulse onset).
- **`plot_per_state_summary` / `plot_transition_triggered`** — seaborn helpers.

## Notebook steps

1. **Load** — set `RESULTS` to your `aerotaxis_results.*` file (or a dataset folder).
2. **Per-state summary** — table of behaviour per gas state.
3. **Bar plots** — speed / reversal / turn fraction per state, split by condition.
4. **Transition-triggered averages** — the O2 on/off response dynamics; swap the
   `feature` argument for `Reversal_Active` or `Turn_Active`.
5. **Per-crop viewer** — ipywidgets dropdown; time series with the gas protocol shaded.
6. **Save** — tidy CSV summaries for R / sharing.

## Extending

- **Different gas paradigm:** nothing changes here — edit the `aerotaxis:` block in
  `config.yaml` and re-run the pipeline; `O2_State` follows automatically.
- **New metric:** add a column upstream (or compute in the notebook) and pass its
  name to `transition_triggered_average` / `per_state_summary`.

**Required libraries:** pandas, numpy, seaborn, matplotlib, ipywidgets, pyarrow (for parquet).
