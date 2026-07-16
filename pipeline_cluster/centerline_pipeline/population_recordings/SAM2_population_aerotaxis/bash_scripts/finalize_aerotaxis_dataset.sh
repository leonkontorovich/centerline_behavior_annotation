#!/usr/bin/env bash
# Finalize a whole aerotaxis dataset once the per-recording pipeline has run:
#   1. combine every crop's temporal_features.csv into one tidy table
#      (create_results_dict_server.py -> aerotaxis_results.<format>)
#   2. run the standard analysis (aerotaxis_analysis.py -> analysis/ with
#      per-state summary, transition-triggered averages, habituation, QC table,
#      and condition statistics).
#
# Run from the dataset root (the folder that contains the *_new/ recording
# folders), or pass the dataset dir as the first argument.
#
# Usage:
#   finalize_aerotaxis_dataset.sh [dataset_dir] [--pulse_state 21pct_O2] [--format parquet] [-- <extra aerotaxis_analysis args>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UTILS="${SCRIPT_DIR}/../toolscripts/utils"

DATASET="."
PULSE_STATE=""
FORMAT="parquet"
EXTRA=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pulse_state) PULSE_STATE="$2"; shift 2 ;;
    --format)      FORMAT="$2"; shift 2 ;;
    --)            shift; EXTRA=("$@"); break ;;
    -*)            echo "Unknown option: $1" >&2; exit 1 ;;
    *)             DATASET="$1"; shift ;;
  esac
done

DATASET="$(cd "$DATASET" && pwd)"
RESULTS="${DATASET}/aerotaxis_results.${FORMAT}"

echo "=========================================="
echo "📦 Finalizing dataset: $DATASET"
echo "=========================================="

echo "▶ Step 1/2: combining per-crop temporal_features.csv ..."
python3 "${UTILS}/create_results_dict_server.py" "$DATASET" --format "$FORMAT"

echo "▶ Step 2/2: running analysis -> ${DATASET}/analysis/ ..."
ANALYSIS_ARGS=("$RESULTS" --outdir "${DATASET}/analysis")
[[ -n "$PULSE_STATE" ]] && ANALYSIS_ARGS+=(--pulse_state "$PULSE_STATE")
# ${EXTRA[@]+...} guards against "unbound variable" for an empty array on bash 3.2
python3 "${UTILS}/aerotaxis_analysis.py" "${ANALYSIS_ARGS[@]}" ${EXTRA[@]+"${EXTRA[@]}"}

echo "=========================================="
echo "✅ Done. Combined table: $RESULTS"
echo "   Summaries + figures:  ${DATASET}/analysis/"
echo "=========================================="
