"""
main.py
=======

Entry point for the snow condition mapping tool.

Usage:
    python main.py --files station1.smet station2.smet --output my_map.html
    python main.py --folder ./data/2025_season/ --output current_conditions.html
"""

import argparse
from pathlib import Path
from typing import List
from read_smet import parse_smet, get_station_conditions
from map_conditions import generate_map
from publish import publish_file

def gather_smet_files(args) -> List[Path]:
    """Collects list of SMET files based on arguments."""
    files = []
    
    if args.folder:
        folder = Path(args.folder)
        if not folder.exists() or not folder.is_dir():
            print(f"❌ Error: Folder '{folder}' does not exist or is not a directory.")
            return []
        # glob for .smet files (case insensitive if needed, but usually .smet)
        files = list(folder.rglob("*.smet"))
        if not files:
            print(f"⚠️  No .smet files found in folder: {folder}")
            
    elif args.files:
        for f_str in args.files:
            p = Path(f_str)
            if p.exists() and p.is_file():
                files.append(p)
            else:
                print(f"⚠️  Warning: Input file not found or invalid: {p}")
    
    return files

def main():
    parser = argparse.ArgumentParser(
        description="Generate an interactive snow conditions map from SNOWPACK .smet files."
    )
    
    # Input group: User must provide either a list of files OR a folder
    input_group = parser.add_mutually_exclusive_group(required=False)#True)
    input_group.add_argument(
        '--files', 
        nargs='+', 
        help="List of paths to .smet files"
    )
    input_group.add_argument(
        '--folder', 
        default='data',
        help="Path to a folder containing .smet files"
    )
    
    # Output argument
    parser.add_argument(
        '--output', 
        default="snow_conditions_map.html",
        help="Path to write the output HTML map (default: snow_conditions_map.html)"
    )

    args = parser.parse_args()
    
    # 1. Gather Files
    smet_files = gather_smet_files(args)
    
    if not smet_files:
        print("❌ No valid SMET files to process. Exiting.")
        return

    print(f"🔎 Found {len(smet_files)} files to process.")
    
    # 2. Process Files
    stations_data = []
    for f_path in smet_files:
        try:
            meta, df = parse_smet(f_path)
            conditions = get_station_conditions(meta, df)
            stations_data.append(conditions)
            print(f"   ✓ Processed: {f_path.name}")
        except Exception as e:
            print(f"   ❌ Failed to process {f_path.name}: {e}")

    # 3. Generate Map
    if stations_data:
        generate_map(stations_data, output_file=args.output)
        #publish_file(args.output)

    else:
        print("❌ No station data could be extracted.")

if __name__ == '__main__':
    main()