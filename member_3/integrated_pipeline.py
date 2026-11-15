"""
NASA Earth Information Center - Earth Jukebox
INTEGRATED PIPELINE: Member 2 (Image & Grid RGB) + Member 3 (Scientific Windspeed Mapping)

Connects:
    1. Member 2 (rgbout/nasa2py.py): Image loading, 5x5 grid division, RGB extraction.
    2. Member 3 (windspeed_mapper.py): NASA legend mapping, Euclidean color distance,
       confidence scoring, statistical analysis, and sound CSV/JSON export for Member 4 & 5.

Usage:
    python integrated_pipeline.py
    python integrated_pipeline.py --image path/to/wind_image.jpg
    python integrated_pipeline.py --json rgbout/wind_grid_data.json
    python integrated_pipeline.py --use-median
"""

import os
import sys
import argparse

# Ensure current directory and rgbout are on the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

rgbout_dir = os.path.join(current_dir, "rgbout")
if rgbout_dir not in sys.path:
    sys.path.insert(0, rgbout_dir)

# Import Member 3 functions
import windspeed_mapper as m3

# Attempt to import Member 2 functions
try:
    import nasa2py as m2
    HAS_MEMBER2_MODULE = True
except ImportError:
    try:
        from rgbout import nasa2py as m2
        HAS_MEMBER2_MODULE = True
    except ImportError:
        HAS_MEMBER2_MODULE = False


def run_pipeline(image_path=None, json_path=None, use_median=False, legend_path="nasa_legend.csv"):
    """
    Executes the integrated Member 2 -> Member 3 pipeline.
    """
    print("\n" + "=" * 80)
    print("NASA EARTH JUKEBOX - INTEGRATED PIPELINE (MEMBER 2 + MEMBER 3)")
    print("=" * 80)

    # 1. Load Legend (Member 1)
    if os.path.exists(legend_path):
        print(f"[Member 1] Loading NASA legend from '{legend_path}'...")
        legend = m3.load_legend_from_csv(legend_path)
    else:
        print("[Member 1] Using default illustrative NASA color legend...")
        legend = m3.DEFAULT_NASA_LEGEND

    grid_results = None

    # 2. Extract or Load Grid Colors (Member 2)
    # Mode A: Process from Image (if an image is supplied or found)
    candidate_images = []
    if image_path:
        candidate_images.append(image_path)
    candidate_images.extend([
        os.path.join(rgbout_dir, "images", "wind_speed.jpg"),
        os.path.join(current_dir, "images", "wind_speed.jpg"),
        os.path.join(current_dir, "wind_speed.jpg"),
        os.path.join(rgbout_dir, "wind_speed.jpg"),
    ])

    valid_image = next((p for p in candidate_images if os.path.exists(p)), None)

    if valid_image and HAS_MEMBER2_MODULE and not json_path:
        print(f"\n[Member 2] Loading NASA image from: {valid_image}")
        pixels = m2.load_image_rgb(valid_image)
        grid_results = m2.extract_grid_colors(pixels, grid_rows=5, grid_cols=5)

        # Output folder for Member 2 visual artifacts
        output_dir = os.path.join(rgbout_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        m2.save_results(grid_results, os.path.join(output_dir, "wind_grid_data.json"))
        m2.create_grid_overlay(pixels, grid_results, os.path.join(output_dir, "wind_grid_overlay.png"))
        m2.create_color_palette(grid_results, os.path.join(output_dir, "wind_color_palette.png"))
        print("[Member 2] Image grid processing and visual overlays completed successfully.")

    # Mode B: Load from Member 2's extracted JSON
    if grid_results is None:
        valid_json = json_path if (json_path and os.path.exists(json_path)) else m3.find_member2_json(current_dir)

        if valid_json:
            print(f"\n[Member 2] Loading existing grid JSON: {valid_json}")
            grid_results = m3.load_member2_json(valid_json)
            print(f"[Member 2] Loaded {len(grid_results)} grid cells.")
        elif os.path.exists("extracted_regions.csv"):
            print("\n[Member 2] Fallback: Loading extracted regions from 'extracted_regions.csv'...")
            grid_results = m3.load_extracted_regions_from_csv("extracted_regions.csv")
        else:
            print("\n[Member 2] Fallback: Using sample extracted regions...")
            grid_results = m3.SAMPLE_EXTRACTED_REGIONS

    # 3. Scientific Mapping (Member 3)
    rgb_mode_str = "Median RGB" if use_median else "Mean RGB"
    print(f"\n[Member 3] Mapping {len(grid_results)} cells to scientific windspeeds using {rgb_mode_str}...")
    mapped_results = m3.process_extracted_regions(grid_results, legend=legend, use_median=use_median)

    # 4. Statistical Analysis
    stats = m3.calculate_windspeed_statistics(mapped_results)

    # 5. Display Formatted Results Table
    m3.display_results_table(mapped_results, stats)

    # 6. Export for Member 4 (Sound Synthesis) and Member 5 (Interactive UI)
    csv_out = os.path.join(current_dir, "windspeed_output_for_member4.csv")
    json_out = os.path.join(current_dir, "windspeed_grid_mapped.json")

    m3.export_to_csv(mapped_results, csv_out)
    m3.export_to_json(mapped_results, json_out, stats=stats)

    print("\n" + "=" * 80)
    print("PIPELINE EXPORT COMPLETED:")
    print(f"  -> For Member 4 (Sound Synthesis): {csv_out}")
    print(f"  -> For Member 5 (UI & Playback)  : {json_out}")
    print("=" * 80 + "\n")

    return mapped_results, stats


def parse_args():
    parser = argparse.ArgumentParser(
        description="Integrated Pipeline: Member 2 (Image Grid Extraction) -> Member 3 (Windspeed Mapping)"
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Path to raw NASA windspeed image to process with Member 2"
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Path to pre-extracted Member 2 grid JSON (e.g. rgbout/wind_grid_data.json)"
    )
    parser.add_argument(
        "--use-median",
        action="store_true",
        help="Use median RGB values for matching instead of mean RGB"
    )
    parser.add_argument(
        "--legend",
        type=str,
        default="nasa_legend.csv",
        help="Path to NASA legend CSV"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        image_path=args.image,
        json_path=args.json,
        use_median=args.use_median,
        legend_path=args.legend
    )
