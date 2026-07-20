#!/usr/bin/env python3
"""
Unit tests for the aerotaxis population analysis
(toolscripts/utils/aerotaxis_analysis.py).

Covers the behaviour changed in this pass:
  * fps is read from the per-recording `fps` column, not assumed 10
  * crop_qc / reversal_reaction honour each crop's own fps
  * per_state_summary is crop-weighted (de-pseudoreplicated) by default
  * _event_count no longer credits a crop that opens mid-event with an onset
  * _bh_fdr matches a hand-computed Benjamini-Hochberg result
  * compare_conditions_per_state emits machine-readable n columns (no dict cell)
  * transition_triggered_average builds its time grid from the true fps

Run:  pytest test_aerotaxis_analysis.py -q
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_HERE = Path(__file__).resolve().parent
_UTILS = _HERE.parent / "toolscripts" / "utils"
sys.path.insert(0, str(_UTILS))
import aerotaxis_analysis as aa  # noqa: E402


def _crop(condition, recording, crop_id, n, fps, state="21pct_O2",
          reversal=0.0, velocity=1.0, start_frame=0, animal_clipped=None):
    """Build a minimal per-frame crop table.

    `animal_clipped` (scalar 0/1 or length-n array) adds the SWC-derived
    `Animal_Clipped` per-frame column; left None the column is absent (older
    data), so crop_qc's graceful-degradation path is exercised too.
    """
    frames = np.arange(start_frame, start_frame + n)
    d = pd.DataFrame({
        "Condition": condition, "Recording": recording, "Crop_ID": crop_id,
        "Frame": frames, "Time_Seconds": frames / fps, "O2_State": state,
        "Forward_Velocity": velocity, "Reversal_Active": reversal,
        "Turn_Active": 0.0, "fps": float(fps),
    })
    if animal_clipped is not None:
        d["Animal_Clipped"] = animal_clipped
    return d


# ---------------------------------------------------------------- fps resolution
def test_resolve_fps_reads_column():
    df = _crop("A", "R1", "C1", 10, fps=5.0)
    fps, src = aa._resolve_fps(df, verbose=False)
    assert fps == 5.0 and src == "data"


def test_resolve_fps_falls_back_without_column():
    df = _crop("A", "R1", "C1", 10, fps=5.0).drop(columns=["fps"])
    fps, src = aa._resolve_fps(df, fps_fallback=10.0, verbose=False)
    assert fps == 10.0 and src == "fallback"


def test_resolve_fps_flags_mixed_rates():
    df = pd.concat([_crop("A", "R1", "C1", 10, fps=5.0),
                    _crop("A", "R2", "C2", 10, fps=20.0)], ignore_index=True)
    fps, src = aa._resolve_fps(df, verbose=False)
    assert src == "data" and fps == pytest.approx(np.median([5.0, 20.0]))


# ---------------------------------------------------------------- per-crop fps
def test_crop_qc_uses_per_crop_fps_for_duration():
    # 20 frames @ 20 fps -> 1 s;  20 frames @ 5 fps -> 4 s
    df = pd.concat([_crop("A", "R1", "fast", 20, fps=20.0),
                    _crop("A", "R1", "slow", 20, fps=5.0)], ignore_index=True)
    qc = aa.crop_qc(df).set_index("Crop_ID")
    assert qc.loc["fast", "duration_s"] == pytest.approx(1.0)
    assert qc.loc["slow", "duration_s"] == pytest.approx(4.0)


def test_crop_qc_falls_back_when_no_fps_column():
    df = _crop("A", "R1", "C1", 20, fps=5.0).drop(columns=["fps"])
    qc = aa.crop_qc(df, fps=10.0).set_index("Crop_ID")
    assert qc.loc["C1", "duration_s"] == pytest.approx(2.0)  # 20/10


# ---------------------------------------------------------------- clipping QC
def test_crop_qc_reports_pct_frames_clipped():
    # 2 of 10 frames flagged clipped -> 20 %
    df = _crop("A", "R1", "C1", 10, fps=10.0,
               animal_clipped=[1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    qc = aa.crop_qc(df).set_index("Crop_ID")
    assert qc.loc["C1", "pct_frames_clipped"] == pytest.approx(20.0)


def test_crop_qc_pct_clipped_is_nan_without_column():
    # older data with no Animal_Clipped column -> column present but NaN
    df = _crop("A", "R1", "C1", 10, fps=10.0)
    qc = aa.crop_qc(df).set_index("Crop_ID")
    assert "pct_frames_clipped" in qc.columns
    assert np.isnan(qc.loc["C1", "pct_frames_clipped"])


def test_clipping_never_gates_aliveness():
    # a fully-clipped but clearly locomoting worm must survive filter_alive:
    # clipping is a technical flag, not a life signal.
    df = _crop("A", "R1", "C1", 100, fps=10.0, velocity=1.0, animal_clipped=1)
    kept = aa.filter_alive(df, verbose=False)
    assert set(kept["Crop_ID"]) == {"C1"}


# ---------------------------------------------------------------- event count
def test_event_count_ignores_initial_active_state():
    # starts already active (1,1,0,1,1) -> exactly ONE observed 0->1 onset
    assert aa._event_count(pd.Series([1, 1, 0, 1, 1])) == 1
    # a clean single rising edge
    assert aa._event_count(pd.Series([0, 0, 1, 1, 0])) == 1
    # never active
    assert aa._event_count(pd.Series([0, 0, 0])) == 0


# ---------------------------------------------------------------- aliveness gate
def _qc_crop(crop_id, n=100, fps=10.0, velocity=0.0, x_drift=0.0,
             bend_amp=0.0, n_onsets=0):
    """A crop table with the columns the aliveness gate inspects."""
    frames = np.arange(n)
    onset = np.zeros(n, dtype=int)
    onset[1:1 + n_onsets] = 1  # rising edges (n_onsets distinct events)
    return pd.DataFrame({
        "Condition": "A", "Recording": "R1", "Crop_ID": crop_id,
        "Frame": frames, "Time_Seconds": frames / fps, "O2_State": "7pct_O2",
        "Forward_Velocity": velocity, "Reversal_Active": 0.0, "Turn_Active": 0.0,
        "Reversal_Onset": onset, "Bend_Amplitude": bend_amp,
        "X_mm": frames * x_drift, "Y_mm": 0.0, "fps": float(fps),
    })


def test_strict_qc_drops_drifter_keeps_bender():
    # drifter: translocates (moved) but never bends or behaves -> a bubble.
    # bender: barely translocates but bends its body -> a real (dwelling) worm.
    drifter = _qc_crop("drift", velocity=0.5, x_drift=0.05, bend_amp=0.0, n_onsets=0)
    bender = _qc_crop("bend", velocity=0.0, x_drift=0.0, bend_amp=0.5, n_onsets=0)
    df = pd.concat([drifter, bender], ignore_index=True)

    lenient = aa.filter_alive(df, verbose=False)
    strict = aa.filter_alive(df, strict=True, verbose=False)

    kept_lenient = set(lenient.Crop_ID.unique())
    kept_strict = set(strict.Crop_ID.unique())
    assert kept_lenient == {"drift", "bend"}   # default union keeps both
    assert kept_strict == {"bend"}             # strict drops the pure drifter


def test_strict_qc_keeps_behaver_without_bends():
    # a worm that reverses/turns but has no Hilbert bend signal is still kept by
    # strict gating via the `behaved` branch.
    behaver = _qc_crop("beh", velocity=0.0, x_drift=0.0, bend_amp=0.0, n_onsets=2)
    strict = aa.filter_alive(behaver, strict=True, verbose=False)
    assert set(strict.Crop_ID.unique()) == {"beh"}


# ---------------------------------------------------------------- pseudoreplication
def test_per_state_summary_is_crop_weighted_by_default():
    # one long all-reversing crop + one short non-reversing crop, same group.
    # frame-pooled reversal_fraction = 100/110; crop-weighted = (1+0)/2 = 0.5
    df = pd.concat([
        _crop("A", "R1", "long", 100, fps=10.0, reversal=1.0),
        _crop("A", "R1", "short", 10, fps=10.0, reversal=0.0),
    ], ignore_index=True)
    crop_w = aa.per_state_summary(df)  # default crop_level=True
    frame_w = aa.per_state_summary(df, crop_level=False)
    row = crop_w.iloc[0]
    assert row["reversal_fraction"] == pytest.approx(0.5)
    assert row["n_crops"] == 2
    assert row["n_recordings"] == 1
    assert frame_w.iloc[0]["reversal_fraction"] == pytest.approx(100 / 110)


def test_per_state_summary_onset_rate_uses_true_fps():
    # 1 onset in a 60 s crop (600 frames @ 10 fps) -> 1.0 onset/min
    df = _crop("A", "R1", "C1", 600, fps=10.0)
    df["Reversal_Onset"] = 0
    df.loc[5, "Reversal_Onset"] = 1
    out = aa.per_state_summary(df)
    assert out.iloc[0]["reversal_onsets_per_min"] == pytest.approx(1.0)


# ---------------------------------------------------------------- BH-FDR
def test_bh_fdr_matches_scipy():
    # validate our dependency-free BH against scipy's authoritative implementation
    from scipy.stats import false_discovery_control
    p = np.array([0.001, 0.008, 0.039, 0.041, 0.042])
    np.testing.assert_allclose(aa._bh_fdr(p),
                               false_discovery_control(p, method="bh"), atol=1e-9)


def test_bh_fdr_unsorted_input():
    from scipy.stats import false_discovery_control
    p = np.array([0.042, 0.001, 0.041, 0.008, 0.039])  # deliberately unsorted
    np.testing.assert_allclose(aa._bh_fdr(p),
                               false_discovery_control(p, method="bh"), atol=1e-9)


def test_bh_fdr_passes_nan_through():
    adj = aa._bh_fdr(np.array([0.01, np.nan, 0.02]))
    assert np.isnan(adj[1])
    assert np.isfinite(adj[0]) and np.isfinite(adj[2])


# ---------------------------------------------------------------- reversal reaction
def test_reversal_reaction_latency_uses_per_crop_fps():
    fps = 5.0
    df = _crop("A", "R1", "C1", 40, fps=fps, state="7pct_O2")
    # transition into the pulse at frame 20
    df.loc[df.Frame >= 20, "O2_State"] = "21pct_O2"
    df["Reversal_Onset"] = 0
    df.loc[df.Frame == 25, "Reversal_Onset"] = 1   # 5 frames after onset -> 1.0 s @ 5 fps
    rr = aa.reversal_reaction(df, to_state="21pct_O2")
    assert len(rr) == 1
    assert rr.iloc[0]["reacted"] == 1
    assert rr.iloc[0]["latency_s"] == pytest.approx(1.0)


# ---------------------------------------------------------------- condition stats
def test_compare_conditions_emits_machine_readable_counts():
    frames = []
    for cond, base in [("A", 0.2), ("B", 0.8)]:
        for r in range(3):  # 3 recordings/condition so the test can actually run
            v = base + 0.01 * r
            frames.append(_crop(cond, f"{cond}{r}", f"{cond}{r}c", 50,
                                fps=10.0, velocity=v))
    df = pd.concat(frames, ignore_index=True)
    out = aa.compare_conditions_per_state(df, metric="Forward_Velocity")
    assert "n_units" in out and "n_per_condition" in out
    assert "n" not in out.columns                       # the old dict column is gone
    row = out.iloc[0]
    assert row["n_units"] == 6                           # 3 + 3 recordings
    assert isinstance(row["n_per_condition"], str) and "A=3" in row["n_per_condition"]


# ---------------------------------------------------------------- TTA grid
def test_transition_triggered_grid_uses_true_fps():
    fps = 5.0
    df = _crop("A", "R1", "C1", 40, fps=fps, state="7pct_O2")
    df.loc[df.Frame >= 20, "O2_State"] = "21pct_O2"
    tta = aa.transition_triggered_average(df, feature="Forward_Velocity",
                                          pre_s=1.0, post_s=1.0)
    rel = np.sort(tta["rel_time_s"].unique())
    # 5 fps -> 0.2 s spacing, from -1 s to +1 s inclusive = 11 samples
    assert len(rel) == 11
    np.testing.assert_allclose(np.diff(rel), 0.2, atol=1e-9)
