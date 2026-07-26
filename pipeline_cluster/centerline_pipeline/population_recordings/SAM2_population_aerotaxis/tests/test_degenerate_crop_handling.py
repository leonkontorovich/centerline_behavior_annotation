#!/usr/bin/env python3
"""
Regression tests for the failure that cost a full 4,576-crop pipeline run.

The chain was: a pixel-valued `min_worm_lenght` threshold blanked ~99% of frames
-> the dynamic column crop collapsed the curvature table to one column and wrote
it as a SUCCESS -> annotate_reversals sliced segments [9,39) out of it and died
with a pandas KeyError -> 4,190 crops produced no temporal_features.csv, while
every log printed "Pipeline complete".

Each test below pins one link so the chain cannot silently re-form:

  * a degenerate curvature table is REFUSED at the point it is produced,
    instead of being written as an all-NaN file that looks fine;
  * a narrow curvature table makes annotate_reversals SKIP the crop with
    correctly-shaped outputs, instead of taking the DAG branch down;
  * those skip outputs are readable by the downstream extractor, so the skip
    does not merely relocate the crash;
  * recording names with stray whitespace parse to the same genotype/plate as
    their clean siblings, instead of silently forming their own condition.

Run:  pytest test_degenerate_crop_handling.py -q
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[4]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_HERE.parent / "toolscripts" / "utils"))
sys.path.insert(0, str(_HERE.parent / "snakemake_files" / "snakefiles_aerotaxis"))

from centerline_behavior_annotation.centerline.dev import (  # noqa: E402
    centerline_equi_distance_2d_smoothing as cesm,
)
from centerline_behavior_annotation.curvature.src import (  # noqa: E402
    annotate_reversals_snakemake as arev,
)
import create_results_dict_server as crd  # noqa: E402

INITIAL_SEGMENT, FINAL_SEGMENT = 9, 39


# ----------------------------------------------------------------------
# annotate_reversals: skip, don't crash
# ----------------------------------------------------------------------
def _run_annotate(tmp_path, curvature: pd.DataFrame):
    """Run the real CLI entrypoint against a curvature table; return outputs."""
    spline = tmp_path / "skeleton_spline_K_new_smoothed.csv"
    curvature.to_csv(spline, index=False, header=False)
    beh = tmp_path / "reversal_annotation.csv"
    pcs = tmp_path / "principal_components.csv"
    arev.main([
        "-i", str(spline),
        # never reached on the skip path, so a nonexistent model is fine here
        "-pca", str(tmp_path / "no_such_model.pkl"),
        "-i_s", str(INITIAL_SEGMENT), "-f_s", str(FINAL_SEGMENT),
        "-win", "10", "-o_bh", str(beh), "-o_pc", str(pcs),
    ])
    return beh, pcs


def test_collapsed_curvature_skips_instead_of_raising(tmp_path):
    """The exact shape that produced 4,190 KeyErrors: 1 column, 30 requested."""
    n_frames = 120
    beh, pcs = _run_annotate(tmp_path, pd.DataFrame({0: np.full(n_frames, np.nan)}))
    assert beh.exists() and pcs.exists(), "skip must still produce both outputs"


def test_skip_outputs_have_one_row_per_frame(tmp_path):
    """Frame alignment is positional downstream, so length must be preserved."""
    n_frames = 137
    beh, _ = _run_annotate(tmp_path, pd.DataFrame({0: np.full(n_frames, np.nan)}))
    assert len(pd.read_csv(beh, index_col=0)) == n_frames


def test_skip_output_is_readable_by_the_extractor(tmp_path):
    """
    Guards the specific trap that an index-only CSV would spring:
    extract_temporal_features.load_reversal() does df.iloc[:, 0], which raises
    on a frame with no data columns. A "graceful" skip that relocates the crash
    is not graceful.
    """
    import extract_temporal_features as ex

    n_frames = 64
    beh, _ = _run_annotate(tmp_path, pd.DataFrame({0: np.full(n_frames, np.nan)}))
    arr = ex.load_reversal(beh)
    assert len(arr) == n_frames
    assert np.isnan(arr).all(), "unknown must stay NaN, not become 0 (no reversal)"


def test_skip_marks_reversals_unknown_not_absent(tmp_path):
    """
    NaN and 0 mean different things: 0 asserts the worm did not reverse, NaN
    admits we could not tell. Only NaN is honest for a crop with no centerline.
    """
    beh, _ = _run_annotate(tmp_path, pd.DataFrame({0: np.full(40, np.nan)}))
    assert pd.read_csv(beh, index_col=0).iloc[:, 0].isna().all()


def test_wide_enough_curvature_is_not_skipped(tmp_path):
    """
    The guard must be narrow. A table with enough columns has to proceed into
    the real PCA path -- here it fails on the deliberately missing model file,
    which proves it was NOT diverted into the skip branch.
    """
    good = pd.DataFrame(np.random.default_rng(0).normal(size=(50, FINAL_SEGMENT + 1)))
    with pytest.raises(Exception) as excinfo:
        _run_annotate(tmp_path, good)
    assert "no_such_model" in str(excinfo.value) or "No such file" in str(excinfo.value)


# ----------------------------------------------------------------------
# centerline: refuse to emit a degenerate table
# ----------------------------------------------------------------------
def test_min_usable_columns_is_at_least_three():
    """Curvature needs 3 points to take derivatives; fewer is never valid."""
    assert cesm.MIN_USABLE_COLUMNS >= 3


def _skeleton_csvs(tmp_path, xs, ys):
    x_csv, y_csv = tmp_path / "x.csv", tmp_path / "y.csv"
    pd.DataFrame(xs).to_csv(x_csv, index=False, header=False)
    pd.DataFrame(ys).to_csv(y_csv, index=False, header=False)
    return x_csv, y_csv


def test_all_nan_skeleton_raises_instead_of_writing_empty_output(tmp_path):
    """
    A crop whose skeletons were all blanked upstream must fail HERE, naming the
    cause, rather than writing an all-NaN curvature file that passes as success.
    """
    n_frames, n_pts = 30, 20
    nan_block = np.full((n_frames, n_pts), np.nan)
    x_csv, y_csv = _skeleton_csvs(tmp_path, nan_block, nan_block)
    out = {k: str(tmp_path / f"{k}.csv") for k in ("x", "y", "k", "ks")}

    with pytest.raises(Exception) as excinfo:
        cesm.main([
            "--skeleton_x", str(x_csv), "--skeleton_y", str(y_csv),
            "--relative_spacing", "2.0", "--num_sampled_points", "10000",
            "--smoothing", "0", "--time_sigma", "2.0", "--spatial_sigma", "1.0",
            "--max_columns", "0",
            "--output_x", out["x"], "--output_y", out["y"],
            "--output_curvature", out["k"], "--output_smoothed_curvature", out["ks"],
        ])
    msg = str(excinfo.value)
    assert "min_worm_length" in msg or "Degenerate skeleton" in msg, (
        f"the error must point at the real cause, got: {msg}")


# ----------------------------------------------------------------------
# recording-name parsing: whitespace must not fork a condition group
# ----------------------------------------------------------------------
@pytest.mark.parametrize("name,genotype,plate", [
    ("2026-06-17_11-51-38_N2_ B", "N2", "B"),   # the real folder on disk
    ("2026-06-17_11-51-38_N2_B", "N2", "B"),    # its clean sibling
    ("2026-06-18_12-17-00_npr_ B", "npr", "B"),
    ("2026-06-17_11-49-35_N2_A1", "N2", "A1"),
    ("2026-06-20_13-00-14_nprrde_A", "nprrde", "A"),
])
def test_recording_names_parse_despite_whitespace(name, genotype, plate):
    got_genotype, got_plate = crd.parse_recording_name(
        name, __import__("re").compile(crd.DEFAULT_NAME_RE))
    assert (got_genotype, got_plate) == (genotype, plate)


def test_spaced_and_clean_names_land_in_the_same_group():
    """
    The actual bug: 'N2_ B' became its own Condition, split from 'N2'. Equality
    of the parsed genotype is the property that matters, not the regex details.
    """
    import re
    pat = re.compile(crd.DEFAULT_NAME_RE)
    spaced, _ = crd.parse_recording_name("2026-06-17_11-51-38_N2_ B", pat)
    clean, _ = crd.parse_recording_name("2026-06-16_13-18-15_N2_A", pat)
    assert spaced == clean == "N2"
