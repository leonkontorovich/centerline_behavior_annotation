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
| `Frame` | **absolute** recording frame (from SWC `track.txt`), so crops share one clock |
| `Time_Seconds` | **absolute** recording time (s), from `track.txt` `time_imputed_seconds` |
| `O2_State` | gas state from the `aerotaxis:` protocol at that absolute time (e.g. `7pct_O2`, `21pct_O2`, `pre_protocol`) |
| `Forward_Velocity` | signed speed (mm/s) from the arena X,Y trajectory; negative during reversals |
| `Reversal_Active` | 1 while reversing, else 0 |
| `Turn_Active` | 1 during a turn/coil, else 0 |
| `Reversal_Onset` | 1 on the frame a reversal begins (for reaction-latency analysis) |
| `Bend_Frequency` | body-bend frequency (Hz) from the Hilbert transform (locomotor arousal) |
| `Bend_Amplitude` | body-bend amplitude (curvature units) from the Hilbert envelope |

Assumptions: one row per frame; `Reversal_Active`/`Turn_Active` are 0/1 so their
means are fractions of time. `Bend_*` may be NaN for crops whose kymogram was too
poor for the Hilbert transform.

## Quick start (CLI)

```bash
# from the dataset folder, after create_results_dict_server.py
python /path/to/toolscripts/utils/aerotaxis_analysis.py \
    aerotaxis_results.parquet --outdir analysis --pulse_state 21pct_O2
```

Writes to `analysis/`:
- `per_state_summary.csv` + `.png` — speed, reversal/turn fraction, bend Hz, reversal onsets/min per `O2_State` × `Condition`
- `transition_triggered_<feature>.csv` + `.png` — each feature aligned to the gas shifts
- `reversal_reaction.csv` — latency from each `--pulse_state` onset to the first reversal

## The analysis primitives (`aerotaxis_analysis.py`)

- **`load_results(path)`** — load a combined results file, or scan a dataset
  folder for `*/output/temporal_features.csv` and concatenate.
- **`per_state_summary(df, by=("Condition","O2_State"), fps=10)`** — mean
  `Forward_Velocity`, `reversal_fraction`, `turn_fraction`, `mean_bend_frequency_hz`,
  `reversal_onsets_per_min`, frame/crop counts.
- **`find_transitions(df)`** — one row per gas shift per crop
  (`from_state`, `to_state`, `Frame`, `Time_Seconds`).
- **`transition_triggered_average(df, feature, pre_s, post_s, fps, transition=None)`**
  — long tidy frame with a `rel_time_s` axis (t=0 at the shift); feed straight to
  `seaborn.lineplot` for mean ± 95% CI across crops. `feature` can be any continuous
  column (`Forward_Velocity`, `Bend_Frequency`, `Reversal_Active`, …); `transition=
  "7pct_O2->21pct_O2"` filters to one shift type (the O2-up pulse onset).
- **`reversal_reaction(df, to_state, window_s, fps)`** — per crop/pulse, latency (s)
  from each transition into `to_state` to the first reversal onset within `window_s`
  (generalises `curvature/src/rev_reaction.py` to the config-driven protocol).
- **`plot_per_state_summary` / `plot_transition_triggered`** — seaborn helpers.

## Notebook steps

1. **Load** — set `RESULTS` to your `aerotaxis_results.*` file (or a dataset folder).
2. **Per-state summary** — behaviour per gas state (rates + means).
3. **Bar plots** — per-state metrics split by condition.
4. **Transition-triggered averages** — the O2 on/off response dynamics for speed,
   bend frequency and reversal probability.
5. **Reversal reaction** — latency distribution to the pulse onset.
6. **Per-crop viewer** — ipywidgets dropdown; time series with the gas protocol shaded.
7. **Save** — tidy CSV summaries for R / sharing.

## Extending

- **Different gas paradigm:** nothing changes here — edit the `aerotaxis:` block in
  `config.yaml` and re-run the pipeline; `O2_State` follows automatically.
- **New metric:** add a column upstream (or compute in the notebook) and pass its
  name to `transition_triggered_average` / `per_state_summary`.
- **Quiescence / arousal:** the repo ships `quiescence_analysis` (pixel-difference +
  speed thresholds, `get_quiescence(...)`). It needs the raw crop images, so it is a
  separate step — a natural add-on for O₂-arousal studies once you want quiescence bouts.

**Required libraries:** pandas, numpy, seaborn, matplotlib, ipywidgets, pyarrow (for parquet).
