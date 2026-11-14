# NASA Windspeed Image-to-Sound Converter
## Member 3: Scientific Value Mapping and Data Analysis Module

This module serves as the scientific analysis engine for the 5-member project. It bridges image analysis (Member 2) and sound synthesis (Member 4) by converting extracted RGB color values into approximate scientific windspeed values (m/s) based on a calibrated NASA color legend (researched by Member 1).

---

## 1. How the Program Works

The module follows a straightforward 5-stage pipeline:

1. **Legend Definition / Calibration**:
   - Stores color points from the scientific legend, mapping each RGB color `(R, G, B)` to an approximate windspeed in meters per second (`m/s`).
   - Supports both an in-memory illustrative legend and external CSV loading (`nasa_legend.csv`).
2. **Receiving Regional Color Inputs**:
   - Accepts image region coordinates, names, and RGB values extracted by Member 2 (`extracted_regions.csv` or Python list/dict).
3. **Euclidean Color Matching**:
   - Instead of complex machine learning, it measures the Euclidean distance in 3D color space:
     $$\text{distance} = \sqrt{(R_{\text{extracted}} - R_{\text{legend}})^2 + (G_{\text{extracted}} - G_{\text{legend}})^2 + (B_{\text{extracted}} - B_{\text{legend}})^2}$$
   - Compares the extracted pixel against every color in the legend to find the closest match.
4. **Tolerance & Reliability Handling**:
   - Matches with distance $\le 25$ are marked **High Confidence**.
   - Matches with distance between $25$ and $75$ are marked **Moderate (Approximate)**.
   - Matches with distance $> 75$ are flagged as **Low / Potential Non-Data (Land/Cloud)**.
5. **Statistical Analysis & Sound CSV Export**:
   - Calculates the minimum, maximum, and average windspeed across all regions (and ocean-only reliable regions).
   - Exports the structured dataset to `windspeed_output_for_member4.csv` so Member 4 can directly map windspeeds to musical pitches/frequencies.

---

## 2. Requirements & Installation

The script is built with pure standard Python 3 and runs out of the box with **zero required external libraries**.

### Optional Performance Acceleration:
If you want to use NumPy for array operations:
```bash
pip install numpy
```
*(The script automatically detects NumPy if present; if not installed, it falls back seamlessly to Python's standard `math` module.)*

---

## 3. Running the Program

### Option A: Run Member 3 Mapper (Auto-detects Member 2 JSON / CSV)
```bash
python windspeed_mapper.py
```
*Automatically detects `rgbout/wind_grid_data.json` if present, falls back to `extracted_regions.csv`, and outputs `windspeed_output_for_member4.csv` and `windspeed_grid_mapped.json`.*

### Option B: Run Integrated End-to-End Pipeline (Member 2 + Member 3)
```bash
# Process pre-extracted grid JSON
python integrated_pipeline.py

# Process raw NASA image directly through Member 2 & 3
python integrated_pipeline.py --image path/to/wind_image.jpg

# Use median RGB matching instead of mean RGB
python integrated_pipeline.py --use-median
```

---

## 4. How Other Team Members Connect to Member 3

- **Member 1 (NASA Legend Research)**:
  - Populate or edit `nasa_legend.csv` with the actual NASA scientific colormap values:
    ```csv
    color_name,r,g,b,windspeed_mps
    Deep Blue,20,40,160,2.5
    Cyan / Light Blue,40,180,220,7.0
    ...
    ```
- **Member 2 (Image & Grid Color Extraction)**:
  - **Grid JSON format** (Primary):
    Place `wind_grid_data.json` inside `rgbout/`. Contains 5x5 grid cells with bounding boxes and `mean_rgb`/`median_rgb`.
    ```python
    from windspeed_mapper import load_member2_json, process_extracted_regions
    cells = load_member2_json("rgbout/wind_grid_data.json")
    results = process_extracted_regions(cells)
    ```
  - **CSV format** (Secondary):
    Export regions to `extracted_regions.csv`:
    ```csv
    region_id,region_name,r,g,b
    REG_001,Calm Tropical Zone,22,45,155
    ...
    ```
- **Member 4 (Sound Synthesis)**:
  - Read `windspeed_output_for_member4.csv` directly into the sound generation script:
    ```python
    import csv
    with open("windspeed_output_for_member4.csv", mode="r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            speed = float(row["windspeed_mps"])
            # Member 4 maps speed to frequency / pitch (e.g. 200 Hz to 1000 Hz)
    ```
- **Member 5 (User Interface & Integration)**:
  - Read `windspeed_grid_mapped.json` which provides cell bounding boxes (`bbox`), cell coordinates, and windspeed for interactive hover/clicking on the NASA image!
  - Or for real-time hover inspection:
    ```python
    from windspeed_mapper import map_single_rgb
    speed = map_single_rgb(r=55, g=195, b=75)
    print(f"Windspeed at cursor: {speed} m/s")
    ```

---

## 5. CSV Output Format for Member 4

The exported file `windspeed_output_for_member4.csv` provides clean columns:

| Column Name | Type | Description |
|---|---|---|
| `region_id` | String | Unique identifier (e.g., `CELL_01`) |
| `region_name` | String | Descriptive region label (e.g., `Grid Cell (R0, C0)`) |
| `extracted_r` | Integer | Red channel from NASA image (0-255) |
| `extracted_g` | Integer | Green channel from NASA image (0-255) |
| `extracted_b` | Integer | Blue channel from NASA image (0-255) |
| `matched_color` | String | Closest color name from the NASA legend |
| `windspeed_mps` | Float | Estimated windspeed in meters per second |
| `color_distance` | Float | Euclidean distance from legend entry |
| `confidence` | String | Match reliability rating |
| `grid_row` | Integer | Optional 5x5 grid row index (0-4) |
| `grid_col` | Integer | Optional 5x5 grid column index (0-4) |
