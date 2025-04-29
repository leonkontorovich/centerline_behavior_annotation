from centerline_behavior_annotation.curvature.src.make_PCA import make_pc_model_wrapper
import argparse

# TODO: commented lines here just for debugging purposes delete whenever
# make_pc_model_wrapper(root_folder=r"C:\Data\ZimmerLab\develop_new_PC_model")
# make_pc_model_wrapper(root_folder=r"Z:\neurobiology\zimmer\ItamarLev\feedback_story\WBFM\1per_barlow")

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

    args = parser.parse_args()

    root_folder = args.root_folder
    pc_model_name = args.pc_model_name if len(args.pc_model_name) > 0 else None
    output_folder = args.output_folder
    initial_segment = int(args.initial_segment)
    end_segment = int(args.end_segment)
    n_components = int(args.n_components)
    zscore_filter = True if args.zscore_filter.lower() in ['true', '1'] else False
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
                          behavior_file_name=behavior_file_name
                          )

