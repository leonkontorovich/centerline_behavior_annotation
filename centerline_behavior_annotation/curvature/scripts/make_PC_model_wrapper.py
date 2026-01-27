from centerline_behavior_annotation.curvature.src.make_PCA import make_pc_model_wrapper
import argparse

# from centerline_behavior_annotation.curvature.src.make_PCA import plot_pca_eigenvectors

# plot_pca_eigenvectors(pc_model_path=r"Z:\neurobiology\zimmer\wbfm\pca_models\2per\2per_segments_30_to_80_components_5_zscore_filtered.pkl",initial_segment=30,end_segment=80,save_path=r"Z:\neurobiology\zimmer\wbfm\pca_models\2per\eigenworms.png")
# TODO: commented lines here just for debugging purposes delete whenever
# make_pc_model_wrapper(root_folder=r"C:\Data\ZimmerLab\develop_new_PC_model")
# make_pc_model_wrapper(root_folder=r"\\samba.lisc.univie.ac.at\scratch\neurobiology\zimmer\fieseler\barlow_track_paper\jalaja\10072025\2025-07-05_Jalaja_L3", equi_distant_curvature=True, output_folder=r"\\samba.lisc.univie.ac.at\scratch\neurobiology\zimmer\wbfm\pca_models")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make PC model wrapper")
    parser.add_argument("--root_folder", help="Root folder path", required=True)
    parser.add_argument("--pc_model_name", help="PC model name", required=False)
    parser.add_argument("--output_folder", help="Output folder path", required=False)
    parser.add_argument("--initial_segment", type=int, help="Initial segment", required=False)
    parser.add_argument("--end_segment", type=int, help="End segment", required=False)
    parser.add_argument("--n_components", type=int, help="Number of components", required=False)
    parser.add_argument("--zscore_filter", type=bool, help="Z-score filter", required=False)
    parser.add_argument("--behavior_specific", type=str, help="name of behavior, if behavior specific PCA", required=False)
    parser.add_argument("--behavior_file_name", type=bool, help="file name including file extension of behavior annotation", required=False)
    parser.add_argument("--equidistant_curv", type=bool, help="should look for equidistant curvature files?", required=False)
    args = parser.parse_args()

    root_folder = args.root_folder
    pc_model_name = args.pc_model_name if len(args.pc_model_name) > 0 else None
    output_folder = args.output_folder
    initial_segment = int(args.initial_segment)
    end_segment = int(args.end_segment)
    n_components = int(args.n_components)
    # check if zscore_filter is a boolean or a string that can be converted to boolean
    if args.zscore_filter is None:
        zscore_filter = False
    elif isinstance(args.zscore_filter, bool):
        zscore_filter = args.zscore_filter
    else:
        # convert string to boolean
        if isinstance(args.zscore_filter, str):
            args.zscore_filter = args.zscore_filter.lower()
        if args.zscore_filter in ['true', '1', 'yes']:
            zscore_filter = True
        elif args.zscore_filter in ['false', '0', 'no']:
            zscore_filter = False
        else:
            raise ValueError(f"Invalid value for zscore_filter: {args.zscore_filter}")

    # check if equidistant_curv is a boolean or a string that can be converted to boolean
    if args.equidistant_curv is None:
        equidistant_curv = False
    elif isinstance(args.equidistant_curv, bool):
        equidistant_curv = args.equidistant_curv
    else:
        # convert string to boolean
        if isinstance(args.equidistant_curv, str):
            args.equidistant_curv = args.equidistant_curv.lower()
        if args.equidistant_curv in ['true', '1', 'yes']:
            equidistant_curv = True
        elif args.equidistant_curv in ['false', '0', 'no']:
            equidistant_curv = False
        else:
            raise ValueError(f"Invalid value for equidistant_curv: {args.equidistant_curv}")

    behavior_specific = args.behavior_specific
    behavior_file_name = args.behavior_file_name


    print(f"calling make_pc_model_wrapper, with the following parameters: {root_folder=}, {pc_model_name=}, {output_folder=}, {initial_segment=}, {end_segment=}, {n_components=}, {zscore_filter=}")

    make_pc_model_wrapper(root_folder=root_folder,
                          pc_model_name=pc_model_name,
                          output_folder=output_folder,
                          initial_segment=initial_segment,
                          end_segment=end_segment,
                          n_components=n_components,
                          zscore_filter=zscore_filter,
                          behavior_specific=behavior_specific,
                          behavior_file_name=behavior_file_name,
                          equi_distant_curvature=equidistant_curv
                          )

