# Snakemake Pipeline with Dynamic Resource Scaling

Quick start guide for running the C. elegans behavior analysis pipeline with automatic resource allocation.

## Quick Start

```bash
# Run on cluster (default)
./RUNME_cluster.sh

# Run locally (for testing)
./RUNME_cluster.sh -c
```

## Files Required

Place these files in your working directory:

- `RUNME_cluster.sh` - Main execution script
- `submit_wrapper.sh` - SLURM submission helper
- `generate_metadata.py` - Video metadata extraction
- `Snakefile` - Pipeline rules
- `cluster_config.yaml` - Resource configurations
- `config.yaml` - Pipeline parameters

## What Happens When You Run

**Step 1: Metadata Generation**
- Scans all `*/*/track.tif` files
- Extracts duration and frame count
- Creates `.meta.json` files for resource scaling
- Shows summary of videos found

**Step 2: Workflow Unlock**
- Clears any previous locks from failed runs

**Step 3: Pipeline Execution**
- Submits jobs to SLURM with scaled resources
- Short videos → fewer resources
- Long videos → more resources

## Command Line Options

### `-c` flag: Run locally

```bash
./RUNME_cluster.sh -c
```

**Use when:**
- Testing the pipeline on small datasets
- Debugging rule logic
- Cluster is unavailable

**What it does:**
- Runs jobs on the current machine
- Uses local cores instead of SLURM
- No job submission to cluster queue

### Configuration Variables

Edit these in `RUNME_cluster.sh`:

```bash
MAX_JOBS=10  # Maximum parallel jobs on cluster
```

**What MAX_JOBS controls:**
- How many jobs run simultaneously
- Higher = faster (if resources available)
- Lower = less cluster load

**Recommendations:**
- Small datasets (<20 videos): `MAX_JOBS=10`
- Large datasets (>50 videos): `MAX_JOBS=20-30`
- Shared cluster: `MAX_JOBS=5-10` (be nice to others!)

## Snakemake Flags Explained

The script uses these Snakemake options:

### `--configfile config.yaml`
Specifies pipeline parameters (fps, paths, thresholds)

### `--cluster "./submit_wrapper.sh ..."`
Defines how to submit each job to SLURM

### `--cluster-config cluster_config.yaml`
Provides baseline resources for each rule

### `--latency-wait 500`
Waits 500 seconds for output files to appear (network file systems are slow)

### `--jobs $JOBS`
Maximum number of jobs to run in parallel

### `--keep-going`
Continues pipeline even if some jobs fail

### `--rerun-incomplete`
Re-runs jobs that didn't complete successfully

### `--cores $JOBS` (local mode only)
Uses this many CPU cores when running locally

## Resource Scaling

### How It Works

**Baseline:** 30-minute video
- CPUs: 24
- Memory: 64GB
- Time: 8 hours

**3-minute video (10% of baseline):**
- CPUs: 2 (scaled down)
- Memory: 6GB (scaled down)
- Time: 48 minutes (scaled down)

**Rules without scaling:**
- `sam2_segment` - Always uses full resources (GPU-intensive)

### Viewing Scaled Resources

Before running, check `generate_metadata.py` output:

```
Example scaled resources for SHORTEST video:
  • CPUs:   24 → 2
  • Memory: 64G → 6G
  • Time:   0-08:00:00 → ~1 hour(s)
```

## Monitoring Jobs

### Check cluster queue
```bash
squeue -u $USER
```

### View job logs
```bash
# List recent logs
ls -ltr log/

# View specific rule
tail -f log/log_tiff2avi_*.out

# Check for errors
grep -i error log/log_*.out
```

### Snakemake log
```bash
cat .snakemake/log/*.snakemake.log
```

## Common Issues

### "submit_wrapper.sh not found"
```bash
# Fix: Ensure wrapper is in the same directory
ls -la submit_wrapper.sh
chmod +x submit_wrapper.sh
```

### "Metadata generation failed"
```bash
# Fix: Install tiffinfo
sudo apt-get install libtiff-tools  # Ubuntu/Debian
brew install libtiff                 # macOS
```

### Jobs stuck in queue
```bash
# Check cluster availability
sinfo

# Check your job priority
squeue -u $USER --start

# Reduce MAX_JOBS if cluster is busy
```

### Pipeline runs but no output
```bash
# Check if jobs are actually completing
squeue -u $USER  # Should show COMPLETED

# Check log files for errors
grep -i "error\|fail" log/log_*.out

# Increase latency-wait if network is slow
# Edit RUNME_cluster.sh: --latency-wait 1000
```

## Advanced Usage

### Dry run (see what will execute)
```bash
snakemake --configfile config.yaml --dryrun
```

### Force re-run specific rule
```bash
snakemake --configfile config.yaml --forcerun tiff2avi --dryrun
```

### Clean up and restart
```bash
# Remove all output files
snakemake --configfile config.yaml --delete-all-output

# Unlock if stuck
snakemake --configfile config.yaml --unlock

# Start fresh
./RUNME_cluster.sh
```

### Run specific dataset
```bash
snakemake --configfile config.yaml \
  2024-07-29_15-16-11_test_cropper/2024-07-29_15-16-11_test_cropper_track_1/output/chemotaxis_analysis.done
```

## Tips & Best Practices

### Before running production data:
1. **Test locally first:** `./RUNME_cluster.sh -c` on 1-2 videos
2. **Check metadata:** Review `generate_metadata.py` output
3. **Verify resources:** Ensure scaled resources make sense
4. **Start small:** Run on subset before full dataset

### During execution:
1. **Monitor queue:** `watch squeue -u $USER`
2. **Check logs:** Look for errors early
3. **Resource usage:** Use `seff <jobid>` to see if jobs use allocated resources

### After completion:
1. **Verify outputs:** Check that all expected files exist
2. **Review logs:** Look for warnings or unusual behavior
3. **Resource efficiency:** Did jobs use what they were allocated?

## File Structure

Expected directory organization:

```
.
├── RUNME_cluster.sh
├── submit_wrapper.sh
├── generate_metadata.py
├── Snakefile
├── cluster_config.yaml
├── config.yaml
├── dataset_1/
│   ├── dataset_1_track_0/
│   │   ├── track.tif
│   │   ├── track.txt
│   │   └── output/
│   │       ├── .meta.json (generated)
│   │       ├── track.avi
│   │       └── ...
│   └── dataset_1_track_1/
│       └── ...
└── dataset_2/
    └── ...
```

## Getting Help

### Pipeline fails?
1. Check `.snakemake/log/` for Snakemake errors
2. Check `log/log_*.out` for job errors
3. Re-run with `--dryrun` to see planned execution

### Resource issues?
1. Review `cluster_config.yaml` for baseline resources
2. Check scaling in `Snakefile` functions
3. Adjust `MAX_CROP_SEC` in Snakefile if needed

### Cluster issues?
1. Check SLURM status: `sinfo`
2. Review job details: `scontrol show job <jobid>`
3. Check account limits: `sacctmgr show user $USER`

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./RUNME_cluster.sh` | Run pipeline on cluster |
| `./RUNME_cluster.sh -c` | Run pipeline locally |
| `squeue -u $USER` | Check your jobs |
| `scancel <jobid>` | Cancel a job |
| `tail -f log/log_*.out` | Watch job output |
| `snakemake --unlock` | Unlock stuck workflow |
| `snakemake --dryrun` | Preview execution |

---

**For detailed technical documentation, see `README_DYNAMIC_RESOURCES.md`**
