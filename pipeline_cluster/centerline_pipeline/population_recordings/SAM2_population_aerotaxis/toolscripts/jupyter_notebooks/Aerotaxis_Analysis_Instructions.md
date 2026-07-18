# Population Aerotaxis Analysis Guide

## Overview

This guide covers the temporal (non-spatial) analysis of the aerotaxis pipeline:
behavioural state changes locked to **global plate-level gas shifts**. There are
no gradients, no odor positions and no chemotaxis index — behaviour is described
purely as a function of gas state and time relative to each gas shift.

Two entry points, both built on the **same tidy table**:

- **`toolscripts/utils/aerotaxis_analysis.py`** — reusable functions (import in a
  notebook/script, or run as a CLI). This is where the analysis logic lives.
- **`jupyter_notebooks/Aerotaxis_population_grouped.ipynb`** (at the pipeline
  root) — a thin notebook that imports the module and shows the standard plots
  interactively.

## Input: the tidy results table

`create_results_dict_server.py` concatenates every per-crop
`temporal_features.csv` into `aerotaxis_results.{parquet,csv,pkl}`. The **full
column schema is documented once** in the protocol guide — repo-root
`README_AEROTAXIS_PIPELINE.md`, §5 *"Outputs & the tidy table"*. This guide only
recaps what the analysis functions key on:

- **Grouping keys** — `Condition`, `Recording`, `Crop_ID` (`GROUP_KEYS`).
- **Gas state** — `O2_State`, `Cycle_Index`, `Time_In_Phase_s`.
- **Behaviour** — `Forward_Velocity` (mm/s, signed), `Reversal_Active` / `Turn_Active`
  (0/1, so their means are time fractions), `Reversal_Onset`, `Bend_Frequency`,
  `Bend_Amplitude`.
- **QC / meta** — `Occluded` (dropped on load), `X_mm` / `Y_mm`, `fps`.

`Bend_*` may be NaN for crops whose kymogram was too poor for the Hilbert
transform. `Cycle_Index` / `Time_In_Phase_s` / `X_mm` / `Y_mm` / `Occluded` / `fps`
are absent for tables from older pipeline versions; every helper tolerates that.

> **A `Crop_ID` is a trajectory fragment, not a unique animal.** SWC has no
> re-identification, so one worm can become several crops: `n_crops` over-counts
> animals and crop-weighting is per-fragment, not per-animal. Report crop counts
> descriptively but base statistical claims on the **Recording-level** tests
> (`compare_conditions_per_state`). Full explanation in
> `README_AEROTAXIS_PIPELINE.md` §6 ("A crop is a track fragment…").

## Quick start (CLI)

```bash
# from the dataset folder, after create_results_dict_server.py
python /path/to/toolscripts/utils/aerotaxis_analysis.py \
    aerotaxis_results.parquet --outdir analysis --pulse_state 21pct_O2
```

Writes `crop_qc.csv`, `per_state_summary.csv`, `transition_triggered_*.csv`,
`per_cycle_summary.csv`, `reversal_reaction.csv`, and `condition_stats.csv` to
`analysis/` — the same set `finalize_aerotaxis_dataset.sh` produces. What each file
contains (crop-weighting, FDR, replication counts) is documented in
`README_AEROTAXIS_PIPELINE.md` §6.

**Frame rate** is read automatically from the `fps` column, so you don't pass
`--fps` for current data (the CLI prints `[fps] using N fps (from data)`); it is
only a fallback for legacy tables that lack the column, and warns when used.

## The analysis primitives (`aerotaxis_analysis.py`)

- **`load_results(path, drop_occluded=True, require_alive=True, ...)`** — load a
  combined results file, or scan a dataset folder for
  `*/output/temporal_features.csv`. By default drops occluded frames and applies
  the lenient aliveness gate (below).
- **`crop_qc(df, fps)` / `filter_alive(df, ...)`** — the **aliveness QC**. Keeps a
  crop if it was tracked `≥ min_track_seconds` (5 s) AND shows ANY sign of life:
  it *moved* (`total_path_mm ≥ min_path_mm` OR `net_displacement_mm ≥ min_displacement_mm`),
  *bent* (`mean_bend_amplitude ≥ min_bend_amplitude`), or *behaved* (`n_events ≥ min_events`).
  Drops only crops flat on all signals (dead/bubble/debris) — a deliberately
  lenient union that keeps slow dwelling worms as well as fast roamers. Inspect
  `crop_qc(df)` (one row per crop, all signals + `alive`) to pick thresholds.
  Non-destructive; `require_alive=False` disables it. (`filter_motile`/`crop_motility`
  remain as aliases.)
- **`per_state_summary(df, by=("Condition","O2_State"), crop_level=True)`** — mean
  `Forward_Velocity`, `reversal_fraction`, `turn_fraction`, `mean_bend_frequency_hz`,
  `reversal_onsets_per_min`, plus `<metric>_sem`, `n_crops`, `n_recordings`.
  Crop-weighted (each crop/fragment once) by default to avoid frame-level
  pseudoreplication; `crop_level=False` reproduces the old frame-pooled means.
  Observation time for the onset rate uses each crop's true fps.
- **`find_transitions(df)`** — one row per gas shift per crop
  (`from_state`, `to_state`, `Frame`, `Time_Seconds`).
- **`transition_triggered_average(df, feature, pre_s, post_s, fps, transition=None)`**
  — long tidy frame with a `rel_time_s` axis (t=0 at the shift); feed straight to
  `seaborn.lineplot` for mean ± 95% CI across crops. `feature` can be any continuous
  column (`Forward_Velocity`, `Bend_Frequency`, `Reversal_Active`, …); `transition=
  "7pct_O2->21pct_O2"` filters to one shift type (the O2-up pulse onset).
- **`per_cycle_summary(df, feature, state=None, by=("Condition",))`** —
  mean `feature` per successive `Cycle_Index`; pass `state="21pct_O2"` for the
  pulse response only. Plot vs `Cycle_Index` to see **population habituation**
  across repeated pulses. This is *not* within-animal adaptation: fragments span
  only a few cycles, so each `Cycle_Index` aggregates different overlapping
  fragment sets (see the crop-vs-animal note above).
- **`reversal_reaction(df, to_state, window_s, fps)`** — per crop/pulse, latency (s)
  from each transition into `to_state` to the first reversal onset within `window_s`
  (generalises `curvature/src/rev_reaction.py` to the config-driven protocol).
- **`compare_conditions_per_state(df, metric, states=None, unit="Recording")`** —
  nonparametric Condition comparison within each gas state, run at the Recording
  level so frames/crops aren't pseudo-replicated (Mann–Whitney for 2 Conditions,
  Kruskal–Wallis for >2). Returns raw `p_value` + `n_units`/`n_per_condition`; the
  CLI adds Benjamini–Hochberg `p_adj` across the whole metric×state family. Needs scipy.
- **`plot_per_state_summary` / `plot_transition_triggered`** — seaborn helpers.

**Tests:** `tests/` holds a pytest suite for the gas-state mapping and every
analysis primitive changed here (`pytest` from the pipeline root). Run it after
editing the analysis or the extractor.

## Notebook steps

1. **Load + QC** — set `RESULTS` to your `aerotaxis_results.*` file (or a dataset
   folder); `load_results` drops occluded frames and applies the aliveness gate.
   Inspect `crop_qc(load_results(RESULTS, require_alive=False))` to see the split.
2. **Per-state summary** — behaviour per gas state (rates + means).
3. **Bar plots** — per-state metrics split by condition.
4. **Transition-triggered averages** — the O2 on/off response dynamics for speed,
   bend frequency and reversal probability.
5. **Reversal reaction** — latency distribution to the pulse onset.
6. **Habituation** — `per_cycle_summary` vs `Cycle_Index` (does the *population*
   response fade across successive pulses? — not within-animal; see above).
7. **Statistics** — `compare_conditions_per_state` across genotypes/conditions.
8. **Per-crop viewer** — ipywidgets dropdown; time series with the gas protocol shaded.
9. **Save** — tidy CSV summaries for R / sharing.

## Extending

- **Different gas paradigm:** nothing changes here — edit the `aerotaxis:` block in
  `config.yaml` and re-run the pipeline; `O2_State` follows automatically.
- **New metric:** add a column upstream (or compute in the notebook) and pass its
  name to `transition_triggered_average` / `per_state_summary`.
- **Quiescence / arousal:** the repo ships `quiescence_analysis` (pixel-difference +
  speed thresholds, `get_quiescence(...)`). It needs the raw crop images, so it is a
  separate step — a natural add-on for O₂-arousal studies once you want quiescence bouts.

**Required libraries:** pandas, numpy, seaborn, matplotlib, ipywidgets, pyarrow (for parquet).
