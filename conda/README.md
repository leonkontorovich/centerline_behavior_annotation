# Conda environments

This folder holds the environment specs for the repo. There are two very
different tiers, and the reproducibility story differs for each.

## 1. Analysis / orchestration (fully reproducible, off-cluster)

`aerotaxis_analysis.yaml` — the environment for everything that is **not** GPU
inference: the Snakemake controller, the temporal-feature extractor,
`create_results_dict_server.py`, the population analysis (`aerotaxis_analysis.py`),
the `tests/` suite, and the notebook.

```bash
conda env create -f conda/aerotaxis_analysis.yaml
conda activate aerotaxis_analysis
pytest pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/tests
```

## 2. GPU inference stack (SAM2 + DeepLabCut) — NOT captured here

The heavy stages (`sam2_segment`, `dlc_analyze_videos`) run in **shared cluster
conda envs referenced only by absolute path**, and the SAM2 source is a separate
checkout. None of it is version-controlled in this repo, so a run's
reproducibility currently depends on those cluster envs staying intact. The
references are:

| What | Where it is pinned today |
|---|---|
| SAM2 conda env | `Snakefile` (`sam2_conda_env_name`, ~L303): `/lisc/data/scratch/neurobiology/zimmer/.conda/envs/SAM2_shared` |
| SAM2 source checkout | `Snakefile` (`model_path`, ~L302): `.../schaar/code/github/segment-anything-2` |
| DeepLabCut conda env | `config.yaml` (`dlc_conda_env_path`): `.../envs/DeepLabCut-2.3.11` |
| DLC model config | `config.yaml` (`dlc_model_configfile_path`) |
| CUDA module | `Snakefile` (`module load CUDA/12.9.1`, in the SAM2 + DLC rules) |

**To make these reproducible, freeze them once on the cluster** (they are large,
so we commit the exported specs, not the envs themselves):

```bash
# on the LISC cluster, with each env active in turn:
conda activate SAM2_shared        && conda env export --no-builds > conda/SAM2_shared.exported.yaml
conda activate DeepLabCut-2.3.11  && conda env export --no-builds > conda/DeepLabCut-2.3.11.exported.yaml
# and record the exact SAM2 source commit:
git -C /lisc/data/scratch/neurobiology/zimmer/schaar/code/github/segment-anything-2 rev-parse HEAD \
    > conda/SAM2_source.commit.txt
```

Commit the resulting `*.exported.yaml` + `SAM2_source.commit.txt` so the GPU
stack can be rebuilt from a known state. (Left as a cluster-side step because the
exact solved versions can only be captured where those envs actually live.)

## 3. Legacy environments

`centerline_behavior_annotations.yaml` and `openCV.yaml` are the original Python
3.7 / TensorFlow 2.11 / OpenCV 3.4 environments for the wider package. They are
triple-pinned with exact build strings and are effectively unsolvable on current
channels (Python 3.7 is EOL); kept for historical reference only. Prefer
`aerotaxis_analysis.yaml` for the aerotaxis pipeline work.
