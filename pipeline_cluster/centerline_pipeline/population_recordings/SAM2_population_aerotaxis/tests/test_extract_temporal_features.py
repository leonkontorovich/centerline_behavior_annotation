#!/usr/bin/env python3
"""
Unit tests for the aerotaxis temporal-feature extractor
(snakemake_files/snakefiles_aerotaxis/extract_temporal_features.py).

Focus:
  * build_o2_state -- the logic-dense gas-protocol -> per-frame-state mapping,
    at every boundary (pre / baseline / cycle phases / wraparound / n_cycles
    termination / t0 offset). This is the function most likely to silently
    mislabel frames, so it is exercised exhaustively.
  * _signed_velocity -- that an occluded (NaN-position) frame no longer poisons
    the velocity of its non-occluded neighbours.

Run:  pytest test_extract_temporal_features.py -q
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

# import the extractor module directly from the snakefiles dir
_HERE = Path(__file__).resolve().parent
_EXTRACT_DIR = _HERE.parent / "snakemake_files" / "snakefiles_aerotaxis"
sys.path.insert(0, str(_EXTRACT_DIR))
import extract_temporal_features as ex  # noqa: E402


# The default reference protocol: 240 s baseline @ 7% O2, then repeating
# 30 s 21% pulse / 60 s 7% return (period = 90 s).
BASELINE = 240.0
BASELINE_STATE = "7pct_O2"
CYCLE = [{"state": "21pct_O2", "duration_s": 30}, {"state": "7pct_O2", "duration_s": 60}]
PERIOD = 90.0


def _state(times, n_cycles=None):
    s, ci, tip = ex.build_o2_state(np.asarray(times, float), BASELINE,
                                   BASELINE_STATE, CYCLE, n_cycles=n_cycles)
    return s, ci, tip


# ---------------------------------------------------------------- pre / baseline
def test_pre_protocol():
    s, ci, tip = _state([-100.0, -0.001])
    assert list(s) == ["pre_protocol", "pre_protocol"]
    assert list(ci) == [-1, -1]
    assert list(tip) == [0.0, 0.0]


def test_baseline_block_and_time_in_phase():
    s, ci, tip = _state([0.0, 100.0, 239.999])
    assert list(s) == [BASELINE_STATE] * 3
    assert list(ci) == [-1, -1, -1]           # baseline is not a numbered cycle
    np.testing.assert_allclose(tip, [0.0, 100.0, 239.999])


# ---------------------------------------------------------------- cycle phases
def test_first_pulse_onset_exactly_at_baseline_end():
    # t == baseline_duration is the FIRST cycle frame, phase 0 (the pulse)
    s, ci, tip = _state([BASELINE])
    assert s[0] == "21pct_O2"
    assert ci[0] == 0
    assert tip[0] == 0.0


def test_pulse_then_return_within_first_cycle():
    s, ci, tip = _state([BASELINE + 29.999, BASELINE + 30.0, BASELINE + 89.999])
    assert list(s) == ["21pct_O2", "7pct_O2", "7pct_O2"]
    assert list(ci) == [0, 0, 0]
    # time-in-phase resets to 0 at the return onset (t = baseline+30)
    np.testing.assert_allclose(tip, [29.999, 0.0, 59.999], atol=1e-6)


def test_second_cycle_wraparound():
    # one full period later we are back in the pulse, cycle index advances
    s, ci, tip = _state([BASELINE + PERIOD, BASELINE + PERIOD + 30.0])
    assert list(s) == ["21pct_O2", "7pct_O2"]
    assert list(ci) == [1, 1]
    np.testing.assert_allclose(tip, [0.0, 0.0], atol=1e-6)


def test_phase_boundaries_use_right_side():
    # exactly on a phase edge belongs to the NEXT phase (edge = phase end)
    s, _, _ = _state([BASELINE + 30.0, BASELINE + 90.0])
    assert s[0] == "7pct_O2"    # end of pulse -> return
    assert s[1] == "21pct_O2"   # end of cycle -> next pulse


# ---------------------------------------------------------------- n_cycles end
def test_n_cycles_terminates_into_post_protocol():
    # with n_cycles=2, anything at/after the 3rd cycle is post_protocol
    t_after = BASELINE + 2 * PERIOD          # start of cycle index 2 -> past cap
    t_before = BASELINE + 2 * PERIOD - 0.001  # still inside cycle index 1
    s, ci, tip = _state([t_before, t_after], n_cycles=2)
    assert s[0] == "7pct_O2" and ci[0] == 1
    assert s[1] == "post_protocol" and ci[1] == -1 and tip[1] == 0.0


def test_n_cycles_none_repeats_to_end():
    # documented behaviour: null n_cycles keeps cycling (no post_protocol)
    s, ci, _ = _state([BASELINE + 50 * PERIOD], n_cycles=None)
    assert s[0] == "21pct_O2"
    assert ci[0] == 50


# ---------------------------------------------------------------- t0 offset
def test_t0_offset_shifts_everything():
    # protocol_time = abs_time - t0_offset; caller subtracts the offset, so we
    # emulate a 15 s camera-before-gas delay: abs_time 15 -> protocol_time 0.
    offset = 15.0
    abs_times = np.array([offset - 1, offset, offset + BASELINE])
    s, _, _ = ex.build_o2_state(abs_times - offset, BASELINE, BASELINE_STATE, CYCLE)
    assert list(s) == ["pre_protocol", BASELINE_STATE, "21pct_O2"]


# ---------------------------------------------------------------- guards
def test_zero_total_cycle_duration_raises():
    with pytest.raises(ValueError):
        ex.build_o2_state(np.array([300.0]), BASELINE, BASELINE_STATE,
                          [{"state": "x", "duration_s": 0}])


def test_empty_input_array():
    s, ci, tip = _state([])
    assert len(s) == len(ci) == len(tip) == 0


def test_non_finite_timestamp_raises():
    # a broken clock must fail loudly, not silently emit a garbage Cycle_Index
    # (np.floor(nan).astype(int) is a platform-dependent sentinel).
    with pytest.raises(ValueError, match="non-finite"):
        _state([0.0, np.nan, 100.0])
    with pytest.raises(ValueError, match="non-finite"):
        _state([BASELINE + 10.0, np.inf])


# ---------------------------------------------------------------- signed velocity
def test_occluded_frame_does_not_poison_neighbours():
    # position with a single NaN (occluded) frame in the middle
    x = np.array([0.0, 1.0, 2.0, np.nan, 4.0, 5.0])
    y = np.zeros_like(x)
    occ = np.array([0, 0, 0, 1, 0, 0])
    rev = np.zeros_like(x)
    vel = ex._signed_velocity(x, y, rev, fps=1.0, smooth_win=1, occluded=occ)
    assert np.isnan(vel[3])                       # occluded frame itself -> NaN
    assert np.isfinite(vel[2]) and np.isfinite(vel[4])  # neighbours survive
    np.testing.assert_allclose(vel[2], 1.0)       # constant 1 px/frame * 1 fps
    np.testing.assert_allclose(vel[4], 1.0)


def test_reversal_sign_is_negative():
    x = np.arange(5.0)
    y = np.zeros_like(x)
    rev = np.array([0, 0, 1, 1, 0])
    vel = ex._signed_velocity(x, y, rev, fps=1.0, smooth_win=1)
    assert (vel[rev == 1] <= 0).all()
    assert (vel[rev == 0] >= 0).all()


def test_single_frame_velocity_is_safe():
    vel = ex._signed_velocity(np.array([3.0]), np.array([3.0]),
                              np.array([0]), fps=1.0, smooth_win=1)
    assert len(vel) == 1 and np.isfinite(vel[0])


# ---------------------------------------------------------------- crop ledger
def test_ledger_reads_both_qc_arrays(tmp_path):
    # a single ledger read exposes both the occlusion mask and the clip flag
    meta = {"is_missing_frame": [False, True, False],
            "animal_clipped": [True, False, False]}
    (tmp_path / "worm_track_3_metadata.json").write_text(json.dumps(meta))
    ledger = ex._read_crop_ledger(tmp_path)
    assert ledger is not None
    np.testing.assert_array_equal(
        ex._ledger_bool_array(ledger, "is_missing_frame"), [False, True, False])
    np.testing.assert_array_equal(
        ex._ledger_bool_array(ledger, "animal_clipped"), [True, False, False])


def test_ledger_absent_or_keyless_returns_none(tmp_path):
    assert ex._read_crop_ledger(tmp_path) is None            # no *_metadata.json
    assert ex._ledger_bool_array(None, "animal_clipped") is None
    assert ex._ledger_bool_array({"is_missing_frame": [1]}, "animal_clipped") is None
