#!/usr/bin/env python3
"""
End-to-end Snakemake DAG test.
Builds a tiny synthetic dataset and runs `snakemake -n` (dry-run) to ensure
that the DAG resolves successfully and there are no syntax/configuration errors
in the Snakefile or its included rules.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_HERE = Path(__file__).resolve().parent
_SNAKEDIR = _HERE.parent / "snakemake_files" / "snakefiles_aerotaxis"
_SNAKEFILE = _SNAKEDIR / "Snakefile"
_CONFIG_TMPL = _SNAKEDIR / "config.yaml"
_REPO_ROOT = _HERE.parents[4]

def test_snakemake_dag_resolves(tmp_path):
    # 1. Setup a synthetic recording folder
    rec_name = "2026-01-01_12-00-00_N2_A_new"
    rec_dir = tmp_path / rec_name
    rec_dir.mkdir()
    
    # Create fake parameter file
    params = {
        "recording": {
            "fps": 10.0,
            "pixel_size_mm": 0.01221
        },
        "region_extraction": {
            "min_region_size": 400,
            "max_region_size": 1000
        }
    }
    (rec_dir / "parameters.yaml").write_text(yaml.dump(params))
    
    # Create one track
    track_dir = rec_dir / f"{rec_name.replace('_new', '')}_track_0"
    track_dir.mkdir()
    (track_dir / "track.tif").touch()
    (track_dir / "track.txt").write_text("time_imputed_seconds,X,Y\n0,0,0\n")
    
    # 2. Setup config
    cfg = yaml.safe_load(_CONFIG_TMPL.read_text())
    cfg["centerline_repo_path"] = str(_REPO_ROOT)
    
    # Lower relative_spacing to avoid initial_segment errors with fake small frames? 
    # Not needed for a pure DAG check, as it doesn't execute rules, but good practice.
    
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg))
    
    if not shutil.which("snakemake"):
        pytest.skip("snakemake not found in PATH")
        
    # 3. Run snakemake -n
    cmd = [
        "snakemake",
        "-n",
        "-s", str(_SNAKEFILE),
        "--configfile", str(cfg_path),
        "-d", str(rec_dir)
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if res.returncode != 0:
        print(res.stdout, file=sys.stdout)
        print(res.stderr, file=sys.stderr)
        
    assert res.returncode == 0, "Snakemake DAG failed to resolve."
