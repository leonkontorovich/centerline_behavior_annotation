#!/usr/bin/env python3
"""
Parses an Alicat gas script (.txt) and updates all config.yaml files
found in the current directory's `*_new/` subfolders.

Usage:
    python parse_gas_script.py <path_to_gasscript.txt>
"""

import sys
import os
import glob
import re

def parse_gas_script(script_path):
    with open(script_path, 'r') as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
    
    if not lines:
        raise ValueError("No data lines found in gas script.")

    # Helper to convert fraction to percentage string
    def get_state(line):
        parts = line.split(',')
        if len(parts) < 4:
            raise ValueError(f"Unexpected line format: {line}")
        o2_frac = float(parts[3])
        o2_pct = int(round(o2_frac * 100))
        return f"{o2_pct}pct_O2", int(parts[0])

    # First line is baseline
    baseline_state, baseline_dur = get_state(lines[0])
    
    # We assume the next lines form the cycle. 
    # Let's find the repeating pattern. Usually it's 2 phases (pulse, return).
    # We'll just grab the next two distinct lines as the cycle block.
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

    # We will replace the aerotaxis block using regex.
    # The block is at the end of the file, so we match from 'aerotaxis:' to the end.
    
    new_block = f"""aerotaxis:
  t0_offset_s: 0.0             # absolute recording time (s) at which the protocol starts
  baseline_duration_s: {baseline_dur}
  baseline_state: "{baseline_state}"
  cycle:
"""
    for state, dur in cycle:
        new_block += f'    - {{state: "{state}", duration_s: {dur}}}\n'
    
    new_block += "  n_cycles: null               # null = repeat to end of recording\n"

    # Replace existing aerotaxis block
    if "aerotaxis:" in content:
        content = re.sub(r'aerotaxis:.*', new_block, content, flags=re.DOTALL)
    else:
        # Append if not found
        content += "\n" + new_block

    with open(config_path, 'w') as f:
        f.write(content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_gas_script.py <path_to_gasscript.txt>")
        sys.exit(1)
        
    script_path = sys.argv[1]
    print(f"Parsing gas script: {script_path}")
    
    try:
        baseline_dur, baseline_state, cycle = parse_gas_script(script_path)
    except Exception as e:
        print(f"Error parsing script: {e}")
        sys.exit(1)
        
    print(f"Found Baseline: {baseline_dur}s of {baseline_state}")
    print("Found Cycle:")
    for state, dur in cycle:
        print(f"  - {dur}s of {state}")

    # Find all config.yaml files in *_new/ directories
    configs = glob.glob("*/*_new/config.yaml") + glob.glob("*_new/config.yaml")
    
    if not configs:
        print("\nNo config.yaml files found! Did you run Step 3 (create_folders...) first?")
        sys.exit(0)
        
    print(f"\nUpdating {len(configs)} config.yaml files...")
    for c in configs:
        update_config_file(c, baseline_dur, baseline_state, cycle)
        print(f"Updated {c}")
        
    print("\nSuccess! All configurations have been automatically populated.")

if __name__ == "__main__":
    main()
