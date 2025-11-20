#!/usr/bin/env python3
import os
import argparse
import shutil
import numpy as np
import cv2
from PIL import Image

# -------- feature extraction (unchanged defaults) --------
def compute_shape_features(contour):
    area = cv2.contourArea(contour)
    if area <= 0:
        return None
    per = cv2.arcLength(contour, True)
    circularity = (4.0 * np.pi * area / (per ** 2)) if per > 0 else 0.0
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = (float(w) / h) if h > 0 else 0.0
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = (area / hull_area) if hull_area > 0 else 0.0
    if len(contour) >= 5:
        (_, _), axes, _ = cv2.fitEllipse(contour)
        major = max(axes); minor = min(axes)
        ecc = np.sqrt(max(0.0, 1.0 - (minor / major) ** 2)) if major > 0 else 0.0
    else:
        ecc = 0.0
    return np.array([ecc, solidity, aspect_ratio, circularity], dtype=float)

def extract_frame_features(frame):
    if frame.ndim == 3 and frame.shape[2] == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    biggest = max(contours, key=cv2.contourArea)
    return compute_shape_features(biggest)

def average_stack_features(tif_path, sample_frames=500, rng_seed=42):
    feats = []
    rng = np.random.default_rng(rng_seed)
    with Image.open(tif_path) as img:
        n = getattr(img, "n_frames", 1)
        idxs = np.arange(n) if n <= sample_frames else rng.choice(n, size=sample_frames, replace=False)
        for i in idxs:
            try:
                img.seek(int(i))
                f = extract_frame_features(np.array(img))
                if f is not None:
                    feats.append(f)
            except Exception:
                continue
    if not feats:
        return None
    return np.mean(np.vstack(feats), axis=0)

# -------- bubble rule (your defaults) --------
def looks_like_bubble(avg_feats, sol_thresh=0.90, circ_thresh=0.50, ar_tol=0.10):
    _, sol, ar, circ = avg_feats
    return (sol >= sol_thresh) and (circ >= circ_thresh) and (abs(ar - 1.0) <= ar_tol)

# -------- FAST finder (depth-limited, no os.walk) --------
def iter_track_tifs(src):
    """
    Prefer: src/_track_*/track.tif
    Else: src/{session}/_track_*/track.tif
    Skip folders named 'output'.
    """
    src = os.path.abspath(src)

    def track_dirs_in(folder):
        with os.scandir(folder) as it:
            for e in it:
                if not e.is_dir():
                    continue
                name = e.name
                if name == "output" or name.startswith('.'):
                    continue
                if "_track_" in name:
                    tif = os.path.join(e.path, "track.tif")
                    if os.path.isfile(tif):
                        yield tif

    # Case 1: tracks directly under src
    direct = list(track_dirs_in(src))
    if direct:
        for t in direct:
            yield t
        return

    # Case 2: one level of sessions, then _track_* under each
    with os.scandir(src) as sessions:
        for s in sessions:
            if not s.is_dir() or s.name.startswith('.'):
                continue
            for t in track_dirs_in(s.path):
                yield t

def main():
    ap = argparse.ArgumentParser(description="Delete bubble-like track.tif folders (fast scan).")
    ap.add_argument("src", help="Root folder (e.g., elpiniki_data)")
    ap.add_argument("--sample-frames", type=int, default=500)
    ap.add_argument("--sol-thresh", type=float, default=0.90)
    ap.add_argument("--circ-thresh", type=float, default=0.50)
    ap.add_argument("--ar-tol", type=float, default=0.10)
    ap.add_argument("--delete", action="store_true", help="Actually delete; otherwise dry-run")
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    if not os.path.isdir(src):
        raise SystemExit(f"Not a directory: {src}")

    total = kept = marked = skipped = 0
    for tif in iter_track_tifs(src):
        total += 1
        parent = os.path.dirname(tif)
        feats = average_stack_features(tif, sample_frames=args.sample_frames)
        if feats is None:
            skipped += 1
            print(f"[SKIP] No features extracted: {tif}")
            continue
        if looks_like_bubble(feats, args.sol_thresh, args.circ_thresh, args.ar_tol):
            marked += 1
            if args.delete:
                try:
                    shutil.rmtree(parent)
                    print(f"[DEL ] Bubble -> removed: {parent}")
                except Exception as e:
                    print(f"[ERR ] Failed to delete {parent}: {e}")
            else:
                print(f"[DRY ] Bubble -> would delete: {parent}")
        else:
            kept += 1
            ecc, sol, ar, circ = feats
            print(f"[KEEP] {parent} (ecc={ecc:.3f}, sol={sol:.3f}, ar={ar:.3f}, circ={circ:.3f})")

    mode = "DELETE" if args.delete else "DRY-RUN"
    print(f"\nDone. scanned={total}, bubble_marked={marked}, kept={kept}, skipped={skipped}, mode={mode}")

if __name__ == "__main__":
    main()
