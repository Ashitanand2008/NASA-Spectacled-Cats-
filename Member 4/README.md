# NASA Accessible Wind-Data Sonification — Member 4

> **NASA Scientific Visualisation Sonification Project**  
> *Member 4 Module: Input Validation, Auditory Pitch Mapping, WAV Synthesis, and Accessible Interface*

---

## 1. What This Project Does & Team Boundaries

### The Problem
NASA publishes visual wind data, satellite imagery, and animated atmospheric maps. Visualizations alone are inaccessible to blind, low-vision, and visually impaired individuals. Our 5-member team is developing a pipeline that converts visual NASA representations into accessible auditory signals.

### Team Responsibilities & System Architecture
```
[NASA Visualization]
        │
        ▼
   Member 1: Selects NASA imagery, legend calibration, units, provenance
        │
        ▼
   Member 2: Image processing, color extraction, regional segmentation
        │
        ▼
   Member 3: Interprets calibrated colors -> outputs ordered JSON windspeed (m/s)
        │
        ▼
★ MEMBER 4 (This Module):
   1. Validates numerical windspeed input according to strict schema
   2. Maps numerical speeds to musical frequencies (C4 to C5)
   3. Synthesizes clean 16-bit PCM WAV audio in memory
   4. Provides an accessible Streamlit UI demo and clean Python API
        │
        ▼
   Member 5: Integrates Member 4's engine into the team's final application
```

### What Member 4 IS Responsible For
- Validating ordered numerical windspeed inputs (0 to 25 m/s, unit `m/s`).
- Deterministic audio synthesis (pure sine waves, 44.1 kHz, smooth fades, 16-bit PCM WAV).
- Providing public functions `sonify()`, `describe()`, and `parse_payload()`.
- Providing an accessible demonstration interface in Streamlit (`app.py`).
- Automated unit and UI testing suite with 100% test passage.

### What Member 4 IS NOT Responsible For
- NASA image, video, or optical flow analysis (handled by Members 1–3).
- Live NASA network API queries or satellite downloads.
- AI/ML inference or computer vision libraries like OpenCV or Pillow.
- User accounts, databases, cloud storage, payment systems, or maps.
- Music generation, voice narration, or decorative UI controls.

---

## 2. Beginner's Glossary: Audio & Scientific Terms

If you are new to audio programming, here is what each term means in simple English:

- **Sonification**: The practice of using non-speech audio to convey data or perceptual information. Just as graphs turn numbers into shapes, sonification turns numbers into sounds.
- **Windspeed (m/s)**: Wind speed measured in metres per second. $1\text{ m/s} \approx 3.6\text{ km/h} \approx 2.24\text{ mph}$.
- **Sine Wave**: The simplest, purest acoustic waveform containing only one single frequency with no harmonic overtones.
- **Pitch**: How "high" or "low" a musical note sounds to the human ear. A higher frequency vibrates faster and sounds higher in pitch.
- **Hertz (Hz)**: The unit of frequency, representing cycles (vibrations) per second. For example, $261.63\text{ Hz}$ means the wave oscillates 261.63 times every second.
- **Sampling Rate (44,100 Hz)**: The number of audio snapshots taken per second to reconstruct digital sound. 44,100 Hz is the worldwide standard for CD-quality audio.
- **16-bit PCM WAV**: Linear Pulse Code Modulation formatted as a standard Windows `.wav` file. 16-bit means each sound sample is represented by an integer between -32,768 and +32,767.

---

## 3. The Sonification Scale & Frequency Mapping

The sonification scale maps windspeeds from $0\text{ to }25\text{ m/s}$ into 5 discrete categories.

> **Important Note:** This is an **illustrative demonstrative scale** designed for prototype accessibility testing, not an official NASA storm classification.

| Speed Range (m/s) | Note | Frequency (Hz) | Category Label | Musical Description |
| :--- | :---: | :---: | :---: | :--- |
| **0.0 <= speed < 5.0** | **C4** | **261.63 Hz** | `Very low` | Middle C (deepest tone in our scale) |
| **5.0 <= speed < 10.0** | **D4** | **293.66 Hz** | `Low` | One whole tone above C4 |
| **10.0 <= speed < 15.0** | **E4** | **329.63 Hz** | `Moderate` | Major third above C4 |
| **15.0 <= speed < 20.0** | **G4** | **392.00 Hz** | `High` | Perfect fifth above C4 |
| **20.0 <= speed <= 25.0** | **C5** | **523.25 Hz** | `Very high` | High C (one octave above C4) |

### Acoustic Specifications
- **Tone Duration**: Exactly `0.45 seconds` per region.
- **Inter-tone Gap**: Exactly `0.08 seconds` of silence between regions (no gap after final tone).
- **Fade Ramps**: Smooth `10 ms` linear ramp at the start (fade-in) and end (fade-out) of every tone to prevent acoustic clicks or pops.
- **Peak Amplitude**: Approximately `0.20` of full scale (~6,553 in 16-bit PCM) to ensure pleasant listening without digital clipping.

---

## 4. Windows Command Prompt (CMD) Setup & Execution

Follow these step-by-step commands using the standard Windows Command Prompt (`cmd.exe`).

### Step 1: Open Command Prompt and Navigate to the Folder
Because the folder path contains a space (`NASA PROJECT`), you **must enclose the entire path in double quotation marks**:

```cmd
cd /d "C:\Users\a\OneDrive\Desktop\NASA PROJECT\antigravity"
```

### Step 2: Virtual Environment Verification
A virtual environment (`.venv`) is already configured in this folder. If you ever need to recreate it from scratch using Python 3.14:

```cmd
py -3.14 -m venv --system-site-packages .venv
```
*(If `py` is not recognized, use the full path: `"C:\Program Files\Python314\python.exe" -m venv --system-site-packages .venv`)*

### Step 3: Verify / Install Dependencies
Install or verify project requirements:

```cmd
.venv\Scripts\python.exe -m pip install -r requirements.txt
```
> **Note on pip upgrades:** You do **not** need to upgrade `pip` for this project to work. The installed version is fully compatible.

### Step 4: Run the Automated Tests
Run the 21 automated unit, DSP, and interface tests:

```cmd
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### Step 5: Run the Standalone Command-Line Demo
Generate a sample WAV file directly without launching a web browser:

```cmd
.venv\Scripts\python.exe sonification.py
```
This reads `examples/sample_regions.json` and creates `outputs/sample_wind_audio.wav`.

### Step 6: Launch the Streamlit Accessible Web Application
Start the accessible local web demo:

```cmd
.venv\Scripts\python.exe -m streamlit run app.py
```
Streamlit will output local URLs. Open your browser to:
```
http://localhost:8501
```

---

## 5. Setting Up in PyCharm

1. Open **PyCharm**.
2. Click **File** -> **Open...** and select:
   `C:\Users\a\OneDrive\Desktop\NASA PROJECT\antigravity`
3. Configure the Python Interpreter:
   - Go to **File** -> **Settings** (or press `Ctrl + Alt + S`).
   - Navigate to **Project: antigravity** -> **Python Interpreter**.
   - Click **Add Interpreter** -> **Add Local Interpreter...**
   - Select **Existing**, click **...** (browse), and choose:
     `C:\Users\a\OneDrive\Desktop\NASA PROJECT\antigravity\.venv\Scripts\python.exe`
   - Click **OK** -> **Apply**.
4. In PyCharm's built-in terminal or run configuration:
   - Run `sonification.py` to test standalone synthesis.
   - Run `tests/test_sonification.py` to run tests.
   - Run terminal command `.venv\Scripts\python.exe -m streamlit run app.py` for the web app.

---

## 6. Input Data Schema (Contract with Member 3)

The input file must be standard UTF-8 JSON.

### Canonical Example (`examples/sample_regions.json`)
```json
{
  "unit": "m/s",
  "regions": [
    {"region": "A", "speed": 3},
    {"region": "B", "speed": 7},
    {"region": "C", "speed": 12},
    {"region": "D", "speed": 18},
    {"region": "E", "speed": 23}
  ]
}
```

### Strict Validation Rules
1. `"unit"` must be present and equal to `"m/s"`.
2. `"regions"` must be an ordered array with between 1 and 100 entries.
3. Each entry must have `"region"` (a string between 1 and 80 characters) and `"speed"` (a finite number between 0.0 and 25.0).
4. **Disallowed**: Booleans (`true`/`false`), numeric strings (`"12"`), negative numbers, values `> 25.0`, `NaN`, `infinity`, or missing fields.

### Common Errors & Fixes
| Error Message | Cause | How to Fix |
| :--- | :--- | :--- |
| `Unsupported unit 'km/h'` | Unit is not `m/s` | Change `"unit": "km/h"` to `"unit": "m/s"` (or convert values to m/s first). |
| `Missing required key 'regions'` | Wrong JSON structure | Ensure the root object has a `"regions"` list key. |
| `speed must be a numeric value, got bool` | Boolean in speed field | Use numbers like `0` or `5`, never `true` or `false`. |
| `speed 28.5 m/s exceeds max scale of 25.0 m/s` | Value above scale | Check calibration. Values must be $\le 25\text{ m/s}$ in this prototype. |
| `The 'regions' list is empty` | 0 regions provided | Provide at least 1 region entry. |

---

## 7. How Member 5 Integrates This Module

Member 5 can import `sonify()` and `describe()` directly into the main application without depending on the demonstration UI:

```python
from sonification import sonify, describe, parse_payload
import streamlit as st

# Option A: Member 5 already has the validated list of regions
regions = [
    {"region": "A", "speed": 3.0},
    {"region": "B", "speed": 12.0},
    {"region": "C", "speed": 23.0},
]

# Synthesize 16-bit PCM WAV audio bytes
audio_bytes = sonify(regions)

# Display in Streamlit or any web/desktop player
st.audio(audio_bytes, format="audio/wav")

# Display screen-reader-friendly text lines
for line in describe(regions):
    st.write(line)

# Option B: Member 5 receives raw JSON payload from Member 3
raw_json = '{"unit": "m/s", "regions": [{"region": "A", "speed": 4}]}'
regions = parse_payload(raw_json)
audio_bytes = sonify(regions)
```

---

## 8. Accessibility Limitations & Scientific Caveats

1. **Category vs. Precision**: Musical pitch gives categorical orientation (e.g. "Low" vs "Very high"). It does not represent exact numerical values down to decimals. Screen-reader text is displayed alongside audio so users can access exact numbers.
2. **No Live Spoken Voice**: This version synthesizes musical sine tones. It does not synthesize spoken speech ("Region A, 3 metres per second").
3. **Calibration Dependency**: Sonification cannot derive real windspeeds from uncalibrated image colors. The accuracy depends entirely on Member 1's legend and Member 3's calibration.
4. **User Testing Required**: Before this system is used as a formal assistive aid, real user testing with blind and low-vision individuals must be conducted.

---

## 9. Future Extension: Speeds Greater Than 25 m/s

If future NASA storm/hurricane imagery exhibits windspeeds exceeding $25\text{ m/s}$ (such as Category 1–5 hurricanes up to $70+\text{ m/s}$):
1. **Never silently clamp or wrap values**. That would misrepresent dangerous weather.
2. Extend `SCALE_MAPPING` in `sonification.py` with additional non-overlapping intervals (e.g. $25\text{ to }35\text{ m/s} \rightarrow \text{E5}$, $35\text{ to }50\text{ m/s} \rightarrow \text{G5}$).
3. Update `MAX_SPEED_MPS` constant.
4. Update tests and UI legends accordingly.
