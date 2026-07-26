#!/usr/bin/env python3
"""
Measure how long your worms actually are, in pixels and mm, and recommend a
`min_worm_length_mm` for config.yaml.

WHY THIS EXISTS
---------------
`create_centerline` blanks any frame whose skeleton is shorter than
`min_worm_length`. That threshold used to be a hardcoded PIXEL constant
(`min_worm_lenght: 83`) tuned on a rig where worms imaged at ~1.0 mm. Run on a
dataset whose worms imaged at ~60-70 px, it blanked ~99% of frames; every crop
then collapsed to an empty curvature table and 4190 of 4576 crops died in
annotate_reversals with an opaque KeyError. Nothing reported a threshold
problem, because nothing was measuring the worms.

This script closes that loop: it measures the worms, so the threshold is set
from data rather than inherited from another microscope.

HOW IT MEASURES (no GPU, no re-segmentation)
--------------------------------------------
The DLC keypoint files survive for every crop, and the corrected SAM2 masks do
not (they are temp() and deleted). So we measure in two steps:

  1. DLC span      -- the head->neck->vulva->tail polyline length, per frame,
                      for every sampled crop. Available everywhere, but it
                      CHORDS a curved worm and so underestimates the true
                      centerline length.
  2. Ratio k       -- on frames where a real skeleton DID survive, we have both
                      measurements, so we estimate k = skeleton / DLC span
                      empirically instead of assuming it (expect ~1.1-1.4).

Predicted true length = k * DLC span, computed for all sampled crops. The
recommendation is a floor set safely below the low tail of that distribution:
this threshold's job is rejecting debris, not staging worms.

CAVEATS -- read before trusting a tight number:

  * If a dataset has NO surviving skeletons anywhere, k cannot be measured and
    the script says so, falling back to an assumed 1.25 rather than inventing a
    number.
  * Where k CAN be measured, it is estimated from the frames that survived
    create_centerline's own length filter -- which are, by construction, the
    LONGEST frames. So a measured k is biased UPWARD, and the more aggressive
    the current threshold, the worse the bias (observed across five recordings
    of one dataset: k = 0.99, 1.25, 1.25, 1.34, 1.76, with the extreme value
    coming from the recording where almost nothing survived). Predicted lengths
    and hence the recommendation inherit that upward bias.
    Practical consequence: prefer the LOWEST recommendation across your
    recordings, not the mean, and treat all of them as upper bounds. Re-run
    after a pass with a corrected threshold to get an unbiased k.

Because of that bias, this script deliberately recommends a floor at half the
1st percentile rather than something tighter. Over-culling is the failure mode
that destroys datasets; letting a little debris through costs nothing, since the
analysis-time aliveness gate removes it anyway.

USAGE
-----
    python calibrate_min_worm_length.py <dataset_dir> [--per-recording 25]

    # single recording
    python calibrate_min_worm_length.py <dataset>/<recording>_new

Writes a summary table to stdout and, with --out_csv, the per-crop measurements.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# DLC keypoints in head->tail order. Only those present are used, so a model
# with a different subset still yields a (shorter) polyline.
BODYPART_ORDER = ["head", "nose", "neck", "vulva", "tail"]

# Per-frame keypoint confidence below which the frame is not used for the span
# measurement. Low-confidence frames are exactly the ones with bad keypoint
# geometry, which would widen the distribution with noise rather than biology.
MIN_LIKELIHOOD = 0.6

# Fraction of the measured low tail to place the recommended floor at. 0.5 puts
# the threshold at half the smallest real worm -- comfortably below biology,
# comfortably above debris.
FLOOR_FRACTION = 0.5

# Fallback px->mm if a recording has neither pixel_size_mm nor the arena/frame
# pair. Mirrors config.yaml's fallback; reported loudly when used.
FALLBACK_PX_TO_MM = 0.01221

# Paired (skeleton, DLC) frames to gather before we stop reading skeleton CSVs.
# k is a single scalar; this many frames determine it to well under a percent,
# and the reads are the slowest part of the scan on a network mount.
RATIO_SAMPLE_TARGET = 3000


def swc_px_to_mm(recording_dir: Path):
    """
    px->mm for a recording, mirroring the Snakefile's resolution order.
    Returns (value, source) so the caller can flag an assumed calibration.
    """
    path = recording_dir / "parameters.yaml"
    try:
        with open(path) as f:
            rec = (yaml.safe_load(f) or {}).get("recording", {}) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return FALLBACK_PX_TO_MM, "fallback (no parameters.yaml)"

    try:
        pix = float(rec.get("pixel_size_mm"))
        if pix > 0:
            return pix, "parameters.yaml:pixel_size_mm"
    except (TypeError, ValueError):
        pass
    try:
        arena_cm = float(rec.get("arena_size_cm"))
        frame_px = float(rec.get("frame_height_px"))
        if arena_cm > 0 and frame_px > 0:
            return arena_cm * 10.0 / frame_px, "parameters.yaml:arena/frame"
    except (TypeError, ValueError):
        pass
    return FALLBACK_PX_TO_MM, "fallback (parameters.yaml lacks pixel_size_mm and frame_height_px)"


def dlc_span_per_frame(h5_path: Path):
    """
    Per-frame head->tail polyline length in px, and the per-frame minimum
    keypoint likelihood. Returns (span, likelihood) or (None, None).
    """
    try:
        df = pd.read_hdf(h5_path)
    except Exception:  # unreadable/partial h5 -- skip this crop, do not abort
        return None, None
    if isinstance(df.columns, pd.MultiIndex) and df.columns.nlevels == 3:
        df = df.copy()
        df.columns = df.columns.droplevel(0)

    present = list(dict.fromkeys(c[0] for c in df.columns))
    order = [b for b in BODYPART_ORDER if b in present]
    if len(order) < 2:
        return None, None

    span = np.zeros(len(df), dtype=float)
    for a, b in zip(order, order[1:]):
        span += np.hypot(df[(a, "x")].to_numpy() - df[(b, "x")].to_numpy(),
                         df[(a, "y")].to_numpy() - df[(b, "y")].to_numpy())
    like = np.min([df[(b, "likelihood")].to_numpy() for b in order], axis=0)
    return span, like


def skeleton_length_per_frame(x_csv: Path, y_csv: Path):
    """
    Per-frame skeleton path length in px; NaN where the frame has < 2 points.
    These are the frames that survived create_centerline's own filter, so they
    are a BIASED (upper) sample of lengths -- used only to calibrate the ratio
    k against DLC on the same frames, never as the length distribution itself.
    """
    try:
        x = pd.read_csv(x_csv, header=None)
        y = pd.read_csv(y_csv, header=None)
    except Exception:
        return None
    xv, yv = x.to_numpy(dtype=float), y.to_numpy(dtype=float)
    n = min(len(xv), len(yv))
    out = np.full(n, np.nan)
    for i in range(n):
        xi, yi = xv[i], yv[i]
        m = ~(np.isnan(xi) | np.isnan(yi))
        if m.sum() < 2:
            continue
        out[i] = np.nansum(np.hypot(np.diff(xi[m]), np.diff(yi[m])))
    return out


def find_crops(root: Path, per_recording: int):
    """
    Yield (recording_dir, crop_dir) pairs. Handles both a dataset root (many
    <recording>_new/<recording>/<crop>/) and a single recording folder.
    Sampling is evenly spread across each recording's crops rather than taking
    the first N, so a recording whose early crops are all bubbles is not
    misrepresented.
    """
    # Fixed-depth globs, NOT rglob. The layout is known:
    #     <dataset>/<rec>_new/<rec>/<crop>/output      (dataset root)
    #     <rec>_new/<rec>/<crop>/output                (single recording)
    # rglob("*/output") descends into every crop's output directory and into any
    # stray nested cropper batch, which on a network mount turns a seconds-long
    # listing into a many-minute one. Globbing the exact depths visits only the
    # directories we need.
    # Shallowest pattern FIRST. Trying the deepest one first makes glob descend
    # an extra level on the shallower layouts -- which means a scandir inside
    # every crop's `output` directory, the single most expensive thing you can
    # do here over a network mount. Shallow-first is safe because the shallower
    # patterns simply match nothing on a deeper layout.
    recordings = {}
    for pattern in ("*/output", "*/*/output", "*/*/*/output"):
        for out_dir in root.glob(pattern):
            crop = out_dir.parent
            recordings.setdefault(crop.parent, []).append(crop)
        if recordings:
            break

    for rec in sorted(recordings):
        crops = sorted(recordings[rec])
        if per_recording and len(crops) > per_recording:
            idx = np.linspace(0, len(crops) - 1, per_recording).astype(int)
            crops = [crops[i] for i in sorted(set(idx))]
        for crop in crops:
            yield rec, crop


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dataset", nargs="?", default=".",
                    help="dataset root or a single <recording>_new folder")
    ap.add_argument("--per-recording", type=int, default=25,
                    help="crops to sample per recording (0 = all). Reading DLC "
                         "h5 files over a network mount is the slow part.")
    ap.add_argument("--out_csv", default=None,
                    help="optional path for the per-crop measurement table")
    args = ap.parse_args(argv)

    root = Path(args.dataset).resolve()
    rows = []
    paired_ratios = []

    print(f"Scanning {root} ...", file=sys.stderr)
    crops = list(find_crops(root, args.per_recording))
    total = len(crops)
    print(f"Measuring {total} crops (DLC h5 + skeleton CSVs). On a network "
          f"mount this is I/O-bound and can take several minutes.",
          file=sys.stderr)

    for i, (rec, crop) in enumerate(crops, 1):
        if i % 10 == 0 or i == total:
            print(f"  [{i}/{total}] {len(rows)} measured  ({rec.name})",
                  file=sys.stderr, flush=True)
        out = crop / "output"
        h5 = next(out.glob("track*_filtered.h5"), None)
        if h5 is None:
            continue
        span, like = dlc_span_per_frame(h5)
        if span is None:
            continue
        good = np.isfinite(span) & (like >= MIN_LIKELIHOOD)
        if good.sum() < 10:  # too few confident frames to characterise the crop
            continue
        median_span = float(np.median(span[good]))

        # Pair with surviving skeleton frames to estimate k, where possible.
        # The two skeleton CSVs are the most expensive read in this loop, so
        # stop once k is well determined -- a few thousand paired frames pin a
        # single ratio far more tightly than needed, and the DLC spans (the
        # actual distribution) are still collected for every crop.
        skel = None
        if len(paired_ratios) < RATIO_SAMPLE_TARGET:
            skel = skeleton_length_per_frame(out / "skeleton_spline_X_coords.csv",
                                             out / "skeleton_spline_Y_coords.csv")
        n_skel = 0
        if skel is not None:
            n = min(len(skel), len(span))
            both = np.isfinite(skel[:n]) & good[:n] & (span[:n] > 0)
            n_skel = int(both.sum())
            if n_skel:
                paired_ratios.extend((skel[:n][both] / span[:n][both]).tolist())

        px_to_mm, src = swc_px_to_mm(rec)
        rows.append({
            "recording": rec.name, "crop": crop.name,
            "n_frames_confident": int(good.sum()),
            "dlc_span_px": median_span,
            "n_skeleton_frames": n_skel,
            "px_to_mm": px_to_mm, "px_to_mm_source": src,
        })

    if not rows:
        print("No measurable crops found (no DLC *_filtered.h5 with confident "
              "frames). Nothing to calibrate.", file=sys.stderr)
        return 1

    df = pd.DataFrame(rows)
    if args.out_csv:
        df.to_csv(args.out_csv, index=False)
        print(f"Per-crop measurements -> {args.out_csv}", file=sys.stderr)

    # ---- ratio k: skeleton length / DLC span, measured not assumed ----
    if paired_ratios:
        k = float(np.median(paired_ratios))
        k_note = (f"measured from {len(paired_ratios):,} frames where both a "
                  f"skeleton and confident DLC keypoints exist")
        k_reliable = True
    else:
        k = 1.25
        k_note = ("ASSUMED -- no crop had both a surviving skeleton and "
                  "confident DLC keypoints, so the ratio could not be measured. "
                  "Treat every length below as approximate")
        k_reliable = False

    df["pred_skeleton_px"] = df.dlc_span_px * k
    df["pred_skeleton_mm"] = df.pred_skeleton_px * df.px_to_mm

    print()
    print("=" * 72)
    print("WORM LENGTH CALIBRATION")
    print("=" * 72)
    print(f"Crops measured        : {len(df):,} across {df.recording.nunique()} recordings")
    print(f"Skeleton/DLC ratio k  : {k:.3f}  ({k_note})")

    fallback = df[df.px_to_mm_source.str.startswith("fallback")]
    if len(fallback):
        print(f"\n  !! {len(fallback)} crops in {fallback.recording.nunique()} "
              f"recording(s) have NO px->mm in parameters.yaml and used the "
              f"{FALLBACK_PX_TO_MM} mm/px fallback. Their mm figures are only as "
              f"good as that assumption -- verify it before trusting them.")

    print("\nDLC span (px, per-crop medians):")
    for q in (1, 5, 25, 50, 75, 95):
        print(f"   p{q:<3d} {np.percentile(df.dlc_span_px, q):7.1f}")

    print(f"\nPredicted true skeleton length (px = DLC span x {k:.3f}):")
    for q in (1, 5, 25, 50, 75, 95):
        print(f"   p{q:<3d} {np.percentile(df.pred_skeleton_px, q):7.1f}")

    print("\nPredicted true skeleton length (mm):")
    for q in (1, 5, 25, 50, 75, 95):
        print(f"   p{q:<3d} {np.percentile(df.pred_skeleton_mm, q):7.3f}")

    # ---- what each candidate threshold would cost you ----
    p1_mm = float(np.percentile(df.pred_skeleton_mm, 1))
    recommended = round(p1_mm * FLOOR_FRACTION, 2)

    print("\n" + "-" * 72)
    print("Crops that would be LOST at each candidate min_worm_length_mm")
    print("(a crop is lost when its median frame falls below the floor)")
    print("-" * 72)
    for cand in sorted({0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, recommended}):
        lost = int((df.pred_skeleton_mm < cand).sum())
        bar = "#" * int(40 * lost / len(df))
        mark = "  <-- recommended" if abs(cand - recommended) < 1e-9 else ""
        print(f"   {cand:4.2f} mm : {lost:5d}/{len(df)} ({100*lost/len(df):5.1f}%) {bar}{mark}")

    print("\n" + "=" * 72)
    print(f"RECOMMENDATION:  min_worm_length_mm: {recommended}")
    print("=" * 72)
    print(f"That is {FLOOR_FRACTION:g} x the 1st percentile of measured worm length "
          f"({p1_mm:.3f} mm),")
    print("i.e. a junk floor comfortably below the smallest real worm. Raising it")
    print("toward the median does NOT improve data quality -- it silently deletes")
    print("frames. Real-worm selection is the analysis-time aliveness gate's job.")
    if not k_reliable:
        print("\nNOTE: k was assumed, not measured. Re-run this after any run that")
        print("produces real skeletons to confirm the number.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
