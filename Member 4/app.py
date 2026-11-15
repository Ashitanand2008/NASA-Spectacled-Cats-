"""NASA Wind Data Sonification — Member 4 Demonstration Interface.

Minimal, accessible Streamlit interface that accepts pre-extracted numerical
windspeed data from a JSON file, synthesizes musical pitch tones according to
the defined demonstrative scale, and provides native audio playback alongside
plain-text screen-reader-friendly descriptions and an audio legend.
"""

from __future__ import annotations

import streamlit as st

import sonification

MAX_UPLOAD_SIZE_BYTES = 1024 * 1024  # 1 MB maximum upload limit

# Page configuration
st.set_page_config(
    page_title="NASA Wind Data Sonification — Member 4",
    layout="centered",
)

# 1. Main Heading
st.title("NASA Wind Data Sonification — Member 4")

# 2. Context & Accessible Explanation
st.write(
    "This accessible interface sonifies numerical windspeed values pre-extracted by our "
    "team's scientific visualization pipeline. Higher musical pitches correspond to higher "
    "windspeed categories according to our demonstrative scale. Upload a JSON file containing "
    "the ordered region speed data to generate and listen to the audio sequence."
)

# 3. JSON File Uploader
uploaded_file = st.file_uploader(
    label="Upload JSON wind data file (maximum 1 MB)",
    type=["json"],
    help="Select a JSON file containing 'unit': 'm/s' and an ordered list of 'regions'.",
)

# Maintain state when file identity changes
if "last_uploaded_name" not in st.session_state:
    st.session_state["last_uploaded_name"] = None
    st.session_state["audio_bytes"] = None
    st.session_state["descriptions"] = None

if uploaded_file is None:
    st.session_state["last_uploaded_name"] = None
    st.session_state["audio_bytes"] = None
    st.session_state["descriptions"] = None
elif uploaded_file.name != st.session_state["last_uploaded_name"]:
    st.session_state["last_uploaded_name"] = uploaded_file.name
    st.session_state["audio_bytes"] = None
    st.session_state["descriptions"] = None

# 4. Generate Audio Button
can_generate = uploaded_file is not None
generate_clicked = st.button("Generate audio", disabled=not can_generate)

if not can_generate:
    st.info("Please upload a valid JSON wind data file to enable audio generation.")

if generate_clicked and uploaded_file is not None:
    # Check upload size limit
    file_bytes = uploaded_file.getvalue()
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        st.error(
            f"The uploaded file is {len(file_bytes):,} bytes, which exceeds the 1 MB (1,048,576 bytes) limit."
        )
    else:
        try:
            # Parse and validate the JSON payload
            validated_regions = sonification.parse_payload(file_bytes)

            # Synthesize WAV audio bytes and generate readable descriptions
            audio_data = sonification.sonify(validated_regions)
            descriptions = sonification.describe(validated_regions)

            # Save in session state so playback persists across safe reruns
            st.session_state["audio_bytes"] = audio_data
            st.session_state["descriptions"] = descriptions

        except ValueError as err:
            st.error(f"Input Validation Error: {err}")
        except Exception:
            # Guard against unexpected technical crashes; present friendly message
            st.error(
                "An unexpected error occurred while processing the file. "
                "Please verify that the file contains standard UTF-8 JSON."
            )

# 5. Native Streamlit Audio Player & Accessible Output
if st.session_state.get("audio_bytes"):
    st.success("WAV audio created successfully.")

    st.subheader("Audio Playback")
    # Native player, no autoplay
    st.audio(st.session_state["audio_bytes"], format="audio/wav", autoplay=False)

    st.subheader("Sequential Region Data")
    st.write("Ordered sequence of regions and corresponding sonification notes:")
    for desc_line in st.session_state["descriptions"]:
        st.write(desc_line)

# 6. Audio Mapping Legend
st.subheader("Audio Mapping Legend")
st.write(
    "Demonstrative 5-tier musical mapping scale (ordered from lowest to highest pitch):"
)
for item in sonification.get_audio_legend():
    st.write(
        f"• {item['range']}: Note {item['note']} ({item['frequency_hz']:.2f} Hz) — Category: {item['category']}"
    )

# 7. Honest Accessibility Statement
st.caption(
    "Accessibility Note: Musical pitch provides category-level auditory orientation, not exact "
    "measurements. Exact numerical values are provided in the sequential text above for screen-reader "
    "accessibility. This prototype does not generate synthetic spoken voice narration. User testing with "
    "blind and low-vision individuals is required before deploying this module as an assistive tool."
)
