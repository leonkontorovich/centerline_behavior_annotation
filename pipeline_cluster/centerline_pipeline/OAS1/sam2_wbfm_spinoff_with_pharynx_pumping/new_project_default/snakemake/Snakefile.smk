import os
from ruamel.yaml import YAML
import snakemake
from pipeline_cluster.centerline_pipeline.OAS1.sam2_wbfm_spinoff_with_pharynx_pumping.utils.snakefile_helper_functions import *


# --------------------------
# HELPER FUNCTIONS
# --------------------------


def _cleanup_helper(output_path):
    """Uses the snakemake defined temporary function to clean up intermediate files, based on a flag"""
    if config['delete_intermediate_files']:
        return temporary(output_path)
    else:
        return output_path


# --------------------------
# ASSIGN PATHS AND VARIABLES
# --------------------------

# Determine the project folder (the parent of the folder containing the Snakefile)
# NOTE: this is an undocumented feature, and may not work for other versions (this is 7.32)
snakefile_dir = workflow.basedir
project_dir = os.path.abspath(os.path.join(snakefile_dir,".."))

logger.info("Detected project folder: ",project_dir)
project_cfg = os.path.join(project_dir,"project_config.yaml")

if not snakemake.__version__.startswith("7.32"):
    logger.warning(f"Note: this pipeline is only tested on snakemake version 7.32.X, but found {snakemake.__version__}")

# get all paths and configs
try:
    config = load_autoscope_dataset_config(project_cfg)

    # assign relevant directories
    raw_data_dir = config['raw_data_dir']
    raw_data_subfolder = config['raw_data_subfolder']
    output_behavior_dir = config['output_behavior_dir']

    # load background image
    background_img = find_background_file(raw_data_dir)


except FileNotFoundError as e:
    print(f"Error: {e}")
    raise

# --------------------------
# MAIN RULE
# --------------------------

final_targets = [
    os.path.join(output_behavior_dir,"behavioral_summary_figure.pdf"),
    os.path.join(output_behavior_dir,"cropped_pharynx_video.avi"),
]

# chemotaxis rule is optional (statement is nested in the project_config)
if config.get("dataset_params", {}).get("run_chemotaxis", True):
    final_targets.append(f"{output_behavior_dir}/chemotaxis_analysis_complete.h5")


rule run_autoscope_behavior:
    input: final_targets


# --------------------------
# PREPROCESSING RULES
# --------------------------


rule subtract_background:
    input:
        ometiff_subfolder=raw_data_subfolder,
        background_img=background_img
    params:
        do_inverse=config["do_inverse"]
    output:
        background_subtracted_img=_cleanup_helper(f"{output_behavior_dir}/raw_stack_AVG_background_subtracted.btf")
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "stack_subtract_background",
            '-i', str(input.ometiff_subfolder),
            '-o', str(output.background_subtracted_img),
            '-bg', str(input.background_img),
            '-invert', str(params.do_inverse),
        ])

rule normalize_img:
    input:
        input_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted.btf"
    params:
        alpha=config["alpha"],
        beta=config["beta"]
    output:
        normalised_img=_cleanup_helper(f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised.btf")
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
        input_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised.btf"
    params:
        weights_path=config["main_unet_model"],
    output:
        worm_unet_prediction=_cleanup_helper(f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised_worm_segmented.btf")
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "unet_segmentation_stack",
            '-i', str(input.input_img),
            '-o', str(output.worm_unet_prediction),
            '-w', str(params.weights_path),
        ])


# TODO: input is the raw video

rule sam2_segment:
    input:
        ometiff_subfolder=raw_data_subfolder,
        dlc_csv=f"{output_behavior_dir}/raw_stack_dlc.csv"
    output:
        output_file=_cleanup_helper(f"{output_behavior_dir}/raw_stack_mask.btf"),
    params:
        column_names=["pharynx"],
        model_path=config["sam2_model"],
        sam2_conda_env_name=config["sam2_conda_env_name"],
        batch_size=250
    shell:
        """
        # I started getting an error with the xml_catalog_files_libxml2 variable, so check if it is set
        if [ -z "${{xml_catalog_files_libxml2:-}}" ]; then
            export xml_catalog_files_libxml2=""
        fi

        # Enable CuDNN backend for faster attention
        export TORCH_CUDNN_SDPA_ENABLED=1

        module load CUDA/12.9.1

        # Activate the environment and the correct cuda
        source /lisc/opt/sw/software/Conda/Miniforge3/bin/activate {params.sam2_conda_env_name}

        # Run the script directly without temp directory overhead
        python -c "from SAM2_snakemake_scripts.sam2_video_processing_miscroscope_data_loader import main; main(['-tiff_path', '{input.ometiff_subfolder}', '-output_file_path', '{output.output_file}', '-DLC_csv_file_path', '{input.dlc_csv}', '-column_names', '{params.column_names}', '-SAM2_path', '{params.model_path}', '--batch_size', '{params.batch_size}', '--device', '${{CUDA_VISIBLE_DEVICES:-0}}'])"
        """

rule binarize:
    input:
        input_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised_worm_segmented.btf"
    params:
        threshold=config["threshold"],
        max_value=config["max_value"]
    output:
        binary_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask.btf"
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "stack_make_binary",
            '-i', str(input.input_img),
            '-o', str(output.binary_img),
            '-th', str(params.threshold),
            '-max_val', str(params.max_value),
        ])

rule coil_unet:
    input:
        binary_input_img=f"{output_behavior_dir}/raw_stack_mask.btf",# From the SAM2 segmentation
        raw_input_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised.btf"
    # Does not need to match the other segmentation; needs to match the training of the coil unet
    params:
        weights_path=config["coiled_shape_unet_model"]
    output:
        coil_unet_prediction=_cleanup_helper(f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask_coil_segmented.btf")
    shell:
        """
        # I started getting an error with the xml_catalog_files_libxml2 variable, so check if it is set
        if [ -z "${{xml_catalog_files_libxml2:-}}" ]; then
            #echo "Warning: xml_catalog_files_libxml2 is not set, setting it to /lisc/app/conda/miniforge3/etc/xml/catalog"
            export xml_catalog_files_libxml2=""
        fi 

        source /lisc/opt/sw/software/Conda/Miniforge3/bin/activate {params.wbfm_conda_env}
        # Also rename the output file to the expected name
        # We don't actually know the name without querying deeplabcut, so just rename it
        python -c "from imutils.src import imutils_parser_main; imutils_parser_main.main(['unet_segmentation_contours_with_children', '-bi', '{input.binary_input_img}', '-ri', '{input.raw_input_img}', '-o', '{output.coil_unet_prediction}', '-w', '{params.weights_path}']); print('UNet segmentation finished. Output saved to: {output.coil_unet_prediction}')"
        """

rule binarize_coil:
    input:
        input_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask_coil_segmented.btf"
    params:
        threshold=config["coil_threshold"],# 240
        max_value=config["coil_new_value"]  # 255
    output:
        binary_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask_coil_segmented_mask.btf"
    run:
        from imutils.src import imutils_parser_main

        imutils_parser_main.main([
            "stack_make_binary",
            '-i', str(input.input_img),
            '-o', str(output.binary_img),
            '-th', str(params.threshold),
            '-max_val', str(params.max_value),
        ])



rule tiff2avi:
    input:
        input_img=raw_data_subfolder
    params:
        fourcc=config["fourcc"],#"0",
        fps=config["fps"]  # "167"
    output:
        avi=_cleanup_helper(f"{output_behavior_dir}/raw_stack.avi")
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
        # Will save the output in the same folder as the input by default
        input_avi=f"{output_behavior_dir}/raw_stack.avi"
    params:
        dlc_model_configfile_path=config["head_tail_dlc_project"],
        dlc_conda_env=config["dlc_conda_env_name_only_dlc"]
    output:
        hdf5_file=f"{output_behavior_dir}/raw_stack_dlc.h5",
        csv_file=f"{output_behavior_dir}/raw_stack_dlc.csv"
    shell:
        """
        # I started getting an error with the xml_catalog_files_libxml2 variable, so check if it is set
        if [ -z "${{xml_catalog_files_libxml2:-}}" ]; then
            #echo "Warning: xml_catalog_files_libxml2 is not set, setting it to /lisc/app/conda/miniforge3/etc/xml/catalog"
            export xml_catalog_files_libxml2=""
        fi 

        source /lisc/opt/sw/software/Conda/Miniforge3/bin/activate {params.dlc_conda_env}
        module load CUDA/12.9.1
        # Also rename the output file to the expected name
        # We don't actually know the name without querying deeplabcut, so just rename it
        python -c "import deeplabcut, os; fname = deeplabcut.analyze_videos('{params.dlc_model_configfile_path}', '{input.input_avi}', videotype='avi', gputouse=${{CUDA_VISIBLE_DEVICES:-0}}, save_as_csv=True); print('Produced raw files with name: ' + fname); os.rename(f'{output_behavior_dir}/raw_stack'+fname+'.h5', '{output_behavior_dir}/raw_stack_dlc.h5'); os.rename(f'{output_behavior_dir}/raw_stack'+fname+'.csv', '{output_behavior_dir}/raw_stack_dlc.csv')"
        """

rule create_centerline:
    input:
        input_binary_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask_coil_segmented_mask.btf",
        # From the coil unet, not directly from the SAM2 segmentation
        hdf5_file=f"{output_behavior_dir}/raw_stack_dlc.h5"

    params:
        output_path=f"{output_behavior_dir}/",# Ulises' functions expect the final slash
        number_of_neighbours="1",
        nose=config['nose'],# Should actually be the nose
        tail=config['tail'],
        num_splines=config['num_splines'],
        fill_with_DLC="1"
    output:
        output_skel_X=f"{output_behavior_dir}/skeleton_skeleton_X_coords.csv",
        output_skel_Y=f"{output_behavior_dir}/skeleton_skeleton_Y_coords.csv",
        output_spline_K=f"{output_behavior_dir}/skeleton_spline_K.csv",
        output_spline_X=f"{output_behavior_dir}/skeleton_spline_X_coords.csv",
        output_spline_Y=f"{output_behavior_dir}/skeleton_spline_Y_coords.csv",
        corrected_head=f"{output_behavior_dir}/skeleton_corrected_head_coords.csv",
        corrected_tail=f"{output_behavior_dir}/skeleton_corrected_tail_coords.csv"
    run:
        from centerline_behavior_annotation.centerline.dev import head_and_tail

        head_and_tail.main([
            '-i', str(input.input_binary_img),
            '-h5', str(input.hdf5_file),
            '-o', str(params.output_path),
            '-nose', str(params.nose),
            '-tail', str(params.tail),
            '-num_splines', str(params.num_splines),
            '-n', str(params.number_of_neighbours),
            '-dlc', str(params.fill_with_DLC),
        ])


# Benjamin-style rule that directly reads the config file
rule invert_curvature_sign:
    input:
        spline_K=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed.csv"
    params:
        ventral=config['ventral'],
    output:
        spline_K_signed=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv"
    run:
        from centerline_behavior_annotation.curvature.src import invert_curvature_sign

        # Call the invert_curvature_sign function with the correct parameters
        invert_curvature_sign.main_benjamin([
            '--spline_K_path', str(input.spline_K),
            '--ventral', str(params.ventral),
            '--output_file_path', str(output.spline_K_signed)
        ])

rule average_kymogram:
    input:
        spline_K=f"{output_behavior_dir}/skeleton_spline_K_signed.csv"
    params:
        #rolling_mean_type =,
        window=config['averaging_window']
    output:
        spline_K_avg=f"{output_behavior_dir}/skeleton_spline_K_signed_avg.csv"
    run:
        import pandas as pd

        df = pd.read_csv(input.spline_K,index_col=None,header=None)
        df = df.rolling(window=params.window,center=True,min_periods=1).mean()
        df.to_csv(output.spline_K_avg,header=None,index=None)
        print('end of python script')

rule average_xy_coords:
    input:
        spline_X=f"{output_behavior_dir}/skeleton_spline_X_coords.csv",
        spline_Y=f"{output_behavior_dir}/skeleton_spline_Y_coords.csv",
    params:
        #rolling_mean_type =,
        window=config['averaging_window']
    output:
        spline_X_avg=f"{output_behavior_dir}/skeleton_spline_X_coords_avg.csv",
        spline_Y_avg=f"{output_behavior_dir}/skeleton_spline_Y_coords_avg.csv",
    run:
        import pandas as pd

        df = pd.read_csv(input.spline_X,index_col=None,header=None)
        df = df.rolling(window=params.window,center=True,min_periods=1).mean()
        df.to_csv(output.spline_X_avg,header=None,index=None)

        df = pd.read_csv(input.spline_Y,index_col=None,header=None)
        df = df.rolling(window=params.window,center=True,min_periods=1).mean()
        df.to_csv(output.spline_Y_avg,header=None,index=None)

rule hilbert_transform_on_kymogram:
    input:
        spline_K=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv",
        output_path=f"{output_behavior_dir}/",# Ulises' functions expect the final slash
    params:
        output_path=f"{output_behavior_dir}/",# Ulises' functions expect the final slash
        fs=config["sampling_frequency"],
        window=config["hilbert_averaging_window"]
    output:
        # wont be created because they the outputs do not have the {sample} root
        hilbert_regenerated_carrier=f"{output_behavior_dir}/hilbert_regenerated_carrier.csv",
        hilbert_inst_freq=f"{output_behavior_dir}/hilbert_inst_freq.csv",
        hilbert_inst_phase=f"{output_behavior_dir}/hilbert_inst_phase.csv",
        hilbert_inst_amplitude=f"{output_behavior_dir}/hilbert_inst_amplitude.csv"

    #This $DIR only goes one time up
    run:
        from centerline_behavior_annotation.behavior_analysis.src import hilbert_transform

        hilbert_transform.main([
            '-i', str(params.output_path),
            '-kp', str(input.spline_K),
            '-fs', str(params.fs),
            '-w', str(params.window),
        ])

rule fast_fourier_transform:
    input:
        spline_K=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed",
    params:
        # project_folder
        sampling_frequency=config["sampling_frequency"],
        window=config["fft_averaging_window"],
        output_path=f"{output_behavior_dir}/",# Ulises' functions expect the final slash

    output:
        y_axis_file=f"{output_behavior_dir}/fft_y_axis.csv",#not correct ?
        xf_file=f"{output_behavior_dir}/fft_xf.csv"
    #This $DIR only goes one time up
    run:
        from centerline_behavior_annotation.centerline.dev import fourier_functions

        fourier_functions.main([
            '-i', str(params.output_path),
            '-kp', str(input.spline_K),
            '-fps', str(params.sampling_frequency),
            '-w', str(params.window),
        ])

rule reformat_skeleton_files:
    input:
        spline_K=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed",
        #should have signed spline_K
        spline_X=f"{output_behavior_dir}/skeleton_spline_X_coords_equi_dist_segment.csv",
        spline_Y=f"{output_behavior_dir}/skeleton_spline_Y_coords_equi_dist_segment.csv",
    #spline_list = ["{sample}_spline_K.csv", "{sample}_spline_X_coords.csv", "{sample}_spline_Y_coords.csv",]

    output:
        merged_spline_file=f"{output_behavior_dir}/skeleton_merged_spline_data_avg.csv",

    run:
        from centerline_behavior_annotation.centerline.dev import reformat_skeleton_files

        reformat_skeleton_files.main([
            '-i_K', str(input.spline_K),
            '-i_X', str(input.spline_X),
            '-i_Y', str(input.spline_Y),
            '-o', str(output.merged_spline_file),
        ])

rule annotate_behaviour:
    input:
        curvature_file=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv"

    params:
        pca_model_path=config["pca_model"],
        initial_segment=config["initial_segment"],
        final_segment=config["final_segment"],
        window=config["window"]
    output:
        principal_components=f"{output_behavior_dir}/principal_components.csv",
        behaviour_annotation=f"{output_behavior_dir}/beh_annotation.csv"
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
        #principal_components = f"{output_behavior_dir}/principal_components.csv"
        spline_K=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv"
    params:
        output_path=f"{output_behavior_dir}/",# Ulises' functions expect the final slash
        threshold=config["turn_threshold"],
        initial_segment=config["turn_initial_segment"],
        final_segment=config["turn_final_segment"],
        avg_window=config["turn_avg_window"]
    output:
        turns_annotation=f"{output_behavior_dir}/turns_annotation.csv"

    run:
        from centerline_behavior_annotation.curvature.src import annotate_turns_snakemake

        annotate_turns_snakemake.main([
            '-input', str(input.spline_K),
            '-t', str(params.threshold),
            '-i_s', str(params.initial_segment),
            '-f_s', str(params.final_segment),
            '-avg_window', str(params.avg_window),
            '-bh', str(output.turns_annotation),
        ])

rule self_touch:
    input:
        binary_img=f"{output_behavior_dir}/raw_stack_AVG_background_subtracted_normalised_worm_segmented_mask.btf"
    params:
        external_area=[7000, 20000],
        internal_area=[100, 2000],
    output:
        self_touch=f"{output_behavior_dir}/self_touch.csv"
    run:
        from imutils.src.imfunctions import stack_self_touch

        df = stack_self_touch(input.binary_img,params.external_area,params.internal_area)
        df.to_csv(output.self_touch)


rule calculate_parameters:
    #So far it only calculates speed
    input:
        curvature_file=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv"
    #This is used as a parameter because it is only used to find the main dir
    output:
        speed_file=f"{output_behavior_dir}/raw_worm_speed.csv"  # This is never produced, so this will always run
    params:
        output_path=f"{output_behavior_dir}/",# Ulises' functions expect the final slash
    run:
        from centerline_behavior_annotation.behavior_analysis.src import calculate_parameters

        calculate_parameters.main([
            '-i', str(params.output_path),
            '-r', str(raw_data_dir),
        ])


rule save_signed_speed:
    input:
        raw_speed_file=f"{output_behavior_dir}/raw_worm_speed.csv",
        behaviour_annotation=f"{output_behavior_dir}/beh_annotation.csv"
    output:
        signed_speed_file=f"{output_behavior_dir}/signed_worm_speed.csv"
    # This is never produced, so this will always run
    run:
        import pandas as pd

        raw_speed_df = pd.read_csv(input.raw_speed_file)
        ethogram_df = pd.read_csv(input.behaviour_annotation)
        signed_speed_df = pd.DataFrame()
        signed_speed_df['Raw Speed Signed (mm/s)'] = raw_speed_df['Raw Speed (mm/s)'] * ethogram_df[
            '0'] * -1  # to invert because fwd is -1 in the ethogram
        signed_speed_df.to_csv(output.signed_speed_file)
        print("If the ethogram had a running average and had less values at the start and end, so will the signed speed")


rule make_behaviour_figure:
    input:
        curvature_file=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv",
        pc_file=f"{output_behavior_dir}/principal_components.csv",
        beh_annotation_file=f"{output_behavior_dir}/beh_annotation.csv",
        speed_file=f"{output_behavior_dir}/signed_worm_speed.csv",
        turns_annotation=f"{output_behavior_dir}/turns_annotation.csv"
    output:
        figure=f"{output_behavior_dir}/behavioral_summary_figure.pdf"  #This is never produced, so it will always run
    params:
        output_path=f"{output_behavior_dir}/"  # Ulises' functions expect the final slash
    run:
        from centerline_behavior_annotation.behavior_analysis.src import make_figure_2

        make_figure_2.main([
            '-i', str(params.output_path),
            '-r', str(raw_data_dir),
            '-k', str(input.curvature_file),
            '-pcs', str(input.pc_file),
            '-beh', str(input.beh_annotation_file),
            '-speed', str(input.speed_file),
            '-turns', str(input.turns_annotation)
        ])


rule process_skeleton_curvature:
    input:
        skeleton_x=f"{output_behavior_dir}/skeleton_spline_X_coords.csv",
        skeleton_y=f"{output_behavior_dir}/skeleton_spline_Y_coords.csv"
    output:
        output_x=f"{output_behavior_dir}/skeleton_spline_X_coords_equi_dist_segment.csv",
        output_y=f"{output_behavior_dir}/skeleton_spline_Y_coords_equi_dist_segment.csv",
        output_curvature=f"{output_behavior_dir}/skeleton_spline_K_equi_dist_segment.csv",
        output_smoothed_curvature=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed.csv"
    params:
        spacing=config['relative_spacing'],
        num_sampled_points=config['num_sampled_points'],
        smoothing=config['smoothing'],
        time_sigma=config['time_sigma'],
        spatial_sigma=config['spatial_sigma'],
        max_columns=config['max_columns'],
    run:
        import sys
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

#
# Pharynx tracking (from old pipeline)
#
#TODO: downsampling
rule crop_pharynx_video:
    input:
        csv=f"{output_behavior_dir}/raw_stack_dlc.csv",
        avi=f"{output_behavior_dir}/raw_stack.avi"
    output:
        cropped_pharynx=f"{output_behavior_dir}/cropped_pharynx_video.avi"
    params:
        fps=config["fps"],
        crop_size=config["crop_size_pharynx"],
        dlc_nose_label=config["nose"],
        dlc_pharynx_label=config["pharynx"]

    run:
        # package installed in the autoscope environment
        from pharynx_tracking import crop_pharynx_video_script

        crop_pharynx_video_script.main([
            '--video', str(input.avi),
            '--csv', str(input.csv),
            '--output', str(output.cropped_pharynx),
            '--fps', str(params.fps),
            '--crop_size', str(params.crop_size),
            '--keypoint_nose', str(params.dlc_nose_label),
            '--keypoint_pharynx', str(params.dlc_pharynx_label),
        ])

rule pharynx_pump_dlc_analyze_videos:
    input:
        cropped_pharynx=f"{output_behavior_dir}/cropped_pharynx_video.avi"
    params:
        dlc_model_configfile_path=config["dlc_model_configfile_path_track_pumps"],
        network_string=config["network_string_pharynx"],
        dlc_conda_env=config["dlc_conda_env_name_only_dlc"]
    output:
        hdf5_file_pharynx=f"{output_behavior_dir}/cropped_pharynx_video_{config['network_string_pharynx']}.h5",
        csv_file_pharynx=f"{output_behavior_dir}/cropped_pharynx_video_{config['network_string_pharynx']}.csv"
    shell:
        """
        # Fix for xml_catalog_files_libxml2 variable
        if [ -z "${{xml_catalog_files_libxml2:-}}" ]; then
            export xml_catalog_files_libxml2=""
        fi 

        source /lisc/opt/sw/software/Conda/Miniforge3/bin/activate {params.dlc_conda_env}
        module load CUDA/12.9.1

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
        reversal_annotation=f"{output_behavior_dir}/beh_annotation.csv",
        turn_annotation=f"{output_behavior_dir}/turns_annotation.csv",
        spline_K=f"{output_behavior_dir}/skeleton_spline_K__equi_dist_segment_2D_smoothed_signed.csv",
        skeleton_spline_X_coords=f"{output_behavior_dir}/skeleton_spline_X_coords_equi_dist_segment.csv",
        skeleton_spline_Y_coords=f"{output_behavior_dir}/skeleton_spline_Y_coords_equi_dist_segment.csv",
        DLC_hdf5_file=f"{output_behavior_dir}/raw_stack_dlc.h5",
        pharynx_pump_csv=f"{output_behavior_dir}/cropped_pharynx_video_{config['network_string_pharynx']}.csv"
    params:
        # Paths the raw data path
        worm_pos=f"{raw_data_dir}/worm_pos.txt",

        # Global config parameters
        fps=config["fps"],
        dlc_nose_label=config["nose"],
        dlc_tail_label=config["tail"],
        bootstrap_iterations=100,
        bootstrap_seed=42,
        dC_lookback_frames=1,

        # Dataset-specific parameters from worm_config.yaml (NO DEFAULTS - will fail if missing)
        factor_px_to_mm=config["factor_px_to_mm"],
        video_resolution_x=config["video_resolution_x"],
        video_resolution_y=config["video_resolution_y"],
        conc_gradient_array=config["conc_gradient_array"],
        distance_array=config["distance_array"],
        top_left_pos=config["top_left_pos"],
        odor_pos=config["odor_pos"],
        diffusion_time_offset=config["diffusion_time_offset"],
        video_source=config["video_source"]
    output:
        chemotaxis_visualisation=f"{output_behavior_dir}/chemotaxis_analysis.pdf",
        chemotaxis_overview=f"{output_behavior_dir}/chemotaxis_overview.png",
        worm_movie=f"{output_behavior_dir}/worm_movie.avi",
        chemotaxis_params=f"{output_behavior_dir}/chemotaxis_params.csv",
        chemotaxis_h5=f"{output_behavior_dir}/chemotaxis_analysis_complete.h5",
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
