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

def parse_gas_script(script_path, o2_col=3, dur_col=0):
    """
    Parse an Alicat mass-flow-controller script into (baseline, cycle).

    The script is comma-separated, one phase per line; column `dur_col`
    (default 0) is the phase duration in seconds and column `o2_col` (default 3)
    is the O2 fraction (0-1). Lines that are blank or start with `@` are ignored.

    The FIRST phase becomes the baseline; ALL remaining phases become the
    repeating cycle (not just the first two) -- so scripts with more than one
    pulse level, or a longer repeating unit, are handled. Every line is
    validated (duration > 0, O2 fraction in [0, 1]); a malformed line raises a
    clear error naming the offending line rather than silently skewing timing.

    Returns (baseline_dur, baseline_state, cycle) where cycle is a list of
    (state_label, duration_s) tuples.
    """
    with open(script_path, 'r') as f:
        raw = [(i + 1, l.strip()) for i, l in enumerate(f)]
    lines = [(n, l) for n, l in raw if l and not l.startswith('@')]

    def get_state(lineno, line):
        parts = line.split(',')
        if len(parts) <= max(o2_col, dur_col):
            raise ValueError(
                f"gas script line {lineno} has {len(parts)} columns, need > "
                f"{max(o2_col, dur_col)}: {line!r}")
        try:
            duration = int(round(float(parts[dur_col])))
            o2_frac = float(parts[o2_col])
        except ValueError:
            raise ValueError(f"gas script line {lineno}: non-numeric duration/O2: {line!r}")
        if duration <= 0:
            raise ValueError(f"gas script line {lineno}: duration must be > 0 (got {duration}): {line!r}")
        if not 0.0 <= o2_frac <= 1.0:
            raise ValueError(
                f"gas script line {lineno}: O2 fraction {o2_frac} not in [0,1]; "
                f"is column {o2_col} really the O2 fraction? line: {line!r}")
        o2_pct = int(round(o2_frac * 100))
        return f"{o2_pct}pct_O2", duration

    if not lines:
        raise ValueError("No data lines found in gas script.")

    baseline_state, baseline_dur = get_state(*lines[0])
    cycle = [(get_state(n, l)) for n, l in lines[1:]]

    if not cycle:
        print("Warning: gas script has only a baseline phase; no repeating cycle "
              "was detected. Add pulse/return lines or edit config.yaml by hand.")
    return baseline_dur, baseline_state, cycle

def _build_aerotaxis_block(baseline_dur, baseline_state, cycle):
    block = [
        "aerotaxis:",
        "  t0_offset_s: 0.0             # absolute recording time (s) at which the protocol starts",
        f"  baseline_duration_s: {baseline_dur}",
        f'  baseline_state: "{baseline_state}"',
        "  cycle:",
    ]
    block += [f'    - {{state: "{state}", duration_s: {dur}}}' for state, dur in cycle]
    block.append("  n_cycles: null               # null = repeat to end of recording")
    return "\n".join(block) + "\n"


def update_config_file(config_path, baseline_dur, baseline_state, cycle):
    """
    Replace ONLY the top-level `aerotaxis:` block in config.yaml, leaving any
    keys before or after it untouched.

    The previous implementation used `re.sub('aerotaxis:.*', ..., DOTALL)`, which
    deletes everything from `aerotaxis:` to end-of-file -- safe only while
    `aerotaxis:` happens to be the last block. This scans line-by-line instead:
    it finds the `aerotaxis:` line and replaces it together with the indented /
    blank / comment lines that belong to it, stopping at the next top-level key.
    """
    with open(config_path, 'r') as f:
        lines = f.read().splitlines()

    new_block = _build_aerotaxis_block(baseline_dur, baseline_state, cycle).splitlines()

    start = next((i for i, l in enumerate(lines) if re.match(r'^aerotaxis\s*:', l)), None)
    if start is None:
        # append (keep a blank separator line)
        out = lines + ([""] if lines and lines[-1].strip() else []) + new_block
    else:
        # consume the block body: subsequent indented / blank / comment lines,
        # up to (not including) the next top-level (column-0, non-comment) key.
        end = start + 1
        while end < len(lines):
            l = lines[end]
            if l.strip() == "" or l.startswith((" ", "\t")) or l.lstrip().startswith("#"):
                end += 1
            else:
                break
        out = lines[:start] + new_block + lines[end:]

    with open(config_path, 'w') as f:
        f.write("\n".join(out) + "\n")

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
