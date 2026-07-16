#!/usr/bin/env python3
"""
Extract temporal behavioural features for a single crop, aligned to a global
plate-level gas-shift protocol (aerotaxis / oxygen-sensing assays).

This REPLACES the spatial chemotaxis analysis. There are no gradients, no
radial distances and no chemotaxis index -- behaviour is described purely as
temporal state locked to global gas shifts (baseline O2, then repeating
pulse/return cycles).

Reads only artifacts already produced by the upstream (untouched) pipeline:
    track.txt                        (SWC tracker log)  -> ABSOLUTE clock + arena position
    <crop>_metadata.json             (SWC crop ledger, optional)   -> Occluded (per-frame mask)
    reversal_annotation.csv          (annotate_reversals)          -> Reversal_Active/Onset, velocity sign
    turn_annotation_by_roundness.csv (calc_turns_by_roundness)     -> Turn_Active
    hilbert_inst_freq.csv            (hilbert_transform_on_kymogram)-> Bend_Frequency (optional)
    hilbert_inst_amplitude.csv       (hilbert_transform_on_kymogram)-> Bend_Amplitude (optional)
    skeleton_spline_X/Y_coords_new.csv (process_skeleton_curvature)-> velocity FALLBACK only

The signed-speed formula matches centerline_behavior_annotation.behavior_analysis
.src.calculate_speed (np.gradient); that module is not imported because it runs a
hardcoded file read at import time.

Clock / alignment (important):
    Each crop is only a *segment* of the whole recording and starts at a
    different absolute time, but the gas protocol is global to the plate. The
    SWC track.txt logs, per frame, the absolute recording frame + time
    (`time_imputed_seconds`) and the worm's absolute arena position (X, Y in
    px). We therefore use track.txt as the authoritative per-frame clock:
      * Time_Seconds / O2_State come from the ABSOLUTE recording time
      * Forward_Velocity is computed from the arena X, Y trajectory (px -> mm)
    The behaviour arrays (reversal/turn) are aligned to that clock from the
    first frame. Current SWC (>= the crop off-by-one fix) writes the crop tif
    and track.txt at the SAME length, so alignment is 1:1; we still trim to the
    common length as a safety net for older data or partial writes.

    If track.txt is missing/unparseable, we fall back to a local clock
    (Frame/fps) and crop-centroid speed, and warn -- so the script still runs.

Occlusion: gap-tolerant SWC tracking emits a blank crop frame (and a NaN arena
position) whenever the animal is lost/occluded, flagging it per frame in the
crop's `<crop>_metadata.json` ("is_missing_frame"). We surface that as an
`Occluded` column (1 = occluded) so downstream population stats can drop those
frames -- their reversal/turn/bend values are derived from a blank frame and
are not real behaviour. If the metadata file is absent (older data), Occluded
is 0 everywhere and the output is identical to before.

Output: a tidy, flat per-frame CSV with columns
    [Crop_ID, Frame, Time_Seconds, O2_State, Cycle_Index, Time_In_Phase_s,
     Forward_Velocity, Reversal_Active, Turn_Active,
     Reversal_Onset, Bend_Frequency, Bend_Amplitude, Occluded, X_mm, Y_mm, fps]
The trailing `fps` column records the TRUE per-recording frame rate (read from
the SWC parameters.yaml by the Snakefile) so downstream analysis converts frames
to seconds with the real rate instead of silently assuming 10 fps. It is a
constant per crop; the combined table carries it through unchanged.
where Frame / Time_Seconds are ABSOLUTE (recording-wide) when track.txt is
available, so crops share one clock for gas-locked population analysis.
`Cycle_Index` (0-based repeat number, -1 for baseline/pre/post) and
`Time_In_Phase_s` (seconds since the current gas phase began) make
habituation/adaptation across successive pulses directly analysable. The
Frame..O2_State columns plus the four behaviour columns are the originally-
specified schema; the rest are enrichments from existing pipeline tools
(reversal onsets, Hilbert body bends, and the SWC per-frame occlusion mask).
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================================
# Protocol -> per-frame gas state
# ======================================================================
def build_o2_state(protocol_time_s, baseline_duration_s, baseline_state, cycle, n_cycles=None):
    """
    Map an array of PROTOCOL-relative timestamps (seconds; 0 = protocol start)
    to gas states, cycle indices and time-within-phase.

    Protocol = one baseline block, then `cycle` (an ordered list of
    {state, duration_s} phases) repeated. Fully vectorised and generic: any
    oxygen-sensing paradigm is expressed by editing baseline_* and cycle in
    config.yaml -- no code change needed here.

    Returns three aligned arrays:
      * states           : gas-state label per frame ("pre_protocol" for t < 0,
                           baseline_state during the baseline block, the cycle
                           phase labels afterwards, "post_protocol" once n_cycles
                           is exceeded).
      * cycle_index      : 0-based index of the repeat the frame falls in, or -1
                           for baseline / pre_protocol / post_protocol. This is
                           what lets downstream code test habituation/adaptation
                           of the response ACROSS successive pulses.
      * time_in_phase_s  : seconds since the current phase block began (0 at each
                           phase onset), for phase-locked averaging.
    """
    t = np.asarray(protocol_time_s, dtype=float)
    states = np.empty(t.shape, dtype=object)
    cycle_index = np.full(t.shape, -1, dtype=int)
    time_in_phase = np.zeros(t.shape, dtype=float)

    cycle_durations = np.array([float(p["duration_s"]) for p in cycle], dtype=float)
    cycle_states = [p["state"] for p in cycle]
    cycle_period = cycle_durations.sum()
    if cycle_period <= 0:
        raise ValueError("aerotaxis.cycle total duration must be > 0")
    phase_starts = np.concatenate(([0.0], np.cumsum(cycle_durations)[:-1]))  # start of each phase within a cycle
    phase_edges = np.cumsum(cycle_durations)                                 # end boundaries within one cycle

    pre = t < 0
    in_baseline = (~pre) & (t < baseline_duration_s)
    in_cycles = (~pre) & (~in_baseline)

    states[pre] = "pre_protocol"
    states[in_baseline] = baseline_state
    time_in_phase[in_baseline] = t[in_baseline]  # time since baseline onset (t=0)

    t_cyc = t[in_cycles] - baseline_duration_s
    cyc_index = np.floor(t_cyc / cycle_period).astype(int)
    t_in_cycle = t_cyc - cyc_index * cycle_period
    phase_idx = np.clip(np.searchsorted(phase_edges, t_in_cycle, side="right"),
                        0, len(cycle_states) - 1)
    cyc_states = np.array([cycle_states[i] for i in phase_idx], dtype=object)
    cyc_time_in_phase = t_in_cycle - phase_starts[phase_idx]
    if n_cycles is not None:
        past = cyc_index >= n_cycles
        cyc_states[past] = "post_protocol"
        cyc_index = np.where(past, -1, cyc_index)
        cyc_time_in_phase = np.where(past, 0.0, cyc_time_in_phase)
    states[in_cycles] = cyc_states
    cycle_index[in_cycles] = cyc_index
    time_in_phase[in_cycles] = cyc_time_in_phase
    return states, cycle_index, time_in_phase


# ======================================================================
# Loaders (formats verified against real SWC output + upstream writers)
# ======================================================================
def load_reversal(path):
    """reversal_annotation.csv: index + 1 data column of {-1, 0, 1}."""
    df = pd.read_csv(path, index_col=0)
    return df.iloc[:, 0].to_numpy()


def load_turn(path):
    """turn_annotation_by_roundness.csv: has a binary 'turn' column."""
    df = pd.read_csv(path, index_col=0)
    return df["turn"].to_numpy()


def load_centroid_px(x_path, y_path):
    """Skeleton spline coords (header=None, index=None) -> per-frame centroid (px)."""
    xs = pd.read_csv(x_path, header=None)
    ys = pd.read_csv(y_path, header=None)
    return xs.mean(axis=1, skipna=True).to_numpy(), ys.mean(axis=1, skipna=True).to_numpy()


def load_hilbert_per_frame(path, take_abs=False):
    """
    Collapse a headerless Hilbert kymogram CSV (frames x body-segments, written by
    the existing hilbert_transform_on_kymogram rule) to one robust value per frame
    (nanmedian across body segments). Returns None if missing/empty/unreadable so
    the feature is simply skipped.

    take_abs=True for instantaneous frequency: its sign encodes body-wave
    direction; the magnitude is the body-bend frequency (Hz) we want as a feature.
    """
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p, header=None)
    except Exception:  # noqa: BLE001
        return None
    if df.shape[0] == 0:
        return None
    vals = df.apply(pd.to_numeric, errors="coerce")
    if take_abs:
        vals = vals.abs()
    return vals.median(axis=1, skipna=True).to_numpy()


def load_track_txt(track_txt, fps):
    """
    Read the SWC tracker log. Returns a dict with per-frame arrays:
        frame     : absolute recording frame index
        abs_time  : absolute recording time (s)
        x, y      : absolute arena position (px)
    or None if the file is missing / not in the expected format.

    Expected header (SWC v1.x):
        frame,time,X,Y,time_imputed_seconds
    `time` may be blank; `time_imputed_seconds` is the reliable clock and
    equals frame/fps. We fall back to frame/fps if that column is absent.
    """
    p = Path(track_txt)
    if not p.exists():
        # Robustness: the SWC writes "<name>_track_N.txt"; the pipeline expects
        # "track.txt" after rename_tracks.py. If the exact name is absent, fall
        # back to the SWC-style sibling in the same crop dir.
        siblings = sorted(p.parent.glob("*_track_*.txt")) or sorted(p.parent.glob("*.txt"))
        if not siblings:
            return None
        p = siblings[0]
        print(f"[info] {track_txt} not found; using SWC log {p.name}", file=sys.stderr)
    try:
        df = pd.read_csv(p)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] could not read {track_txt} ({e}).", file=sys.stderr)
        return None

    cols = {c.lower(): c for c in df.columns}
    if "x" not in cols or "y" not in cols:
        print(f"[warn] {track_txt} lacks X/Y columns {list(df.columns)}.", file=sys.stderr)
        return None

    x = df[cols["x"]].to_numpy(dtype=float)
    y = df[cols["y"]].to_numpy(dtype=float)

    if "frame" in cols:
        frame = df[cols["frame"]].to_numpy(dtype=float)
    else:
        frame = np.arange(len(df), dtype=float)

    if "time_imputed_seconds" in cols:
        abs_time = df[cols["time_imputed_seconds"]].to_numpy(dtype=float)
    elif "time" in cols and df[cols["time"]].notna().any():
        abs_time = df[cols["time"]].to_numpy(dtype=float)
    else:
        abs_time = frame / fps

    return {"frame": frame, "abs_time": abs_time, "x": x, "y": y}


def load_missing_frames(crop_dir):
    """
    Read the SWC crop ledger `<crop>_metadata.json` and return its per-frame
    `is_missing_frame` list (True = animal occluded/lost -> blank crop frame),
    or None if no ledger is found / it lacks the key.

    The ledger's `frame_indices` are contiguous first..last, exactly like the
    crop tif and (current SWC) track.txt, so the returned mask is aligned to the
    behaviour/position arrays by POSITION -- no reindexing needed.

    We search the crop dir for `track_metadata.json` first (if rename_tracks.py
    renamed it to the pipeline convention), then the native SWC
    `*_track_*_metadata.json`, then any `*_metadata.json`.
    """
    d = Path(crop_dir)
    if not d.is_dir():
        return None
    candidates = (
        sorted(d.glob("track_metadata.json"))
        or sorted(d.glob("*_track_*_metadata.json"))
        or sorted(d.glob("*_metadata.json"))
    )
    if not candidates:
        return None
    try:
        with open(candidates[0]) as f:
            meta = json.load(f)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] could not read crop ledger {candidates[0]} ({e}).", file=sys.stderr)
        return None
    missing = meta.get("is_missing_frame")
    if missing is None:
        return None
    return np.asarray(missing, dtype=bool)


def _signed_velocity(x_mm, y_mm, reversal_active, fps, smooth_win, occluded=None):
    """Speed magnitude (mm/s) signed by reversal state (reversal -> negative).

    Occluded frames carry a NaN arena position (the animal was lost). A raw
    np.gradient would spread that NaN onto the two *neighbouring*, non-occluded
    frames and silently blank their velocity even though they were tracked fine.
    We therefore interpolate the position gaps before differentiating -- so real
    neighbours keep a valid (gap-spanning) speed -- and then re-mask the occluded
    frames themselves to NaN (they are dropped at analysis time anyway, and their
    velocity is not real). If every position is NaN, the result is all-NaN.
    """
    xs = pd.Series(x_mm, dtype=float).interpolate(limit_direction="both")
    ys = pd.Series(y_mm, dtype=float).interpolate(limit_direction="both")
    x = xs.rolling(smooth_win, min_periods=1, center=True).mean().to_numpy()
    y = ys.rolling(smooth_win, min_periods=1, center=True).mean().to_numpy()
    if len(x) >= 2:
        speed = np.sqrt(np.gradient(x) ** 2 + np.gradient(y) ** 2) * fps
    else:
        speed = np.zeros(len(x))
    direction = np.where(reversal_active == 1, -1.0, 1.0)
    vel = speed * direction
    if occluded is not None:
        vel = np.where(np.asarray(occluded) > 0.5, np.nan, vel)
    return vel


def _fit_length(arr, n):
    """Truncate or NaN-pad a 1-D array to length n so all columns align."""
    arr = np.asarray(arr, dtype=float)
    if len(arr) >= n:
        return arr[:n]
    out = np.full(n, np.nan)
    out[: len(arr)] = arr
    return out


# ======================================================================
def main(arg_list=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crop_id", required=True, help="Crop_ID (the track_dir name)")
    ap.add_argument("--reversal_annotation", required=True)
    ap.add_argument("--turn_annotation", required=True)
    ap.add_argument("--skeleton_x", required=True, help="velocity fallback only")
    ap.add_argument("--skeleton_y", required=True, help="velocity fallback only")
    ap.add_argument("--worm_pos", required=True, help="SWC track.txt (authoritative clock + arena position)")
    ap.add_argument("--bend_freq", default="", help="hilbert_inst_freq.csv (optional -> Bend_Frequency)")
    ap.add_argument("--bend_amplitude", default="", help="hilbert_inst_amplitude.csv (optional -> Bend_Amplitude)")
    ap.add_argument("--fps", type=float, required=True)
    ap.add_argument("--factor_px_to_mm", type=float, required=True)
    ap.add_argument("--speed_smooth_window", type=int, default=None,
                    help="rolling window (frames) for position smoothing; default = round(fps)")
    # protocol timing
    ap.add_argument("--t0_offset_s", type=float, default=0.0,
                    help="absolute recording time at which the gas protocol starts")
    ap.add_argument("--baseline_duration_s", type=float, required=True)
    ap.add_argument("--baseline_state", required=True)
    ap.add_argument("--cycle_json", required=True,
                    help='JSON list of {"state","duration_s"} phases')
    ap.add_argument("--n_cycles", default="none")
    # output
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args(arg_list)

    cycle = json.loads(args.cycle_json)
    n_cycles = None if str(args.n_cycles).lower() in ("none", "null", "") else int(args.n_cycles)
    smooth_win = args.speed_smooth_window or max(1, int(round(args.fps)))

    # ---- behaviour arrays (derived from the crop tif) ----
    reversal = load_reversal(args.reversal_annotation)
    turn = load_turn(args.turn_annotation)

    # ---- authoritative clock + position from SWC track.txt ----
    track = load_track_txt(args.worm_pos, args.fps)

    if track is not None:
        # Absolute recording clock. Align behaviour arrays from the first frame;
        # tif vs track.txt can differ by ~1 frame, so trim to the common length.
        n = min(len(track["frame"]), len(reversal), len(turn))
        abs_frame = track["frame"][:n]
        abs_time = track["abs_time"][:n]
        x_mm = track["x"][:n] * args.factor_px_to_mm
        y_mm = track["y"][:n] * args.factor_px_to_mm
    else:
        # Fallback: no track.txt -> local clock + crop-centroid speed.
        print(f"[warn] {args.worm_pos} unusable -- local clock (Frame/fps) and "
              f"crop-centroid speed; ABSOLUTE gas alignment NOT guaranteed.", file=sys.stderr)
        cx, cy = load_centroid_px(args.skeleton_x, args.skeleton_y)
        n = min(len(cx), len(cy), len(reversal), len(turn))
        abs_frame = np.arange(n, dtype=float)
        abs_time = abs_frame / args.fps
        x_mm = cx[:n] * args.factor_px_to_mm
        y_mm = cy[:n] * args.factor_px_to_mm

    if n == 0:
        raise ValueError(f"[{args.crop_id}] no frames to process (empty inputs).")

    # ---- per-frame occlusion mask from the SWC crop ledger (optional) ----
    # Located next to track.txt (the crop dir). Aligned by position (same
    # contiguous frame range as the behaviour arrays). Absent -> all-False.
    missing = load_missing_frames(Path(args.worm_pos).parent)
    if missing is not None:
        occluded = (_fit_length(missing.astype(float), n) > 0.5).astype(int)
    else:
        occluded = np.zeros(n, dtype=int)

    reversal = _fit_length(reversal, n)
    turn = _fit_length(turn, n)
    reversal_active = (reversal == -1).astype(int)
    # reversal onset = frame where reversal starts (0 -> 1); enables reversal-
    # reaction-to-gas-shift analysis (generalises curvature/src/rev_reaction.py).
    reversal_onset = np.zeros(n, dtype=int)
    reversal_onset[1:] = ((reversal_active[1:] == 1) & (reversal_active[:-1] == 0)).astype(int)

    forward_velocity = _signed_velocity(x_mm, y_mm, reversal_active, args.fps,
                                        smooth_win, occluded=occluded)

    # ---- body-bend metrics from the existing Hilbert outputs (optional) ----
    bend_freq = load_hilbert_per_frame(args.bend_freq, take_abs=True)      # Hz
    bend_amp = load_hilbert_per_frame(args.bend_amplitude, take_abs=False)  # curvature units
    bend_freq = _fit_length(bend_freq, n) if bend_freq is not None else np.full(n, np.nan)
    bend_amp = _fit_length(bend_amp, n) if bend_amp is not None else np.full(n, np.nan)

    # ---- gas state from ABSOLUTE time, offset to protocol start ----
    protocol_time = abs_time - args.t0_offset_s
    o2_state, cycle_index, time_in_phase = build_o2_state(
        protocol_time, args.baseline_duration_s, args.baseline_state, cycle, n_cycles
    )

    # ---- tidy output (originally-requested columns first, then enrichments) ----
    out = pd.DataFrame({
        "Crop_ID": args.crop_id,
        "Frame": abs_frame.astype(int),
        "Time_Seconds": abs_time,
        "O2_State": o2_state,
        "Cycle_Index": cycle_index,
        "Time_In_Phase_s": time_in_phase,
        "Forward_Velocity": forward_velocity,
        "Reversal_Active": reversal_active,
        "Turn_Active": np.nan_to_num(turn, nan=0).astype(int),
        "Reversal_Onset": reversal_onset,
        "Bend_Frequency": bend_freq,
        "Bend_Amplitude": bend_amp,
        "Occluded": occluded,
        # Absolute arena position (mm). From track.txt when available, else the
        # crop centroid (fallback). Kept so analysis-time QC can measure absolute
        # displacement / positional spread per crop without re-reading track.txt.
        "X_mm": x_mm,
        "Y_mm": y_mm,
        # TRUE per-recording frame rate (from SWC parameters.yaml via the
        # Snakefile). Constant per crop; lets downstream analysis convert frames
        # to seconds with the real rate instead of assuming 10 fps.
        "fps": float(args.fps),
    })
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False)
    n_occ = int(occluded.sum())
    occ_note = f", {n_occ} occluded" if n_occ else ""
    print(f"[{args.crop_id}] wrote {len(out)} frames "
          f"({out.Time_Seconds.iloc[0]:.1f}-{out.Time_Seconds.iloc[-1]:.1f}s{occ_note}) -> {args.out_csv}")


if __name__ == "__main__":
    main(sys.argv[1:])
