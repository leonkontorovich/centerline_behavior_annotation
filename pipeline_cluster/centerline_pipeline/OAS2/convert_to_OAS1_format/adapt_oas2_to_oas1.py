import shutil
from pathlib import Path
import pandas as pd
from video_conversions.ndtiff import ometiff2ndtiff

# Path to default files
# - default raw file config file used for annotating vulva side
CONFIG_PATH = Path("/lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/OAS1/sam2_wbfm_spinoff_with_pharynx_pumping/configs/raw_data_config/worm_config.yaml")

def process_gantry_csv(recording_folder: Path):
    """Extract time, x, y from gantry_position.csv and save as txt."""
    csv_files = list(recording_folder.glob("*gantry_position.csv"))
    if not csv_files:
        print(f"  [INFO] No gantry CSV found in {recording_folder.name}")
        return

    csv_path = csv_files[0]
    df = pd.read_csv(csv_path, usecols=["time", "x", "y"])
    df.columns = ["time", "X", "Y"]

    output_name = f"{recording_folder.name}-TablePosRecord.txt"
    output_path = recording_folder / output_name
    df.to_csv(output_path, index=False)
    # print(f"  [DONE] CSV processed and saved as {output_name}")

def convert_btf_to_ndtiff(recording_folder: Path):
    """
    Convert BTF to ND-TIFF format using external conversion script.
    """
    btf_files = list(recording_folder.glob("*.btf"))
    if not btf_files:
        print(f"  [INFO] No BTF file found in {recording_folder.name}")
        return

    btf = btf_files[0]
    ch0_name = f"{recording_folder.name}_Ch0"

    print(f"  [RUN] Converting BTF to ND-TIFF ({ch0_name})")

    ometiff2ndtiff.main([
        "--input", str(btf),
        "--output", str(recording_folder),
        "--name", ch0_name,
    ])
    print("  [DONE] Conversion completed")



def copy_config(recording_folder: Path):
    """Copy worm_config.yaml into the recording folder."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

    shutil.copy(CONFIG_PATH, recording_folder / "worm_config.yaml")
    # print("  [DONE] Config file copied")

def process_one_folder(recording_folder: Path):
    """Process a single recording folder."""
    print(f"[PROCESSING] {recording_folder.name}")
    process_gantry_csv(recording_folder)
    convert_btf_to_ndtiff(recording_folder)
    copy_config(recording_folder)
    print(f"[DONE] Finished {recording_folder.name}\n")

def process_root_folder(root_folder: Path):
    """
    Main processing function.

    This function:
    1. Scans the root folder for subfolders containing 'recording' in the name.
    2. For each such folder:
       - Processes the gantry CSV (time, x, y → TXT)
       - Converts the BTF file to ND-TIFF format
       - Copies worm_config.yaml into the folder
    3. Prints informative messages for each action.
    """
    recording_folders = [
        f for f in root_folder.iterdir() if f.is_dir() and "worm" in f.name
    ]

    if not recording_folders:
        print(f"No folders containing 'worm' found in {root_folder}")
        return

    print(f"Found {len(recording_folders)} folder(s) with 'recording' in the name:")
    for f in recording_folders:
        print(f" - {f.name}")

    print("\nStarting processing...\n")
    for folder in recording_folders:
        print(f"[PROCESSING] {folder.name}")
        process_gantry_csv(folder)
        convert_btf_to_ndtiff(folder)
        copy_config(folder)
        print(f"[DONE] Finished {folder.name}\n")

    print("All done!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python prepare_OAS_formatting.py <recording_folder>")
        sys.exit(1)

    recording_folder = Path(sys.argv[1])
    process_one_folder(recording_folder)
