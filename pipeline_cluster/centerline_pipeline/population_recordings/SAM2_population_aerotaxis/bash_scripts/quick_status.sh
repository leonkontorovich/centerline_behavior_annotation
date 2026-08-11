#!/bin/bash

# Fast Pipeline Status Checker
# Quick validation of Snakemake pipeline completion

# Colors
G='\033[0;32m' # Green
R='\033[0;31m' # Red
Y='\033[1;33m' # Yellow
B='\033[1m'    # Bold
N='\033[0m'    # No color

# Config
SOURCE="${1:-$(pwd)}"
# Must match config.yaml `network_string` exactly, or the DLC-filtered stage is
# under-reported. (The previous default was truncated/mangled.)
NETWORK="${2:-DLC_resnet50_population_nose_neck_vulva_tail_elpiniki_chanuka_itamarSep23shuffle2_1030000}"

echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"
echo -e "${B}           SNAKEMAKE PIPELINE STATUS CHECK${N}"
echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"

# Count experiments and tracks
echo -e "\n${B}📂 Scanning filesystem...${N}"
EXP_COUNT=$(find "$SOURCE" -mindepth 1 -maxdepth 1 -type d | wc -l)
TOTAL=$(find "$SOURCE" -name "track.tif" | wc -l)

echo "   Experiments: $EXP_COUNT"
echo "   Total tracks: $TOTAL"

# Quick count of key outputs
echo -e "\n${B}🔍 Checking pipeline outputs...${N}"

# Final outputs (completed pipelines)
COMPLETED=$(find "$SOURCE" -path "*/output/temporal_features.csv" | wc -l)

# Intermediate permanent files
HILBERT=$(find "$SOURCE" -path "*/output/hilbert_inst_freq.csv" | wc -l)
REVERSALS=$(find "$SOURCE" -path "*/output/reversal_annotation.csv" | wc -l)
TURNS=$(find "$SOURCE" -path "*/output/turn_annotation_by_roundness.csv" | wc -l)
SKELETON=$(find "$SOURCE" -path "*/output/skeleton_spline_K_new_smoothed.csv" | wc -l)
CENTERLINE=$(find "$SOURCE" -path "*/output/skeleton_spline_K.csv" | wc -l)
DLC_FILTERED=$(find "$SOURCE" -path "*/output/track${NETWORK}_filtered.h5" | wc -l)

# Count tracks with any output (started)
STARTED=$(find "$SOURCE" -type d -name "output" -exec sh -c '[ "$(find "$1" -type f | wc -l)" -gt 0 ]' _ {} \; -print | wc -l)

# Calculate derived metrics
NOT_STARTED=$((TOTAL - STARTED))
RUNNING_OR_FAILED=$((STARTED - COMPLETED))

# Infer explicit failures from workflow logs (one failure per Error in rule line)
EXPLICIT_FAILS=$(find "$SOURCE" -maxdepth 2 -name "workflow_*.log" -o -name "slurm-*.out" 2>/dev/null | xargs -I {} grep -h '^Error in rule' "{}" 2>/dev/null | wc -l | awk '{print $1}')


# Infer temp file steps from permanent downstream files
# If DLC filtered exists, temp files (tiff2avi, dlc_analyze, sam2) must have succeeded
TIFF2AVI=$DLC_FILTERED
DLC_ANALYZE=$DLC_FILTERED
SAM2=$DLC_FILTERED
CORRECTED=$DLC_FILTERED

# If centerline exists but DLC filtered doesn't, those steps still succeeded
if [[ $CENTERLINE -gt $DLC_FILTERED ]]; then
    TIFF2AVI=$CENTERLINE
    DLC_ANALYZE=$CENTERLINE
    SAM2=$CENTERLINE
    CORRECTED=$CENTERLINE
fi

# Output summary
echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"
echo -e "${B}                 OVERALL STATUS${N}"
echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"

COMP_PCT=$(awk "BEGIN {printf \"%.1f\", $COMPLETED * 100 / $TOTAL}")
FAIL_PCT=$(awk "BEGIN {printf \"%.1f\", $RUNNING_OR_FAILED * 100 / $TOTAL}")
NOT_PCT=$(awk "BEGIN {printf \"%.1f\", $NOT_STARTED * 100 / $TOTAL}")

printf "Total tracks:      %4d\n" "$TOTAL"
printf "${G}✅ Completed:       %4d${N} (%s%%)\n" "$COMPLETED" "$COMP_PCT"
printf "${R}❌ Not finished:          %4d${N} (%s%%)\n" "$RUNNING_OR_FAILED" "$FAIL_PCT"
printf "⏸️  Not started:     %4d (%s%%)\n" "$NOT_STARTED" "$NOT_PCT"
printf "${R}💥 Explicit Fails:  %4d${N} (from logs)\n" "$EXPLICIT_FAILS"

echo -e "\n${B}Note:${N}"
echo -e "  • Temporary files are deleted after processing (marked as temp() in Snakefile)"
echo -e "  • Their success is ${B}inferred${N} from permanent downstream files"
echo -e "  • Permanent files are ${B}actually checked${N} on disk"

echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"
echo -e "${B}           TEMPORARY FILES (Inferred from Downstream)${N}"
echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"

print_stage() {
    local name="$1"
    local count=$2
    local pct=$(awk "BEGIN {printf \"%.1f\", $count * 100 / $TOTAL}")
    local fail=$((TOTAL - count))
    
    if (( $(echo "$pct >= 90" | bc -l) )); then
        icon="${G}✅${N}"
    elif (( $(echo "$pct >= 70" | bc -l) )); then
        icon="${Y}⚠️${N}"
    else
        icon="${R}❌${N}"
    fi
    
    printf "%b %-35s: %4d/%d (%.1f%%) | ❌%d\n" \
        "$icon" "$name" "$count" "$TOTAL" "$pct" "$fail"
}

# Temporary files (deleted after use, inferred from permanent downstream files)
print_stage "tiff2avi → track.avi" "$TIFF2AVI"
print_stage "dlc_analyze_videos → *.h5" "$DLC_ANALYZE"
print_stage "sam2_segment → track_mask.btf" "$SAM2"
print_stage "correct_SAM2_DLC_errors → *_corrected.btf" "$CORRECTED"

echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"
echo -e "${B}              PERMANENT OUTPUT FILES (Actually Present)${N}"
echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"

# Permanent output files (actually checked on disk)
print_stage "dlc_filter_predictions_arima" "$DLC_FILTERED"
print_stage "create_centerline" "$CENTERLINE"
print_stage "process_skeleton_curvature" "$SKELETON"
print_stage "calc_turns_by_roundness" "$TURNS"
print_stage "annotate_reversals" "$REVERSALS"
print_stage "hilbert_transform_on_kymogram" "$HILBERT"

echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"
echo -e "${B}                      FINAL OUTPUT${N}"
echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"

print_stage "temporal_features.csv" "$COMPLETED"

echo -e "\n${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"
echo -e "${B}                   RESULTS${N}"
echo -e "${B}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"

echo -e "\n${B}Pipeline Completion:${N} ${COMP_PCT}%"
echo -e "${B}Pipelines Finished:${N} ${G}${COMPLETED}${N}/${TOTAL}"

if [[ $COMPLETED -eq $TOTAL ]]; then
    echo -e "\n${G}${B}🎉 All pipelines completed successfully!${N}"
elif [[ $COMPLETED -eq 0 ]]; then
    if [[ $NOT_STARTED -eq $TOTAL ]]; then
        echo -e "\n${Y}⚠️  No pipelines have started yet${N}"
        echo -e "   Run: ${B}snakemake --cores N${N}"
    else
        echo -e "\n${R}❌ No pipelines have completed successfully${N}"
        echo -e "   ${FAILED} tracks started but failed"
        echo -e "   Check logs and rerun: ${B}snakemake --rerun-incomplete --cores N${N}"
    fi
else
    echo -e "\n${Y}💡 Status:${N}"
    echo -e "   • ${G}${COMPLETED}${N} tracks completed successfully"
    if [[ $RUNNING_OR_FAILED -gt 0 ]]; then
        echo -e "   • ${R}${RUNNING_OR_FAILED}${N} tracks need attention (started but incomplete)"
    fi
    if [[ $EXPLICIT_FAILS -gt 0 ]]; then
        echo -e "   • ${R}💥 Found ${EXPLICIT_FAILS} explicit failure(s) in logs${N} (grep '^Error in rule')"
    fi
    if [[ $NOT_STARTED -gt 0 ]]; then
        echo -e "   • ${NOT_STARTED} tracks not yet started"
    fi
fi

echo ""
