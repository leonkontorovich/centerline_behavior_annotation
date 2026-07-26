# Making the aerotaxis pipeline fit whatever the cropper outputs

**Date:** 2026-07-26
**Status:** implemented (calibration run pending — see Open items)

## Problem

A 35-recording, 4,576-crop run of the aerotaxis pipeline on
`rde4_behavior/Croppings` produced usable output for 386 crops (8.4 %). Every
log reported `✅ Pipeline complete!`.

Failure chain, from the evidence:

1. `config.yaml` carried `min_worm_lenght: 83`, a **pixel** threshold tuned on a
   rig where worms imaged at ~1.0 mm. In this dataset worms image at **48–71 px**
   (DLC head→neck→vulva→tail polyline, medians across recordings).
2. `create_centerline` blanks any frame whose skeleton is shorter than that, so
   **0.0–0.2 % of frames** kept a skeleton. Surviving frames clustered at
   83–90 px — the signature of a threshold sitting above the distribution's bulk.
3. `process_skeleton_curvature`'s dynamic column crop saw near-zero occupancy,
   cut at the first column, and wrote a 1-column all-NaN curvature table **as a
   success**.
4. `annotate_reversals` sliced segments `[9, 39)` from that table and raised
   `KeyError: "None of [Index([9.0 ... 38.0])] are in the [columns]"` —
   **4,190 times**, the only failing rule in the entire dataset.
5. `RUNME_cluster.sh` printed its success banner unconditionally, so nothing
   surfaced the failure.

386 + 4,190 = 4,576 exactly: every crop either finished or died at that rule.

The root cause is not the threshold value. It is that a **magnification-specific
constant lived in a config that travels between rigs**, with nothing measuring
whether it fit the data. The pipeline already auto-sources `fps`,
`factor_px_to_mm`, and `min/max_worm_area` from SWC's `parameters.yaml`;
`min_worm_lenght` was simply never migrated.

## Design

### 1. Express the threshold as biology, convert per recording

`config.yaml` gains `min_worm_length_mm: 0.4`, replacing `min_worm_lenght: 83`.
A new `swc_min_worm_length(dataset)` in the Snakefile converts it to pixels via
`swc_factor_px_to_mm()`, following the existing `swc_*` pattern.

Worm length in mm is biology and is the same number on every rig; worm length in
pixels depends entirely on magnification. The old key is still honoured (with a
warning) when `min_worm_length_mm` is absent, so deployed configs keep working.

The value is a **junk floor** — it rejects debris and broken mask fragments and
sits far below a real adult (~0.8–1.1 mm). Selecting real worms remains the
analysis-time aliveness gate's job. On this dataset it resolves to 32.8 px.

### 2. Make silent fallbacks visible

Every `swc_*` helper reports its resolved value and provenance once per
recording:

```
[swc] <rec>: fps = 10  (source: parameters.yaml)
[swc] <rec>: factor_px_to_mm = 0.01221  (source: config.yaml fallback)  <-- FALLBACK, verify this fits your cropper output
```

This matters beyond tidiness: this dataset's `parameters.yaml` has neither
`pixel_size_mm` nor `frame_height_px`, so the "auto-sourced" px→mm silently used
the config fallback. It happened to be correct. Nothing verified that, and the
same silence is what let the length constant through.

### 3. Fail at the cause, not three rules later

- `process_skeleton_curvature` raises when the dynamic crop leaves fewer than
  `MIN_USABLE_COLUMNS` (3) columns, with an error naming both plausible causes
  (threshold too high vs genuine junk crop) — instead of writing an all-NaN file
  that passes as success.
- `annotate_reversals` **skips** a crop whose curvature table is too narrow,
  writing correctly-shaped NaN outputs so the crop's DAG branch survives. Junk
  crops are expected in a population recording and must not be pipeline errors.
  The skip emits full-length NaN columns specifically because
  `load_reversal()` does `df.iloc[:, 0]` — an index-only CSV would just relocate
  the crash.
- The Snakefile validates at DAG-build time that
  `final_segment ≤ 100 / relative_spacing`, turning a whole-dataset runtime
  failure into a startup error.

NaN rather than 0 in the skip outputs is deliberate: 0 asserts the worm did not
reverse, NaN admits we could not tell.

### 4. Report the true exit status

`RUNME_cluster.sh` captures Snakemake's exit code, prints `❌ Pipeline FAILED`
with the triage command on non-zero, and propagates it. `workflow_runner.sh`
runs under `set -e`, so its `bash RUNME_cluster.sh` call became
`|| EXIT_CODE=$?` — otherwise the now-correct non-zero exit would abort the
runner before its own failure report.

### 5. Measure the worms

`toolscripts/utils/calibrate_min_worm_length.py` recommends
`min_worm_length_mm` from data, with no GPU and no re-segmentation:

1. Measure the DLC head→tail polyline span per crop (h5 files survive for all
   4,576 crops; the corrected masks are `temp()` and were deleted).
2. Estimate `k = skeleton_length / DLC_span` **empirically** from frames where
   both exist, rather than assuming the chord-vs-arc correction.
3. Predict true length as `k × span` for all crops, and report what each
   candidate threshold would discard.

When no crop has both measurements, `k` cannot be estimated; the script says so
and falls back to an assumed 1.25 rather than presenting a fabricated number.

Wired into the protocol as **step 4a**, recommended on any new rig, objective,
magnification, or worm stage.

### 6. Whitespace in recording names

Four folders are named `..._N2_ B` (with a space). The plate group is
`[A-Za-z0-9]+`, so `_ B` fails to match, the name falls back wholesale to
`Genotype = "N2_ B"` with an empty `Plate`, and since `Condition` defaults to
`Genotype`, that recording silently becomes its own condition group — split from
the N2 it belongs to. Nothing errors; the statistics are just quietly wrong.
`parse_recording_name` now strips whitespace before matching.

## Explicitly out of scope

**`min/max_worm_area`.** These auto-source from SWC's
`region_extraction.min/max_region_size` (150/550 px²), which are thresholds on
connected components in the **full-plate raw image** under SWC's intensity
binarisation. The pipeline applies them to **SAM2 masks inside the crop** —
different segmenters, different edge behaviour, and nothing checks they agree.
`Turn_Active` fires on 52 % of frames, which is implausible.

Two candidate causes needing opposite fixes:

- **(a)** SAM2 masks exceed 550 px², forcing `roundness = 0` on valid frames
  (`annotate_turns_...:62` zeroes roundness, and that zero then feeds the
  rolling mean, corrupting neighbours).
- **(b)** For a 70 × 8 px worm, `roundness = circularity + 0.913 − CAR` ≈ 0.60,
  just over `min_round_threshold: 0.55` — ordinary crawling reads as a turn.

The masks were deleted, so this cannot be settled now. The calibration re-run
regenerates them; `turn_annotation_by_roundness.csv` already stores `mask_area`
and `roundness_mask_convex_hull` per frame, so the distributions will separate
(a) from (b). Deferred deliberately rather than guessed at.

## Cropper (SWC) alignment audit

Checked against the current SWC fork (`SimpleWormCropper`, HEAD `5af264a`), which
has moved well ahead of the build that produced this dataset. Every interface
the pipeline depends on still holds:

| Contract | Status |
|---|---|
| `<rec>_track_N.{tif,txt}` naming, per-track subfolder | unchanged (`cropping_manager.py:652`) |
| `track.txt` columns `frame,time,X,Y,time_imputed_seconds` | unchanged (`SWC_track.export_track_centroid`) |
| Ledger keys `frame_indices`, `is_missing_frame`, `animal_clipped` | all present (`SWC_crop.py:338-346`) |
| `region_extraction.min/max_region_size` | unchanged (default 150) |
| `recording.pixel_size_mm`, `frame_height_px`, `frame_width_px` | now persisted by `persist_derived_calibration()` — the pipeline already prefers them |

One genuine gap found and closed: SWC now also writes
`recording.fps_measured_from_metadata`, the fps measured from the recording's own
frame timestamps. SWC deliberately does not override the configured `fps` with
it, and warns only at **crop** time — in a log an analyst may never open. Since
every gas-locked feature depends on fps, `swc_fps()` now re-raises that
disagreement (same 5 % tolerance) at analysis time, and likewise does not
override.

No SWC change affects output *structure*, so no pipeline restructuring was
needed. The only behavioural consequence is positive: re-cropping with a current
build supplies `pixel_size_mm` directly, removing this dataset's silent px→mm
fallback.

## Verification

- 13 new regression tests in `tests/test_degenerate_crop_handling.py`, one per
  link in the failure chain; 49 tests pass overall.
- Snakefile header executed against a stub config reproducing this dataset's
  `parameters.yaml`: resolves `min_worm_length_px = 32.8` (was 83), flags the
  px→mm fallback, and rejects a `final_segment`/`relative_spacing` mismatch.
- `bash -n` on both shell scripts and on the *generated* `workflow_runner.sh`.

## Calibration result

Five recordings, 12 crops each:

| Recording | k | median worm | recommended | lost at old 83 px (1.01 mm) |
|---|---|---|---|---|
| `2026-06-16_12-44-36_rde_B` | 1.76 measured | 1.24 mm | 0.46 | 8 % |
| `2026-06-16_15-01-05_mut_A` | 0.99 measured | 0.76 mm | 0.32 | **100 %** |
| `2026-06-18_12-36-04_npr_C` | 1.25 assumed | 0.80 mm | 0.35 | 92 % |
| `2026-06-20_11-00-53_N2_A` | 1.34 measured | 0.99 mm | 0.36 | 50 % |
| `2026-06-26_12-58-07_mut_A` | 1.25 assumed | 0.78 mm | 0.34 | **100 %** |

This is the diagnosis confirmed quantitatively and independently: the old
threshold sat at or above the entire worm-length distribution in most
recordings.

`min_worm_length_mm` set to **0.30** — at or below every per-recording
recommendation. `k` is measured only from frames that survived the old filter,
i.e. the longest ones, so every recommendation is biased upward; the extreme
k = 1.76 comes from the recording where least survived. Taking the minimum and
rounding down absorbs that bias. Over-culling destroys datasets; stray debris is
removed by the aliveness gate for free. The bias is now documented in the
script's CAVEATS, with the instruction to re-run for an unbiased `k` after a
corrected pass.

## Open items

1. **Re-run the dataset** with the corrected threshold, then re-run the
   calibration to confirm `k` without the survivorship bias.
3. **Resolve the `worm_area` question** from the regenerated masks.
4. **`2026-06-26_12-50-40_rde_A_new/`** is a stray SWC batch root containing 18
   other recordings' unrenamed crops; that recording has never been processed.
   Needs untangling before the re-run.
5. **Re-copy the pipeline into the dataset** (step 3a) — the deployed
   `extract_temporal_features.py` predates the Jul 18/20 commits and omits
   `Cycle_Index`, `Time_In_Phase_s`, `X_mm`, `Y_mm`, `Animal_Clipped`, `fps`.
6. **Package code resolves to the shared install**
   (`zimmer/autoscope/code/centerline_behavior_annotation`), not this clone.
   The `centerline/` and `curvature/` fixes here take effect only once that copy
   is updated or the clone is `pip install -e`'d into the env.
