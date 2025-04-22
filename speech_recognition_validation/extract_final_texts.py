#!/usr/bin/env python3
"""
Script to filter and dedupe recognition result JSON files, extracting only the final recognized sentence and its timestamp.

Usage:
    python filter_recognition_results.py <input_dir> <output_dir>

Each JSON file matching `recognition_result_*_interview.json` in the input directory
will be processed, and a new file named `<old_name>_filtered.json` will be created
in the output directory, containing a deduplicated, time-sorted list of objects with `text` and `time_ms`.
"""
import os
import json
import argparse
import glob

def process_file(filepath, output_dir):
    """
    Process a single JSON file, extracting and deduplicating final recognized sentences and times.
    Writes the filtered results to the output directory.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Map to collect unique time_ms entries, preferring refined results
    filtered_map = {}
    for entry in data:
        # Determine if this entry has a refinement
        is_refined = 'final_refinement' in entry
        alt = None
        # Try to extract the most accurate alternative
        if is_refined:
            try:
                alt = entry['final_refinement']['normalized_text']['alternatives'][0]
            except (KeyError, IndexError):
                alt = None
        # Fallback to final if no refinement found
        if alt is None and 'final' in entry:
            try:
                alt = entry['final']['alternatives'][0]
            except (KeyError, IndexError):
                alt = None

        if alt:
            text = alt.get('text')
            time_ms = alt.get('end_time_ms')
            # Deduplicate by time_ms, prefer refined entries
            if time_ms in filtered_map and not is_refined:
                continue
            filtered_map[time_ms] = {'text': text, 'time_ms': time_ms}

    # Sort by numeric time and build list
    sorted_items = sorted(filtered_map.items(), key=lambda x: int(x[0]))
    filtered = [item for _, item in sorted_items]

    # Prepare output path
    base = os.path.basename(filepath)
    name, ext = os.path.splitext(base)
    out_name = f"{name}_filtered{ext}"
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, out_name)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"Processed {base} -> {out_name}, entries: {len(filtered)}")


def main():
    parser = argparse.ArgumentParser(
        description="Filter and dedupe recognition result JSON files, extracting final sentences and times."
    )
    parser.add_argument(
        'input_dir',
        help='Path to the folder containing JSON files'
    )
    parser.add_argument(
        'output_dir',
        help='Path to the folder where filtered files will be saved'
    )
    args = parser.parse_args()

    pattern = os.path.join(args.input_dir, 'recognition_result_*_interview.json')
    files = glob.glob(pattern)
    if not files:
        print(f"No files found matching pattern {pattern}")
        return

    for filepath in files:
        process_file(filepath, args.output_dir)

if __name__ == '__main__':
    main()
