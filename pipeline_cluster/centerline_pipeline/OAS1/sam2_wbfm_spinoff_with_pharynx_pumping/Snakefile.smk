import os
import glob
from ruamel.yaml import YAML

# Find all datasets matching the pattern data/w*/
# This matches folders like: data/worm1/, data/worm2/, data/w1/, etc.
DATASETS = glob.glob("data/w*/")

output_folder_name = 'output/'

# Create a unique output folder for each dataset
for dataset in DATASETS:
    output_folder = os.path.join(dataset, output_folder_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

# Prepend '/output' to each dataset path to ensure processed data goes into the output folder
DATASETS_OUTPUT = glob.glob("data/w*/" + output_folder_name)

print(f"Found {len(DATASETS)} datasets to process:")
print(DATASETS)

configfile: "config.yaml"

# Helper function to load dataset-specific config
def load_dataset_config(datasets_output_path):
    """Load the worm_config.yaml for a specific dataset"""
    # datasets_output_path is like "data/worm2/output/"
    # We need to go to "data/worm2/worm_config.yaml"
    dataset_dir = os.path.dirname(datasets_output_path.rstrip('/'))
    config_path = os.path.join(dataset_dir, "worm_config.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return YAML().load(f)
    return {}

# Helper function for cleanup
def _cleanup_helper(output_path):
    """Uses the snakemake defined temporary function to clean up intermediate files, based on a flag"""
    if config.get('delete_intermediate_files', False):
        return temporary(output_path)
    else:
        return output_path

rule targets:
    input:
        chemotaxis_done = expand("{datasets_output}chemotaxis_analysis.done", datasets_output=DATASETS_OUTPUT),
        worm_movie = expand("{datasets_output}worm_movie.avi", datasets_output=DATASETS_OUTPUT),
        chemotaxis_overview = expand("{datasets_output}chemotaxis_overview.png", datasets_output=DATASETS_OUTPUT),
        principal_components = expand("{datasets_output}principal_components.csv", datasets_output=DATASETS_OUTPUT),
        output_skel_X = expand("{datasets_output}skeleton_skeleton_X_coords.csv", datasets_output=DATASETS_OUTPUT),
        output_skel_Y = expand("{datasets_output}skeleton_skeleton_Y_coords.csv", datasets_output=DATASETS_OUTPUT),
        output_spline_X = expand("{datasets_output}skeleton_spline_X_coords.csv", datasets_output=DATASETS_OUTPUT),
        output_spline_Y = expand("{datasets_output}skeleton_spline_Y_coords.csv", datasets_output=DATASETS_OUTPUT),
        corrected_head = expand("{datasets_output}skeleton_corrected_head_coords.csv", datasets_output=DATASETS_OUTPUT),
        corrected_tail = expand("{datasets_output}skeleton_corrected_tail_coords.csv", datasets_output=DATASETS_OUTPUT),
        cropped_pharynx = expand("{datasets_output}cropped_pharynx_video.avi", datasets_output=DATASETS_OUTPUT),

#
# Preprocessing rules
#

rule subtract_background:
    input:
        ndtiff_subfolder = lambda w: (lambda p: os.path.join(p, next(d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d)) and 'ch0' in d.lower())))(os.path.dirname(w.datasets_output.rstrip('/'))),
        background_img = lambda w: os.path.join(os.path.dirname(os.path.dirname(w.datasets_output.rstrip('/'))), "background", "AVG_2023-12-14_14-37_background_Ch0_MMStack.ome.tif")
    params:
        do_inverse = config["do_inverse"]
    output:
        background_subtracted_img = _cleanup_helper("{datasets_output}raw_stack_AVG_background_subtracted.btf")
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "stack_subtract_background",
            '-i', str(input.ndtiff_subfolder),
            '-o', str(output.background_subtracted_img),
            '-bg', str(input.background_img),
            '-invert', str(params.do_inverse),
        ])

rule normalize_img:
    input:
        input_img = "{datasets_output}raw_stack_AVG_background_subtracted.btf"
    params:
        alpha = config["alpha"],
        beta = config["beta"]
    output:
        normalised_img = _cleanup_helper("{datasets_output}raw_stack_AVG_background_subtracted_normalised.btf")
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "stack_normalise",
            '-i', str(input.input_img),
            '-o', str(output.normalised_img),
            '-a', str(params.alpha),
            '-b', str(params.beta),
        ])

rule worm_unet:
    input:
        input_img = "{datasets_output}raw_stack_AVG_background_subtracted_normalised.btf"
    params:
        weights_path = config["main_unet_model"],
    output:
        worm_unet_prediction = _cleanup_helper("{datasets_output}raw_stack_AVG_background_subtracted_normalised_worm_segmented.btf")
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "unet_segmentation_stack",
            '-i', str(input.input_img),
            '-o', str(output.worm_unet_prediction),
            '-w', str(params.weights_path),
        ])

rule binarize:
    input:
        input_img = "{datasets_output}raw_stack_AVG_background_subtracted_normalised_worm_segmented.btf"
    params:
        threshold = config["threshold"],
        max_value = config["max_value"]
    output:
        binary_img = _cleanup_helper("{datasets_output}raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask.btf")
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "stack_make_binary",
            '-i', str(input.input_img),
            '-o', str(output.binary_img),
            '-th', str(params.threshold),
            '-max_val', str(params.max_value),
        ])

#
# Video and tracking rules
#


rule tiff2avi:
    input:
        input_img = lambda w: (lambda p: os.path.join(p, next(d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d)) and 'ch0' in d.lower())))(os.path.dirname(w.datasets_output.rstrip('/')))
    params:
        fourcc = config["fourcc"],
        fps = config["fps"]
    output:
        avi = _cleanup_helper("{datasets_output}raw_stack.avi")
    run:

        from imutils.src import imutils_parser_main
        imutils_parser_main.main([
            "tiff2avi",
            '-i', str(input.input_img),
            '-o', str(output.avi),
            '-fourcc', str(params.fourcc),
            '-fps', str(params.fps),
        ])

rule dlc_analyze_videos:
    input:
        input_avi = "{datasets_output}raw_stack.avi"
    params:
        dlc_model_configfile_path = config["head_tail_dlc_project"],
        dlc_conda_env = config["dlc_conda_env_name_only_dlc"]
    output:
        hdf5_file = "{datasets_output}raw_stack_dlc.h5",
        csv_file = "{datasets_output}raw_stack_dlc.csv"
    shell:
        """
        # Fix for xml_catalog_files_libxml2 variable
        if [ -z "${{xml_catalog_files_libxml2:-}}" ]; then
            export xml_catalog_files_libxml2=""
        fi 
        
        source /lisc/app/conda/miniforge3/bin/activate {params.dlc_conda_env}
        module load cuda-toolkit/12.9.0
        
        # Run DLC and rename output files to expected names
        python -c "import deeplabcut, os; \
        output_dir = os.path.dirname('{output.hdf5_file}'); \
        fname = deeplabcut.analyze_videos('{params.dlc_model_configfile_path}', '{input.input_avi}', videotype='avi', gputouse=${{CUDA_VISIBLE_DEVICES:-0}}, save_as_csv=True); \
        print('Produced raw files with name: ' + fname); \
        os.rename(output_dir + '/raw_stack' + fname + '.h5', '{output.hdf5_file}'); \
        os.rename(output_dir + '/raw_stack' + fname + '.csv', '{output.csv_file}')"
        """

#
# SAM2 Segmentation (updated version)
#

rule sam2_segment:
    input:
        ndtiff_subfolder = lambda w: (lambda p: os.path.join(p, next(d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d)) and 'ch0' in d.lower())))(os.path.dirname(w.datasets_output.rstrip('/'))), 
        dlc_csv = "{datasets_output}raw_stack_dlc.csv"
    output:
        output_file = _cleanup_helper("{datasets_output}raw_stack_mask.btf")
    params:
        column_names = ["pharynx"],
        model_path = config["sam2_model"],
        sam2_conda_env_name = config["sam2_conda_env_name"],
        batch_size = 300
    shell:
        """
        # Fix for xml_catalog_files_libxml2 variable
        if [ -z "${{xml_catalog_files_libxml2:-}}" ]; then
            export xml_catalog_files_libxml2=""
        fi

        # Enable CuDNN backend for faster attention
        export TORCH_CUDNN_SDPA_ENABLED=1

        module load cuda-toolkit/12.9.0

        # Activate the environment
        source /lisc/app/conda/miniforge3/bin/activate {params.sam2_conda_env_name}

        # Run the script directly without temp directory overhead
        python -c "from SAM2_snakemake_scripts.sam2_video_processing_miscroscope_data_loader import main; \
        main(['-tiff_path', '{input.ndtiff_subfolder}', \
        '-output_file_path', '{output.output_file}', \
        '-DLC_csv_file_path', '{input.dlc_csv}', \
        '-column_names', '{params.column_names}', \
        '-SAM2_path', '{params.model_path}', \
        '--batch_size', '{params.batch_size}', \
        '--device', '${{CUDA_VISIBLE_DEVICES:-0}}'])"
        """

rule coil_unet:
    input:
        binary_input_img = "{datasets_output}raw_stack_mask.btf",
        raw_input_img = "{datasets_output}raw_stack_AVG_background_subtracted_normalised.btf"
    params:
        weights_path = config["coiled_shape_unet_model"],
        env = "/lisc/scratch/neurobiology/zimmer/.conda/envs/wbfm"
    output:
        coil_unet_prediction = _cleanup_helper(
            "{datasets_output}raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask_coil_segmented.btf"
        )
    shell:
        """
        source /lisc/app/conda/miniforge3/bin/activate {params.env}
        
        python -c "from imutils.src import imutils_parser_main; \
        imutils_parser_main.main([ \
            'unet_segmentation_contours_with_children', \
            '-bi', '{input.binary_input_img}', \
            '-ri', '{input.raw_input_img}', \
            '-o', '{output.coil_unet_prediction}', \
            '-w', '{params.weights_path}', \
        ])"
        """


rule binarize_coil:
    input:
        input_img = "{datasets_output}raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask_coil_segmented.btf"
    params:
        threshold = config["coil_threshold"],
        max_value = config["coil_new_value"]
    output:
        binary_img = _cleanup_helper("{datasets_output}raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask_coil_segmented_mask.btf")
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "stack_make_binary",
            '-i', str(input.input_img),
            '-o', str(output.binary_img),
            '-th', str(params.threshold),
            '-max_val', str(params.max_value),
        ])

#
# Centerline and skeleton analysis
#

rule create_centerline:
    input:
        input_binary_img = "{datasets_output}raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask_coil_segmented_mask.btf",  # From coil unet
        hdf5_file = "{datasets_output}raw_stack_dlc.h5"
    params:
        csv_output_path = "{datasets_output}",
        number_of_neighbours = "1",
        nose = config['nose'],
        tail = config['tail'],
        num_splines = config['num_splines'],
        fill_with_DLC = "1"
    output:
        output_skel_X = "{datasets_output}skeleton_skeleton_X_coords.csv",
        output_skel_Y = "{datasets_output}skeleton_skeleton_Y_coords.csv",
        output_spline_K = "{datasets_output}skeleton_spline_K.csv",
        output_spline_X = "{datasets_output}skeleton_spline_X_coords.csv",
        output_spline_Y = "{datasets_output}skeleton_spline_Y_coords.csv",
        corrected_head = "{datasets_output}skeleton_corrected_head_coords.csv",
        corrected_tail = "{datasets_output}skeleton_corrected_tail_coords.csv"
    run:
        from centerline_behavior_annotation.centerline.dev import head_and_tail

        head_and_tail.main([
            '-i', str(input.input_binary_img),
            '-h5', str(input.hdf5_file),
            '-o', str(params.csv_output_path),
            '-nose', str(params.nose),
            '-tail', str(params.tail),
            '-num_splines', str(params.num_splines),
            '-n', str(params.number_of_neighbours),
            '-dlc', str(params.fill_with_DLC),
        ])

rule process_skeleton_curvature:
    input:
        skeleton_x = "{datasets_output}skeleton_spline_X_coords.csv",
        skeleton_y = "{datasets_output}skeleton_spline_Y_coords.csv"
    output:
        output_x = "{datasets_output}skeleton_spline_X_coords_equi_dist_segment.csv",
        output_y = "{datasets_output}skeleton_spline_Y_coords_equi_dist_segment.csv",
        output_curvature = "{datasets_output}skeleton_spline_K_equi_dist_segment.csv",
        output_smoothed_curvature = "{datasets_output}skeleton_spline_K__equi_dist_segment_2D_smoothed.csv"
    params:
        spacing = config['relative_spacing'],
        num_sampled_points = config['num_sampled_points'],
        smoothing = config['smoothing'],
        time_sigma = config['time_sigma'],
        spatial_sigma = config['spatial_sigma'],
        max_columns = config['max_columns'],
    run:
        from centerline_behavior_annotation.centerline.dev import centerline_equi_distance_2d_smoothing

        centerline_equi_distance_2d_smoothing.main([
            '--skeleton_x', str(input.skeleton_x),
            '--skeleton_y', str(input.skeleton_y),
            '--relative_spacing', str(params.spacing),
            '--num_sampled_points', str(params.num_sampled_points),
            '--smoothing', str(params.smoothing),
            '--time_sigma', str(params.time_sigma),
            '--spatial_sigma', str(params.spatial_sigma),
            '--max_columns', str(params.max_columns),
            '--output_x', str(output.output_x),
            '--output_y', str(output.output_y),
            '--output_curvature', str(output.output_curvature),
            '--output_smoothed_curvature', str(output.output_smoothed_curvature)
        ])

rule invert_curvature_sign:
    input:
        spline_K = "{datasets_output}skeleton_spline_K__equi_dist_segment_2D_smoothed.csv"
    params:
        ventral = lambda wildcards: load_dataset_config(wildcards.datasets_output)["ventral"]
    output:
        spline_K_signed = "{datasets_output}skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv"
    run:
        from centerline_behavior_annotation.curvature.src import invert_curvature_sign

        invert_curvature_sign.main_benjamin([
            '--spline_K_path', str(input.spline_K),
            '--ventral', str(params.ventral),
            '--output_file_path', str(output.spline_K_signed)
        ])

#
# Behavior annotation
#

rule annotate_behaviour:
    input:
        curvature_file = "{datasets_output}skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv"
    params:
        pca_model_path = config["pca_model"],
        initial_segment = config["initial_segment"],
        final_segment = config["final_segment"],
        window = config["window"]
    output:
        principal_components = "{datasets_output}principal_components.csv",
        behaviour_annotation = "{datasets_output}beh_annotation.csv"
    run:
        from centerline_behavior_annotation.curvature.src import annotate_reversals_snakemake

        annotate_reversals_snakemake.main([
            '-i', str(input.curvature_file),
            '-pca', str(params.pca_model_path),
            '-i_s', str(params.initial_segment),
            '-f_s', str(params.final_segment),
            '-win', str(params.window),
            '-o_pc', str(output.principal_components),
            '-o_bh', str(output.behaviour_annotation),
        ])

rule annotate_turns:
    input:
        spline_K = "{datasets_output}skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv",
        beh_annotation = "{datasets_output}beh_annotation.csv"
    params:
        threshold = config["turn_threshold"],
        initial_segment = config["turn_initial_segment"],
        final_segment = config["turn_final_segment"],
        avg_window = config["turn_avg_window"],
        min_event_length = config.get("turn_min_event_length", 24)
    output:
        turns_annotation = "{datasets_output}turns_annotation.csv"
    run:
        from centerline_behavior_annotation.curvature.src import annotate_turns_reversal_based
        
        annotate_turns_reversal_based.main([
            '-spline', str(input.spline_K),
            '-beh_ann', str(input.beh_annotation),
            '-t', str(params.threshold),
            '-i_s', str(params.initial_segment),
            '-f_s', str(params.final_segment),
            '-avg_window', str(params.avg_window),
            '-min_event_length', str(params.min_event_length),
            '-output', str(output.turns_annotation),
        ])

rule save_signed_speed:
    input:
        raw_speed_file = "{datasets_output}raw_worm_speed.csv",
        behaviour_annotation = "{datasets_output}beh_annotation.csv"
    output:
        signed_speed_file = "{datasets_output}signed_worm_speed.csv"
    run:
        import pandas as pd
        raw_speed_df = pd.read_csv(input.raw_speed_file)
        ethogram_df = pd.read_csv(input.behaviour_annotation)
        signed_speed_df = pd.DataFrame()
        signed_speed_df['Raw Speed Signed (mm/s)'] = raw_speed_df['Raw Speed (mm/s)'] * ethogram_df['0'] * -1
        signed_speed_df.to_csv(output.signed_speed_file)

rule calculate_parameters:
    input:
        curvature_file = "{datasets_output}skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv"
    output:
        speed_file = "{datasets_output}raw_worm_speed.csv"
    params:
        output_path = "{datasets_output}",
        raw_data_dir = lambda wildcards: os.path.dirname(wildcards.datasets_output.rstrip('/'))
    run:
        from centerline_behavior_annotation.behavior_analysis.src import calculate_parameters

        calculate_parameters.main([
            '-i', str(params.output_path),
            '-r', str(params.raw_data_dir),
        ])

rule hilbert_transform_on_kymogram:
    input:
        spline_K = "{datasets_output}skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv"
    params:
        output_path = "{datasets_output}",
        fs = config["sampling_frequency"],
        window = config["hilbert_averaging_window"]
    output:
        hilbert_regenerated_carrier = "{datasets_output}hilbert_regenerated_carrier.csv",
        hilbert_inst_freq = "{datasets_output}hilbert_inst_freq.csv",
        hilbert_inst_phase = "{datasets_output}hilbert_inst_phase.csv",
        hilbert_inst_amplitude = "{datasets_output}hilbert_inst_amplitude.csv"
    run:
        from centerline_behavior_annotation.behavior_analysis.src import hilbert_transform

        hilbert_transform.main([
            '-i', str(params.output_path),
            '-kp', str(input.spline_K),
            '-fs', str(params.fs),
            '-w', str(params.window),
        ])

#
# Pharynx tracking (from old pipeline)
#

rule crop_pharynx_video:
    input:
        csv = "{datasets_output}raw_stack_dlc.csv",
        avi = "{datasets_output}raw_stack.avi"
    output:
        cropped_pharynx = "{datasets_output}cropped_pharynx_video.avi"
    params:
        fps = config["fps"],
        crop_size = config["crop_size_pharynx"]
    run:
        from pharynx_tracking import crop_pharynx_video_script

        crop_pharynx_video_script.main([
            '--video', str(input.avi),
            '--csv', str(input.csv),
            '--output', str(output.cropped_pharynx),
            '--fps', str(params.fps),
            '--crop_size', str(params.crop_size),
        ])

rule pharynx_pump_dlc_analyze_videos:
    input:
        cropped_pharynx = "{datasets_output}cropped_pharynx_video.avi"
    params:
        dlc_model_configfile_path = config["dlc_model_configfile_path_track_pumps"],
        network_string = config["network_string_pharynx"],
        dlc_conda_env = config["dlc_conda_env_name_only_dlc"]
    output:
        hdf5_file_pharynx = "{datasets_output}cropped_pharynx_video" + config["network_string_pharynx"] + ".h5",
        csv_file_pharynx = "{datasets_output}cropped_pharynx_video" + config["network_string_pharynx"] + ".csv"
    shell:
        """
        # Fix for xml_catalog_files_libxml2 variable
        if [ -z "${{xml_catalog_files_libxml2:-}}" ]; then
            export xml_catalog_files_libxml2=""
        fi 
        
        source /lisc/app/conda/miniforge3/bin/activate {params.dlc_conda_env}
        module load cuda-toolkit/12.9.0
        
        # Run DLC and rename output files to expected names
        python -c "import deeplabcut, os; \
        output_dir = os.path.dirname('{output.hdf5_file_pharynx}'); \
        fname = deeplabcut.analyze_videos('{params.dlc_model_configfile_path}', '{input.cropped_pharynx}', videotype='avi', gputouse=${{CUDA_VISIBLE_DEVICES:-0}}, save_as_csv=True); \
        print('Produced raw files with name: ' + fname); \
        os.rename(output_dir + '/cropped_pharynx_video' + fname + '.h5', '{output.hdf5_file_pharynx}'); \
        os.rename(output_dir + '/cropped_pharynx_video' + fname + '.csv', '{output.csv_file_pharynx}')"
        """

#
# Chemotaxis analysis (updated version with worm_config.yaml loading)
#

rule chemotaxis_analysis:
    input:
        reversal_annotation = "{datasets_output}beh_annotation.csv",
        turn_annotation = "{datasets_output}turns_annotation.csv",
        spline_K = "{datasets_output}skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv",
        skeleton_spline_X_coords = "{datasets_output}skeleton_spline_X_coords_equi_dist_segment.csv",
        skeleton_spline_Y_coords = "{datasets_output}skeleton_spline_Y_coords_equi_dist_segment.csv",
        DLC_hdf5_file = "{datasets_output}raw_stack_dlc.h5",
        pharynx_pump_csv = "{datasets_output}cropped_pharynx_video" + config["network_string_pharynx"] + ".csv"
    params:
        # Paths
        worm_pos = lambda wildcards: os.path.join(os.path.dirname(wildcards.datasets_output.rstrip('/')), "worm_pos.txt"),
        
        # Global config parameters
        fps = config["fps"],
        dlc_nose_label = config["nose"],
        dlc_tail_label = config["tail"],
        bootstrap_iterations = 100,
        bootstrap_seed = 42,
        dC_lookback_frames = 1,
        
        # Dataset-specific parameters from worm_config.yaml (NO DEFAULTS - will fail if missing)
        factor_px_to_mm = lambda wildcards: load_dataset_config(wildcards.datasets_output)["factor_px_to_mm"],
        video_resolution_x = lambda wildcards: load_dataset_config(wildcards.datasets_output)["video_resolution_x"],
        video_resolution_y = lambda wildcards: load_dataset_config(wildcards.datasets_output)["video_resolution_y"],
        conc_gradient_array = lambda wildcards: load_dataset_config(wildcards.datasets_output)["conc_gradient_array"],
        distance_array = lambda wildcards: load_dataset_config(wildcards.datasets_output)["distance_array"],
        top_left_pos = lambda wildcards: load_dataset_config(wildcards.datasets_output)["top_left_pos"],
        odor_pos = lambda wildcards: load_dataset_config(wildcards.datasets_output)["odor_pos"],
        diffusion_time_offset = lambda wildcards: load_dataset_config(wildcards.datasets_output)["diffusion_time_offset"],
        video_source = lambda wildcards: load_dataset_config(wildcards.datasets_output)["video_source"]
    output:
        chemotaxis_visualisation = "{datasets_output}chemotaxis_analysis.pdf",
        chemotaxis_overview = "{datasets_output}chemotaxis_overview.png",
        worm_movie = "{datasets_output}worm_movie.avi",
        chemotaxis_params = "{datasets_output}chemotaxis_params.csv",
        chemotaxis_h5 = "{datasets_output}chemotaxis_analysis_complete.h5",
        done = touch("{datasets_output}chemotaxis_analysis.done")
    shell:
        """
        unset DCGM_ARGS
        
        if [ -z "${{xml_catalog_files_libxml2:-}}" ]; then
            export xml_catalog_files_libxml2=""
        fi
        
        eval "$(/lisc/app/conda/miniforge3/bin/conda shell.bash hook)"
        conda activate /lisc/scratch/neurobiology/zimmer/.conda/envs/autoscope_behaviour_shared
        
        python -c "from chemotaxis_analysis_high_res import initialize_load_files_high_res_universal_bootstrapping; \
        initialize_load_files_high_res_universal_bootstrapping.main([ \
            '--reversal_annotation', '{input.reversal_annotation}', \
            '--skeleton_spline', '{input.spline_K}', \
            '--worm_pos', '{params.worm_pos}', \
            '--skeleton_spline_X_coords', '{input.skeleton_spline_X_coords}', \
            '--skeleton_spline_Y_coords', '{input.skeleton_spline_Y_coords}', \
            '--factor_px_to_mm', '{params.factor_px_to_mm}', \
            '--video_resolution_x', '{params.video_resolution_x}', \
            '--video_resolution_y', '{params.video_resolution_y}', \
            '--fps', '{params.fps}', \
            '--conc_gradient_array', '{params.conc_gradient_array}', \
            '--distance_array', '{params.distance_array}', \
            '--turn_annotation', '{input.turn_annotation}', \
            '--top_left_pos', '{params.top_left_pos}', \
            '--odor_pos', '{params.odor_pos}', \
            '--diffusion_time_offset', '{params.diffusion_time_offset}', \
            '--img_type', '{params.video_source}', \
            '--DLC_coords', '{input.DLC_hdf5_file}', \
            '--DLC_nose', '{params.dlc_nose_label}', \
            '--DLC_tail', '{params.dlc_tail_label}', \
            '--pharynx_pump_csv', '{input.pharynx_pump_csv}', \
            '--bootstrap_iterations', '{params.bootstrap_iterations}', \
            '--bootstrap_seed', '{params.bootstrap_seed}', \
            '--dC_lookback_frames', '{params.dC_lookback_frames}' \
        ])"
        """
