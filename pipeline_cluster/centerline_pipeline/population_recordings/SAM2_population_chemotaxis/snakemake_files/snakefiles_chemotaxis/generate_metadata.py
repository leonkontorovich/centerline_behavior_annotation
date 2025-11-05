#!/usr/bin/env python3
"""
Pre-generate all .meta.json files for dynamic resource allocation.
Run this BEFORE running the Snakemake pipeline.
"""

import json
import subprocess
import sys
from pathlib import Path
import yaml

def count_tiff_frames(tiff_path):
    """Count frames in a multi-page TIFF using tiffinfo"""
    try:
        result = subprocess.run(
            ['tiffinfo', str(tiff_path)], 
            capture_output=True, 
            text=True,
            check=True
        )
        frame_count = result.stdout.count('TIFF Directory')
        return frame_count
    except subprocess.CalledProcessError as e:
        print(f"❌ Error reading {tiff_path}: {e}", file=sys.stderr)
        return 0
    except FileNotFoundError:
        print("❌ tiffinfo not found. Install libtiff-tools", file=sys.stderr)
        sys.exit(1)

def read_existing_metadata(meta_path):
    """Read duration from existing .meta.json file"""
    try:
        with open(meta_path) as f:
            metadata = json.load(f)
            duration = float(metadata["streams"][0]["duration"])
            frames = int(metadata["streams"][0]["nb_frames"])
            return duration, frames
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError):
        return None, None

def generate_metadata(tiff_path, output_meta_path, fps):
    """Generate .meta.json file for a TIFF"""
    frame_count = count_tiff_frames(tiff_path)
    duration = frame_count / fps if frame_count > 0 else 0
    
    # Create output directory if needed
    output_meta_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write metadata
    metadata = {
        "streams": [{
            "duration": str(duration),
            "nb_frames": str(frame_count)
        }]
    }
    
    with open(output_meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return duration, frame_count

def format_duration(seconds):
    """Format seconds as MM:SS or HH:MM:SS"""
    if seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}:{mins:02d}:{secs:02d}"

def main():
    # Load config to get fps
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    fps = config['fps']
    
    print(f"🔍 Scanning for track.tif files...")
    print(f"📊 Using FPS: {fps}")
    print("=" * 60)
    
    # Find all track.tif files
    tiff_files = list(Path('.').rglob('*/*/track.tif'))
    
    if not tiff_files:
        print("❌ No track.tif files found!")
        sys.exit(1)
    
    print(f"Found {len(tiff_files)} videos\n")
    
    total_duration = 0
    new_count = 0
    existing_count = 0
    
    for tiff_path in sorted(tiff_files):
        # Get dataset/track_dir from path
        track_dir = tiff_path.parent.name
        dataset = tiff_path.parent.parent.name
        
        # Output path: dataset/track_dir/output/.meta.json
        output_meta = tiff_path.parent / 'output' / '.meta.json'
        
        # Check if metadata already exists
        if output_meta.exists():
            duration, frames = read_existing_metadata(output_meta)
            if duration is not None:
                total_duration += duration
                existing_count += 1
                print(f"⏭️  {dataset}/{track_dir}: {frames} frames, {format_duration(duration)} (existing)")
            else:
                # Corrupted metadata, regenerate
                duration, frames = generate_metadata(tiff_path, output_meta, fps)
                total_duration += duration
                new_count += 1
                print(f"♻️  {dataset}/{track_dir}: {frames} frames, {format_duration(duration)} (regenerated)")
        else:
            # Generate new metadata
            duration, frames = generate_metadata(tiff_path, output_meta, fps)
            total_duration += duration
            new_count += 1
            print(f"✅ {dataset}/{track_dir}: {frames} frames, {format_duration(duration)} (new)")
    
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   • New metadata generated: {new_count}")
    print(f"   • Existing metadata found: {existing_count}")
    print(f"   • Total videos: {len(tiff_files)}")
    print(f"   • Total duration: {format_duration(total_duration)} ({total_duration/3600:.2f} hours)")
    
    # Resource allocation preview
    print("\n📋 Resource Allocation Preview:")
    print("-" * 60)
    
    try:
        # Load cluster config
        with open('cluster_config.yaml') as f:
            cluster_config = yaml.safe_load(f)
        
        # Show resource scaling for shortest video
        if tiff_files:
            # Find shortest video
            durations = []
            for p in tiff_files:
                meta_path = p.parent / 'output' / '.meta.json'
                dur, _ = read_existing_metadata(meta_path)
                if dur is not None:
                    durations.append(dur)
            
            if durations:
                min_duration = min(durations)
                max_duration = max(durations)
                avg_duration = sum(durations) / len(durations)
                
                scale_min = min_duration / 1800  # MAX_CROP_SEC = 1800
                scale_max = max_duration / 1800
                
                print(f"Video duration range:")
                print(f"  • Shortest: {format_duration(min_duration)} ({scale_min*100:.1f}% of 30-min baseline)")
                print(f"  • Longest:  {format_duration(max_duration)} ({scale_max*100:.1f}% of 30-min baseline)")
                print(f"  • Average:  {format_duration(avg_duration)}")
                
                print(f"\nExample scaled resources for SHORTEST video (dlc_analyze_videos):")
                
                # Get base resources
                base_cpus = cluster_config.get('dlc_analyze_videos', {}).get('cpus_per_task', 24)
                base_mem = cluster_config.get('dlc_analyze_videos', {}).get('mem', '64G')
                base_time = cluster_config.get('dlc_analyze_videos', {}).get('time', '0-08:00:00')
                
                # Calculate scaled for shortest video
                scaled_cpus = max(1, min(base_cpus, int(base_cpus * scale_min + 0.5)))
                scaled_mem_gb = max(1, int(int(base_mem.rstrip('G')) * scale_min))
                scaled_hours = max(1, int(8 * scale_min))
                
                print(f"  • CPUs:   {base_cpus} → {scaled_cpus}")
                print(f"  • Memory: {base_mem} → {scaled_mem_gb}G")
                print(f"  • Time:   {base_time} → ~{scaled_hours} hour(s)")
                
                print(f"\n💡 Note: sam2_segment always uses FIXED resources (no scaling)")
    except Exception as e:
        print(f"⚠️  Could not generate resource preview: {e}")
    
    print("\n🚀 Ready to run: ./RUNME_cluster.sh")

if __name__ == '__main__':
    main()