# Autoscope Pipeline
Pipeline to extract behavioural parameters from Open Autoscope (OA) recordings.



## Tutorial
On 25th of July 2023 Ulises gave a presentation about the pipeline, the slides are not self-explanatory but they can be checked under:
```bash
/project/neurobiology/zimmer/lab_stuff/Lab Meetings/ulises/20230724_beh_analysis_pipeline_tutorial_UR.key
```

## Introduction 
To run this package you need to be to some extent familiar with:
1. Python code
2. Snakemake Pipelines
3. Bash scripting
4. Slurm and cluster job management
5. Tmux

If you are not, familiarize yourself with it before using this.

## Motivation
The motivation of this repository was to run the code written to extract behavioural features from OA recordings, in a pipeline.
It assumes the following file structure:



 * cluster_config.yaml
 * config.yaml
 * data
   * background
     * AVG_background.tif
   * worm1
     * 2022-11-27_12-31_w1_Ch0
       * 2022-11-27_12-31_w1_Ch0_MMStack_1.ome.tif
       * 2022-11-27_12-31_w1_Ch0_MMStack_metadata.txt
       * 2022-11-27_12-31_w1_Ch0_MMStack.ome.tif
       * comments.txt
       * DisplaySettings.json
     * 2022-11-27_12-31_w1-TablePosRecord.txt
   * worm2
   * 2022-11-27_13-19_w2_Ch0
     * 2022-11-27_13-19_w2_Ch0_MMStack_1.ome.tif
     * 2022-11-27_13-19_w2_Ch0_MMStack_metadata.txt
     * 2022-11-27_13-19_w2_Ch0_MMStack.ome.tif
     * comments.txt
     * DisplaySettings.json
   * 2022-11-27_13-19_w2-TablePosRecord.txt
 * log
 * RUNME_cluster.sh




### Environment
(If you need help with this, check our protocols in https://github.com/Zimmer-lab/protocols/tree/master/computational/zimmer_lab_code_pipeline)

Important: Works with opencv version 3.4.2

####  Option 1:
Install the environment with the provided oa_behavior_analysis_pipeline.yaml file which contains the necessary packages to run the pipeline.

Private packages need to be installed manually. To do that clone them and install them with pip. For example:
```commandline
pip install /scratch/neurobiology/zimmer/ulises/code/imutils
pip install /scratch/neurobiology/zimmer/ulises/code/centerline
pip install /scratch/neurobiology/zimmer/ulises/code/curvature
pip install /scratch/neurobiology/zimmer/ulises/code/behavior_analysis
```

Snakemake needs to be installed via mamba (See https://github.com/Zimmer-lab/autoscope_pipeline/issues/5):
```commandline
 mamba install -c conda-forge -c bioconda snakemake
```
#### Option 2:
You can also use the shared environment (but you should know if it is maintained).
```commandline
conda activate /scratch/neurobiology/zimmer/.conda/envs/oa_behavior_analysis_pipeline
```

### Sister projects
There is another snakemake pipeline sister to this which was created for whole brain freely moving recordings. You might want to check it.

See:

[https://github.com/Zimmer-lab/autoscope_pipeline](https://github.com/Zimmer-lab/wbfm_behavior_analysis_pipeline)https://github.com/Zimmer-lab/wbfm_behavior_analysis_pipeline





