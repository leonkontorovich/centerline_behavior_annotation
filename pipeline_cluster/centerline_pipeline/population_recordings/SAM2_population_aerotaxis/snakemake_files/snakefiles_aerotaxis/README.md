# Aerotaxis pipeline — single-recording working folder

This is the Snakemake project for **one recording**. A copy of these files lands
in every `<recording>_new/` folder when you run the dataset setup step, and each
folder is processed independently.

**For the full start-to-finish protocol** (SWC → rename → setup → bubble filter →
run → aggregate → analyse), see the canonical guide at the repository root:

> **`README_AEROTAXIS_PIPELINE.md`**

## Run just this recording

```bash
./RUNME_cluster.sh            # submit to SLURM (default)
./RUNME_cluster.sh -c         # run locally (testing / debugging)
./RUNME_cluster.sh --jobs 20  # cap parallel jobs
```

`RUNME_cluster.sh` (1) runs `generate_metadata.py` to size each job to its video
length, (2) unlocks the workflow, then (3) runs Snakemake. Per-job CPU/memory/
walltime scale with recording duration; GPU rules (`sam2_segment`,
`dlc_analyze_videos`) use fixed resources. The full pipeline that runs every
recording at once is `bash_scripts/run_aerotaxis_population_pipeline.sh` — see
the root guide.

To launch **all** recordings in a dataset at once, use
`run_aerotaxis_population_pipeline.sh` from the dataset root (see the root guide,
step 6).

## The gas protocol

Behaviour is aligned to the global gas protocol in `config.yaml` under
`aerotaxis:`. The setup step populates it from your Alicat `.txt` gas script;
edit it by hand only for non-standard paradigms. `fps` and `factor_px_to_mm`
there are fallbacks — the real values come per recording from SWC
`parameters.yaml`.

## Files in this folder

| File | Purpose |
|------|---------|
| `Snakefile` | pipeline rules + per-recording resource scaling |
| `config.yaml` | pipeline parameters + the `aerotaxis:` gas protocol |
| `cluster_config.yaml` | baseline SLURM resources per rule |
| `RUNME_cluster.sh` | run this recording (metadata → unlock → Snakemake) |
| `submit_wrapper.sh` | SLURM submission helper (conditional `--gres`) |
| `generate_metadata.py` | pre-compute per-video duration for resource scaling |
| `extract_temporal_features.py` | build one crop's `temporal_features.csv` |

For the resource-scaling internals and the SLURM GRES wrapper, see
`README_DYNAMIC_RESOURCES.md` in the pipeline root
(`population_recordings/SAM2_population_aerotaxis/`).
