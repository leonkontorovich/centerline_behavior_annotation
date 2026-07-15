#!/usr/bin/env python3
"""
Automates the full preparation of a population aerotaxis dataset for the pipeline.
This script:
1. Creates `*_new` folders inside the target dataset directory.
2. Moves the raw recording folders into their respective `*_new` folders.
3. Copies all necessary pipeline scripts and config templates into the `*_new` folders.
4. Parses the given Alicat gas script (.txt) to extract the baseline and cycles.
5. Updates the `config.yaml` files in every `*_new` folder with the correct gas protocol.

Usage:
    python setup_aerotaxis_dataset.py <dataset_directory> <path_to_gasscript.txt>
"""

import sys
import os
import shutil
import glob
import re

# The source folder containing the universal pipeline templates
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_FOLDER = os.path.join(SCRIPT_DIR, "../population_recordings/SAM2_population_aerotaxis/snakemake_files/snakefiles_aerotaxis")

def parse_gas_script(script_path):
    with open(script_path, 'r') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
    
    def get_state(line):
        parts = line.split(',')
        if len(parts) < 4:
            raise ValueError(f"Unexpected line format: {line}")
        o2_frac = float(parts[3])
        o2_pct = int(round(o2_frac * 100))
        return f"{o2_pct}pct_O2", int(parts[0])

    if not lines:
        raise ValueError("No data lines found in gas script.")

    baseline_state, baseline_dur = get_state(lines[0])
    cycle = []
    
    if len(lines) > 1:
        pulse_state, pulse_dur = get_state(lines[1])
        cycle.append((pulse_state, pulse_dur))
    if len(lines) > 2:
        return_state, return_dur = get_state(lines[2])
        cycle.append((return_state, return_dur))
        
    return baseline_dur, baseline_state, cycle

def update_config_file(config_path, baseline_dur, baseline_state, cycle):
    with open(config_path, 'r') as f:
        content = f.read()
    
    new_block = f"""aerotaxis:
  t0_offset_s: 0.0             # absolute recording time (s) at which the protocol starts
  baseline_duration_s: {baseline_dur}
  baseline_state: "{baseline_state}"
  cycle:
"""
    for state, dur in cycle:
        new_block += f'    - {{state: "{state}", duration_s: {dur}}}\n'
    new_block += "  n_cycles: null               # null = repeat to end of recording\n"

    if "aerotaxis:" in content:
        content = re.sub(r'aerotaxis:.*', new_block, content, flags=re.DOTALL)
    else:
        content += "\n" + new_block

    with open(config_path, 'w') as f:
        f.write(content)

def main():
    if len(sys.argv) < 3:
        print("Usage: python setup_aerotaxis_dataset.py <dataset_directory> <path_to_gasscript.txt>")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    gas_script = sys.argv[2]
    
    if not os.path.exists(target_dir):
        print(f"Error: Target directory {target_dir} not found.")
        sys.exit(1)
    if not os.path.exists(gas_script):
        print(f"Error: Gas script {gas_script} not found.")
        sys.exit(1)

    print("Parsing gas script...")
    baseline_dur, baseline_state, cycle = parse_gas_script(gas_script)
    
    print(f"Detected Baseline: {baseline_dur}s {baseline_state}")
    for state, dur in cycle:
        print(f"Detected Cycle Phase: {dur}s {state}")

    print("\nProcessing recording folders...")
    # Find subfolders that are not already processed (_new)
    subfolders = [os.path.join(target_dir, d) for d in os.listdir(target_dir) 
                  if os.path.isdir(os.path.join(target_dir, d)) and not d.endswith('_new')]
                  
    if not subfolders:
        print("No raw recording folders found to process (all folders might already be _new folders).")
        sys.exit(0)

    for subfolder in subfolders:
        folder_name = os.path.basename(subfolder)
        new_folder = os.path.join(target_dir, f"{folder_name}_new")
        print(f"Processing: {folder_name}")
        
        # Create new folder
        os.makedirs(new_folder, exist_ok=True)
        
        # Move original folder inside new folder
        new_subfolder_path = os.path.join(new_folder, folder_name)
        if not os.path.exists(new_subfolder_path):
            shutil.move(subfolder, new_folder)
        
        # Copy pipeline files
        files_to_copy = [
            "cluster_config.yaml", "config.yaml", "Snakefile",
            "RUNME_cluster.sh", "submit_wrapper.sh", 
            "generate_metadata.py", "extract_temporal_features.py", "README.md"
        ]
        
        for f in files_to_copy:
            src_f = os.path.join(SRC_FOLDER, f)
            dst_f = os.path.join(new_folder, f)
            if os.path.exists(src_f):
                shutil.copy2(src_f, dst_f)
                # Make executables executable
                if f.endswith('.sh'):
                    os.chmod(dst_f, 0o755)
            else:
                print(f"Warning: Source file {src_f} not found!")
        
        # Update config.yaml
        config_path = os.path.join(new_folder, "config.yaml")
        if os.path.exists(config_path):
            update_config_file(config_path, baseline_dur, baseline_state, cycle)
            print(f"  -> Pipeline files copied and config updated successfully.")

    print("\nSuccess! The dataset is ready for the bubble filter.")

if __name__ == "__main__":
    main()
