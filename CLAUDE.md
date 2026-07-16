# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Python package for analyzing worm behavior through centerline extraction and annotation. The repository combines 5 previously separate repositories focused on worm behavioral analysis using computer vision and machine learning techniques.

## Environment Setup

### Conda Environment
Create the environment using the provided configuration:
```bash
conda env create -f conda/centerline_behavior_annotations.yaml
conda activate centerline_behavior_annotations
```

### Installation
Install the package in development mode:
```bash
pip install -e .
```

## Key Development Commands

### Running Snakemake Workflows
The population behavior pipeline is specialized for **aerotaxis / O₂-sensing**
assays and lives in
`pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/`.
The full start-to-finish protocol is documented in `README_AEROTAXIS_PIPELINE.md`
(repo root). In brief:

**Single recording** (from inside a `<recording>_new/` folder):
```bash
./RUNME_cluster.sh        # cluster (default)
./RUNME_cluster.sh -c     # local, for testing
```

**Whole dataset** (from the dataset root):
```bash
bash pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/run_aerotaxis_population_pipeline.sh --folders 4 --jobs 50
```

### Pipeline Workflow Management
- Snakemake automatically manages dependencies and parallelization
- Each workflow detects available track directories and adjusts job count accordingly (max 4 parallel jobs)
- Use `snakemake --unlock --configfile config.yaml` to unlock workflows after failed runs

## Architecture Overview

### Core Package Structure (`centerline_behavior_annotation/`)

**centerline/** - Centerline extraction and processing
- Binary image creation and skeleton extraction from worm images
- Coordinate conversion and smoothing algorithms
- Head/tail detection and annotation

**curvature/** - Curvature analysis and behavior classification
- PCA-based eigenworm analysis for behavior annotation
- Reversal, turn, and coil detection algorithms  
- Principal component models for standardizing behavioral states

**behavior_analysis/** - High-level behavioral analysis
- Manual annotation conversion to timeseries format
- Speed calculation and ethogram generation
- Comparative analysis tools

**dlc_utils/** - DeepLabCut integration
- DLC model training and evaluation scripts
- Video labeling and analysis workflows
- GPU cluster processing tools

**quiescence_analysis/** - Quiescence detection
- Pixel difference analysis for movement detection
- Specialized tools for identifying periods of inactivity

### Pipeline Structure (`pipeline_cluster/`)

**OAS1/** - Primary segmentation pipeline
- OpenCV-based segmentation
- SAM2-based segmentation  
- U-Net based segmentation options

**OAS2/** - Secondary processing pipeline
- Background subtraction and normalization
- Post-processing workflows

**population_recordings/** - Population-level analysis
- `SAM2_population_aerotaxis/` — aerotaxis / O₂-sensing behavior analysis (temporal, gas-shift-locked)
- Population statistics and modeling
- Batch processing of multiple recordings

## Configuration Management

### Key Configuration Files
- `config.yaml` - Main pipeline parameters (video processing, model paths, detection thresholds)
- `cluster_config.yaml` - SLURM cluster job specifications
- Conda environment files in `conda/` directory

### Important Parameters
- **Video processing**: fps, pixel-to-mm conversion factors
- **Model paths**: DLC models, PCA models for behavior classification
- **Detection thresholds**: worm area, length, roundness criteria
- **Segmentation**: number of spline points, smoothing parameters

## Data Flow

1. **Video Input** → **OAS1 Segmentation** → Binary masks
2. **Binary masks** → **Centerline extraction** → Skeleton coordinates  
3. **Skeleton data** → **Curvature analysis** → Principal components
4. **PC data** → **Behavior annotation** → Classified behaviors (forward, reversal, coil, turn)
5. **Behavioral data** → **Population analysis** → Statistics and visualizations

## Development Notes

- The repository uses SLURM for cluster computing with job arrays for parallel processing
- Snakemake workflows automatically handle file dependencies and incremental updates
- PCA models are pre-trained on population data for consistent behavior classification
- DLC models require GPU resources for training and inference
- All processing maintains pixel-to-mm calibration for quantitative analysis