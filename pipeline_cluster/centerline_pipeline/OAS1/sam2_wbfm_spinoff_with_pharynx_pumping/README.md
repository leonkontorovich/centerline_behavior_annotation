# Autoscope Pipeline – Folder Structure

This repository expects a simple and clean directory layout.  
Run the pipeline from the **project root** (the folder containing the `Snakefile`).

## Folder Layout

```
project_root/
├── Snakefile
├── config.yaml
├── cluster_config.yaml
├── RUNME_cluster.sh
├── log/                     # Snakemake + cluster logs
└── data/
    ├── background/
    │   └── AVG_2023-12-14_14-37_background_Ch0_MMStack.ome.tif
    └── worm2/               # One folder per dataset (worm1, worm2, ...)
        ├── 2023-12-14_..._worm1_Ch0/   # Raw microscope data (OME/ndtiff)
        ├── output/                      # Pipeline results (created automatically)
        └── worm_config.yaml             # Dataset-specific config
```

## What Goes Where

- **Raw imaging data** → `data/wormX/your_raw_data_folder/`
- **Background OME-TIFF** → `data/background/`
- **Per-dataset config** → `data/wormX/worm_config.yaml`
- **Pipeline outputs** → automatically placed into `data/wormX/output/`

## Running the Pipeline

Local or cluster run:

```bash
bash RUNME_cluster.sh
```

Local only:

```bash
bash RUNME_cluster.sh -c
```

The pipeline will detect the directory structure automatically.
