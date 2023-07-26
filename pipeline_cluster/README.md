# Autoscope Pipeline
Pipeline to extract behavioural parameters from Autoscope recordings.

On 25th of July 2023 Ulises gave a presentation about the pipeline, the slides are not self-explanatory but they can be checked under:
```bash
/project/neurobiology/zimmer/lab_stuff/Lab Meetings/ulises/20230724_beh_analysis_pipeline_tutorial_UR.key
```

### Environment

Important: Works with opencv version 3.4.2

(If you need help with this, check our protocols in https://github.com/Zimmer-lab/protocols/tree/master/computational/zimmer_lab_code_pipeline)

* Option 1:
Install the environment with the provided oa_behavior_analysis_pipeline.yaml file which contains the necessary packages to run the pipeline.

Private packages need to be installed manually. To do that clone them and install them with pip. For example:
```bash
pip install /scratch/neurobiology/zimmer/ulises/code/imutils
pip install /scratch/neurobiology/zimmer/ulises/code/centerline
pip install /scratch/neurobiology/zimmer/ulises/code/curvature
pip install /scratch/neurobiology/zimmer/ulises/code/behavior_analysis
```

* Option 2:
You can also use the shared environmen (but you should know if it is maintained).
```bash
conda activate /scratch/neurobiology/zimmer/.conda/envs/oa_behavior_analysis_pipeline
```





