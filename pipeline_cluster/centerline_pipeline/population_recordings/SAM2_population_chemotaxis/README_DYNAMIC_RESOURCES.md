# Dynamic Resource Allocation with Snakemake and SLURM

## Overview

This guide explains how to implement **dynamic resource scaling** in Snakemake pipelines on SLURM clusters, where computational resources (CPU, memory, time) are automatically adjusted based on input data characteristics (e.g., video duration).

## The Problem

Standard Snakemake cluster submissions use **static resources** from `cluster_config.yaml`:
- A 3-minute video gets the same 24 CPUs and 64GB as a 30-minute video
- Wastes resources and queue time
- Inefficient scheduling

## The Solution: Dynamic Scaling

Resources scale proportionally to workload:
- 3-minute video → 2 CPUs, 6GB, 1 hour
- 30-minute video → 24 CPUs, 64GB, 8 hours

---

## Architecture

### 1. Pre-Generation Script (`generate_metadata.py`)

**Purpose:** Extract metadata (duration, frame count) from input files BEFORE running Snakemake.

**Why needed:** Snakemake needs to know resource requirements before job submission.

**Example:**
```python
def count_tiff_frames(tiff_path):
    result = subprocess.run(['tiffinfo', str(tiff_path)], ...)
    frame_count = result.stdout.count('TIFF Directory')
    return frame_count

# Write to: dataset/track_dir/output/.meta.json
metadata = {
    "streams": [{
        "duration": str(duration),
        "nb_frames": str(frame_count)
    }]
}
```

### 2. Snakefile Resource Functions

**Purpose:** Define functions that calculate resources dynamically based on metadata.

**Key Pattern:**
```python
MAX_CROP_SEC = 1800  # 30-minute baseline

def get_video_duration_seconds(wildcards):
    """Read metadata and return video duration"""
    path = f"{wildcards.dataset}/{wildcards.track_dir}/output/.meta.json"
    with open(path) as f:
        duration = float(json.load(f)["streams"][0]["duration"])
    return max(1.0, duration)

def create_scaled_threads_function(rule_name):
    """Returns a function that scales threads based on video duration"""
    def calculate_threads(wildcards):
        base = int(get_cluster_config_value(rule_name, "cpus_per_task", 1))
        scale = get_video_duration_seconds(wildcards) / MAX_CROP_SEC
        return max(1, min(base, math.ceil(base * scale)))
    return calculate_threads
```

**Usage in rules:**
```python
rule tiff2avi:
    input: "{dataset}/{track_dir}/output/.meta.json"  # Dependency on metadata
    output: "{dataset}/{track_dir}/output/track.avi"
    threads: create_scaled_threads_function("tiff2avi")
    resources:
        mem_mb=create_scaled_memory_function("tiff2avi"),
        time=create_scaled_time_function("tiff2avi"),
        partition=create_partition_function("tiff2avi"),
        gres=create_gres_function("tiff2avi")  # NOT USED - see below!
```

### 3. The GRES Problem and Wrapper Solution

#### The Critical Issue

**Problem:** When using `{resources.gres}` in the cluster command:
- If `gres` is empty → Snakemake **skips substitution entirely**
- Arguments shift left by one position
- `{rule}` goes into the GRES slot
- Job submission fails or uses wrong parameters

**Example of failure:**
```bash
# Expected:
./wrapper.sh TIME PART CPU MEM OUTPUT GRES RULE

# What actually happens when gres is empty:
./wrapper.sh TIME PART CPU MEM OUTPUT RULE JOBSCRIPT
                                            ↑     ↑
                                          GRES   JOB
                                         (WRONG!)
```

#### Why `{cluster.gres}` Instead of `{resources.gres}`

**Key Discovery:** Use `{cluster.gres}` from `cluster_config.yaml`:
- `{cluster.*}` values are **always substituted** (even when `null` or empty)
- `{resources.*}` values that are empty are sometimes **not substituted**
- For GRES, we don't need dynamic scaling anyway (it's either empty or `gpu:1`)

#### The Wrapper Script

**Purpose:** Conditionally include `--gres` flag only when it has a valid value.

**File:** `submit_wrapper.sh`
```bash
#!/usr/bin/env bash
# Wrapper to conditionally add --gres flag
# SLURM rejects --gres with empty value or "None"

TIME="$1"
PART="$2"
CPU="$3"
MEM="$4"
OUT="$5"
GRES="$6"
JOB="$7"
shift 7

# Build sbatch command
CMD="sbatch -t $TIME -p $PART --cpus-per-task $CPU --mem ${MEM}M --output $OUT --job-name=$JOB --nice=0"

# Only add --gres if it has a value AND is not the string "None"
if [ -n "$GRES" ] && [ "$GRES" != "None" ]; then
    CMD="$CMD --gres $GRES"
fi

# Execute
exec $CMD "$@"
```

**Why necessary:**
```bash
# Without wrapper:
sbatch ... --gres None ...  # ❌ SLURM: "Invalid TRES specification"
sbatch ... --gres ...       # ❌ SLURM: "Invalid TRES specification"

# With wrapper:
sbatch ...                  # ✅ No --gres flag (correct for non-GPU jobs)
sbatch ... --gres gpu:1     # ✅ GRES flag included (correct for GPU jobs)
```

### 4. Main Execution Script

**File:** `RUNME_cluster.sh`

**Key sections:**

```bash
# STEP 1: Pre-generate metadata
python3 ./generate_metadata.py

# STEP 2: Run Snakemake with wrapper
snakemake \
  --cluster "./submit_wrapper.sh {resources.time} {resources.partition} {threads} {resources.mem_mb} log/log_%x_%A_%a_%j.out {cluster.gres} {rule}" \
  --cluster-config cluster_config.yaml \
  ...
```

**Critical details:**
- Uses `{resources.*}` for **dynamically scaled** values (time, partition, threads, mem_mb)
- Uses `{cluster.gres}` for **static** GRES value (always substituted, no argument shift)
- Memory needs `M` suffix: `{resources.mem_mb}M`
- Wrapper path must be relative: `./submit_wrapper.sh`

---

## Configuration Files

### cluster_config.yaml

**Purpose:** Define baseline (maximum) resources for each rule.

```yaml
__default__:
    time: 0-08:00:00
    partition: basic
    cpus_per_task: 8
    mem: 64G
    output: log/log_%x_%A_%a_%j.out
    gres:  # Empty for non-GPU jobs

dlc_analyze_videos:
    time: 0-08:00:00
    partition: basic,gpu
    cpus_per_task: 24
    mem: 64G
    gres: gpu:1  # GPU required

sam2_segment:
    time: 0-12:00:00
    partition: basic,gpu
    mem: 128G
    gres: gpu:1  # Fixed resources (no scaling)
```

**Note:** For rules with fixed resources (no scaling), use `create_static_*_function()` instead of `create_scaled_*_function()`.

### config.yaml

**Purpose:** Pipeline parameters and paths.

```yaml
fps: 10
factor_px_to_mm: '0.00962'
dlc_model_configfile_path: /path/to/model/config.yaml
# ... other pipeline parameters
```

---

## Usage

### Setup

1. **Place scripts in working directory:**
   ```bash
   ls -la
   # RUNME_cluster.sh
   # submit_wrapper.sh
   # generate_metadata.py
   # Snakefile
   # cluster_config.yaml
   # config.yaml
   ```

2. **Make executable:**
   ```bash
   chmod +x RUNME_cluster.sh submit_wrapper.sh
   ```

### Running

```bash
# Run on cluster
./RUNME_cluster.sh

# Run locally (for testing)
./RUNME_cluster.sh -c
```

### Workflow

1. `generate_metadata.py` scans all `track.tif` files and creates `.meta.json`
2. Snakemake reads metadata and calculates scaled resources
3. Wrapper conditionally formats the sbatch command
4. Jobs submit to SLURM with appropriate resources

---

## Debugging

### Enable Verbose Output

Add to `RUNME_cluster.sh`:
```bash
--printshellcmds \
--verbose
```

### Check Wrapper Input

Add debug output to `submit_wrapper.sh`:
```bash
echo "===== WRAPPER DEBUG =====" >&2
echo "TIME:      '$TIME'" >&2
echo "PARTITION: '$PART'" >&2
echo "CPU:       '$CPU'" >&2
echo "MEM:       '$MEM'" >&2
echo "GRES:      '$GRES'" >&2
echo "JOB:       '$JOB'" >&2
echo "=========================" >&2
```

### Verify Job Submission

```bash
# Check running jobs
squeue -u $USER

# Check log files
ls -ltr log/
tail log/log_tiff2avi_*.out
```

---

## Common Pitfalls

### ❌ Using {resources.gres} in cluster command
```bash
# DON'T DO THIS:
--cluster "sbatch ... --gres {resources.gres} ..."
```
**Problem:** Empty values cause argument shift.

**Solution:** Use `{cluster.gres}` instead.

### ❌ Forgetting memory unit suffix
```bash
# DON'T DO THIS:
--mem {resources.mem_mb}

# DO THIS:
--mem {resources.mem_mb}M
```

### ❌ Not pre-generating metadata
**Problem:** Snakemake can't calculate resources without metadata.

**Solution:** Always run `generate_metadata.py` first (automated in `RUNME_cluster.sh`).

### ❌ Wrapper not executable or wrong path
```bash
# Check:
ls -la submit_wrapper.sh
# Should show: -rwxr-xr-x

# Fix:
chmod +x submit_wrapper.sh
```

---

## Advanced: Adding New Scaled Rules

1. **Add to cluster_config.yaml:**
   ```yaml
   my_new_rule:
       time: 0-04:00:00
       partition: basic
       cpus_per_task: 8
       mem: 32G
       gres:
   ```

2. **In Snakefile:**
   ```python
   rule my_new_rule:
       input: "{dataset}/{track_dir}/output/.meta.json"  # Metadata dependency
       output: "{dataset}/{track_dir}/output/result.txt"
       threads: create_scaled_threads_function("my_new_rule")
       resources:
           mem_mb=create_scaled_memory_function("my_new_rule"),
           time=create_scaled_time_function("my_new_rule"),
           partition=create_partition_function("my_new_rule"),
           gres=create_gres_function("my_new_rule")
       shell: "..."
   ```

---

## Key Takeaways

1. **Dynamic scaling requires pre-computed metadata** that Snakemake can read
2. **Use `{cluster.gres}` not `{resources.gres}`** to avoid argument shift
3. **The wrapper is essential** because SLURM rejects empty `--gres` flags
4. **Always test locally first** with `./RUNME_cluster.sh -c`
5. **Resource functions are called per-job** using wildcards to get metadata

---

## Files Summary

| File | Purpose |
|------|---------|
| `generate_metadata.py` | Pre-compute video metadata (duration, frames) |
| `Snakefile` | Define rules with dynamic resource functions |
| `cluster_config.yaml` | Baseline (maximum) resources per rule |
| `config.yaml` | Pipeline parameters |
| `submit_wrapper.sh` | Conditionally add --gres flag for SLURM |
| `RUNME_cluster.sh` | Main execution script |

---

## References

- Snakemake cluster execution: https://snakemake.readthedocs.io/en/stable/executing/cluster.html
- SLURM sbatch: https://slurm.schedmd.com/sbatch.html
- GRES (Generic Resources): https://slurm.schedmd.com/gres.html

---

**Last Updated:** October 2025  
**Pipeline:** C. elegans behavior analysis with dynamic resource scaling
