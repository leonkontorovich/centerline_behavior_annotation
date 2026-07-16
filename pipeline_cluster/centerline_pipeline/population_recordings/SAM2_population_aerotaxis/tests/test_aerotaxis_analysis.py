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
          reversal=0.0, velocity=1.0, start_frame=0):
    """Build a minimal per-frame crop table."""
    frames = np.arange(start_frame, start_frame + n)
    return pd.DataFrame({
        "Condition": condition, "Recording": recording, "Crop_ID": crop_id,
        "Frame": frames, "Time_Seconds": frames / fps, "O2_State": state,
        "Forward_Velocity": velocity, "Reversal_Active": reversal,
        "Turn_Active": 0.0, "fps": float(fps),
    })


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


# ---------------------------------------------------------------- event count
def test_event_count_ignores_initial_active_state():
    # starts already active (1,1,0,1,1) -> exactly ONE observed 0->1 onset
    assert aa._event_count(pd.Series([1, 1, 0, 1, 1])) == 1
    # a clean single rising edge
    assert aa._event_count(pd.Series([0, 0, 1, 1, 0])) == 1
    # never active
    assert aa._event_count(pd.Series([0, 0, 0])) == 0


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
