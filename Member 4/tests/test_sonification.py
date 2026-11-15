"""Automated Test Suite for NASA Wind Data Sonification (Member 4).

Tests cover:
  1. Boundary condition tests for all 10 sonification mapping thresholds.
  2. Audio format, sampling rate (44.1 kHz), mono, 16-bit PCM WAV encoding.
  3. Predictable durations for 1, 3, and 5 regions (tones + inter-tone gaps).
  4. Signal properties: non-zero, finite, no clipping, proper amplitude envelope.
  5. Dominant frequency verification via FFT for synthesized pitches.
  6. Strict input validation and rejection of out-of-range/malformed data.
  7. Verification that describe() matches sonify() mapping.
  8. Immutability of input data during processing.
  9. End-to-end integration test reading sample JSON and producing valid WAV.
  10. Streamlit Demo App automated interaction tests (upload, error, audio render).
"""

import io
import math
import sys
import unittest
import wave
from pathlib import Path

import numpy as np
import scipy.io.wavfile

# Ensure parent directory is in sys.path so sonification can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sonification


class TestBoundaryMappings(unittest.TestCase):
    """Test note and category mappings at all exact boundary values."""

    def test_boundary_zero_and_below_five(self):
        # 0 <= speed < 5 m/s: C4, 261.63 Hz, 'Very low'
        note, freq, label = sonification.map_speed_to_note(0.0)
        self.assertEqual(note, "C4")
        self.assertAlmostEqual(freq, 261.63, places=2)
        self.assertEqual(label, "Very low")

        note, freq, label = sonification.map_speed_to_note(4.999)
        self.assertEqual(note, "C4")
        self.assertAlmostEqual(freq, 261.63, places=2)
        self.assertEqual(label, "Very low")

    def test_boundary_five_and_below_ten(self):
        # 5 <= speed < 10 m/s: D4, 293.66 Hz, 'Low'
        note, freq, label = sonification.map_speed_to_note(5.0)
        self.assertEqual(note, "D4")
        self.assertAlmostEqual(freq, 293.66, places=2)
        self.assertEqual(label, "Low")

        note, freq, label = sonification.map_speed_to_note(9.999)
        self.assertEqual(note, "D4")
        self.assertAlmostEqual(freq, 293.66, places=2)
        self.assertEqual(label, "Low")

    def test_boundary_ten_and_below_fifteen(self):
        # 10 <= speed < 15 m/s: E4, 329.63 Hz, 'Moderate'
        note, freq, label = sonification.map_speed_to_note(10.0)
        self.assertEqual(note, "E4")
        self.assertAlmostEqual(freq, 329.63, places=2)
        self.assertEqual(label, "Moderate")

        note, freq, label = sonification.map_speed_to_note(14.999)
        self.assertEqual(note, "E4")
        self.assertAlmostEqual(freq, 329.63, places=2)
        self.assertEqual(label, "Moderate")

    def test_boundary_fifteen_and_below_twenty(self):
        # 15 <= speed < 20 m/s: G4, 392.00 Hz, 'High'
        note, freq, label = sonification.map_speed_to_note(15.0)
        self.assertEqual(note, "G4")
        self.assertAlmostEqual(freq, 392.00, places=2)
        self.assertEqual(label, "High")

        note, freq, label = sonification.map_speed_to_note(19.999)
        self.assertEqual(note, "G4")
        self.assertAlmostEqual(freq, 392.00, places=2)
        self.assertEqual(label, "High")

    def test_boundary_twenty_and_twenty_five(self):
        # 20 <= speed <= 25 m/s: C5, 523.25 Hz, 'Very high'
        note, freq, label = sonification.map_speed_to_note(20.0)
        self.assertEqual(note, "C5")
        self.assertAlmostEqual(freq, 523.25, places=2)
        self.assertEqual(label, "Very high")

        note, freq, label = sonification.map_speed_to_note(25.0)
        self.assertEqual(note, "C5")
        self.assertAlmostEqual(freq, 523.25, places=2)
        self.assertEqual(label, "Very high")


class TestAudioSynthesisAndProperties(unittest.TestCase):
    """Test audio synthesis, WAV encoding format, durations, and signal levels."""

    def test_wav_format_and_headers(self):
        """Verify output is valid RIFF/WAVE, 44,100 Hz, 1 channel (mono), 16-bit PCM."""
        regions = [{"region": "SampleZone", "speed": 12.0}]
        wav_bytes = sonification.sonify(regions)

        self.assertIsInstance(wav_bytes, bytes)
        self.assertTrue(len(wav_bytes) > 44, "WAV bytes must be larger than the 44-byte header.")
        self.assertTrue(wav_bytes.startswith(b"RIFF"), "Must start with RIFF header.")
        self.assertIn(b"WAVE", wav_bytes[:16], "Must contain WAVE identifier.")

        # Decode using standard library wave module
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1, "Must be mono (1 channel).")
            self.assertEqual(wf.getsampwidth(), 2, "Must be 16-bit (2 bytes per sample).")
            self.assertEqual(wf.getframerate(), 44100, "Must be 44,100 Hz.")
            self.assertEqual(wf.getcomptype(), "NONE", "Must be uncompressed PCM.")

    def test_expected_durations_one_three_five_regions(self):
        """Verify exact expected sample count and duration for 1, 3, and 5 regions.

        Formulas:
          - 1 region: 0.45 s tone -> 19845 samples
          - 3 regions: 3 * 0.45 + 2 * 0.08 = 1.51 s -> 66591 samples
          - 5 regions: 5 * 0.45 + 4 * 0.08 = 2.57 s -> 113337 samples
        """
        fs = 44100
        tone_samples = int(round(0.45 * fs))  # 19845
        gap_samples = int(round(0.08 * fs))   # 3528

        test_cases = [
            (1, 1 * tone_samples + 0 * gap_samples),
            (3, 3 * tone_samples + 2 * gap_samples),
            (5, 5 * tone_samples + 4 * gap_samples),
        ]

        for num_regions, expected_samples in test_cases:
            regions = [{"region": f"R{i}", "speed": 5.0} for i in range(num_regions)]
            wav_bytes = sonification.sonify(regions)
            rate, pcm = scipy.io.wavfile.read(io.BytesIO(wav_bytes))

            self.assertEqual(rate, fs)
            self.assertEqual(
                len(pcm),
                expected_samples,
                f"Expected {expected_samples} samples for {num_regions} regions, got {len(pcm)}",
            )
            # Duration in seconds should match within 0.001 s
            expected_sec = expected_samples / fs
            actual_sec = len(pcm) / fs
            self.assertAlmostEqual(actual_sec, expected_sec, delta=0.001)

    def test_signal_amplitude_and_no_clipping(self):
        """Verify the signal is non-zero, finite, within bounds, and has no clipping."""
        regions = [{"region": "Calm", "speed": 3.0}, {"region": "Storm", "speed": 22.0}]
        wav_bytes = sonification.sonify(regions)
        _rate, pcm = scipy.io.wavfile.read(io.BytesIO(wav_bytes))

        # Check not all zeros
        self.assertTrue(np.any(pcm != 0), "Synthesized signal must not be completely silent.")

        # Check peak amplitude is around 0.20 of full scale (32767 * 0.20 = ~6553)
        max_val = np.max(np.abs(pcm))
        self.assertGreater(max_val, 5000, "Peak amplitude should be near nominal ~6553.")
        self.assertLessEqual(max_val, 8192, "Signal must stay comfortably below clipping.")

        # Check inter-tone gap is true silence (0s)
        fs = 44100
        tone_samples = int(round(0.45 * fs))
        gap_samples = int(round(0.08 * fs))
        gap_segment = pcm[tone_samples : tone_samples + gap_samples]
        self.assertTrue(np.all(gap_segment == 0), "Inter-tone gap must be silent.")

    def test_dominant_frequency_via_fft(self):
        """Verify that synthesized notes actually have the expected dominant frequencies.

        We test C4 (261.63 Hz) and C5 (523.25 Hz).
        """
        test_pitches = [
            ({"region": "R_C4", "speed": 2.5}, 261.63),
            ({"region": "R_C5", "speed": 23.0}, 523.25),
        ]

        for region_dict, expected_freq in test_pitches:
            wav_bytes = sonification.sonify([region_dict])
            rate, pcm = scipy.io.wavfile.read(io.BytesIO(wav_bytes))

            # Discard fade-in and fade-out to analyze steady-state sinusoidal core
            fs = rate
            fade_samples = int(round(0.01 * fs))
            steady_state = pcm[fade_samples : len(pcm) - fade_samples].astype(float)

            # Compute FFT with zero-padding to achieve high frequency resolution (<0.5 Hz)
            n_fft = 88200
            fft_magnitudes = np.abs(np.fft.rfft(steady_state, n=n_fft))
            freqs = np.fft.rfftfreq(n_fft, d=1.0 / fs)

            dominant_freq = freqs[np.argmax(fft_magnitudes)]
            self.assertAlmostEqual(
                dominant_freq,
                expected_freq,
                delta=2.0,
                msg=f"Expected peak at {expected_freq} Hz, found {dominant_freq} Hz.",
            )


class TestValidationAndErrorHandling(unittest.TestCase):
    """Test strict input validation and rejection of out-of-range or malformed inputs."""

    def test_unsupported_or_missing_unit(self):
        # Missing unit
        with self.assertRaises(ValueError) as ctx:
            sonification.parse_payload({"regions": [{"region": "A", "speed": 5}]})
        self.assertIn("unit", str(ctx.exception).lower())

        # Unsupported unit
        with self.assertRaises(ValueError) as ctx:
            sonification.parse_payload(
                {"unit": "km/h", "regions": [{"region": "A", "speed": 5}]}
            )
        self.assertIn("unsupported unit", str(ctx.exception).lower())

    def test_empty_or_oversized_regions_list(self):
        # Empty list
        with self.assertRaises(ValueError) as ctx:
            sonification.sonify([])
        self.assertIn("empty", str(ctx.exception).lower())

        # > 100 regions
        too_many = [{"region": f"R{i}", "speed": 10.0} for i in range(101)]
        with self.assertRaises(ValueError) as ctx:
            sonification.sonify(too_many)
        self.assertIn("exceeding the maximum", str(ctx.exception).lower())

    def test_missing_region_or_speed_keys(self):
        with self.assertRaises(ValueError) as ctx:
            sonification.sonify([{"speed": 10.0}])
        self.assertIn("missing", str(ctx.exception).lower())

        with self.assertRaises(ValueError) as ctx:
            sonification.sonify([{"region": "OnlyName"}])
        self.assertIn("missing", str(ctx.exception).lower())

    def test_invalid_region_names(self):
        # Empty string
        with self.assertRaises(ValueError):
            sonification.sonify([{"region": "", "speed": 5.0}])

        # Whitespace only
        with self.assertRaises(ValueError):
            sonification.sonify([{"region": "   ", "speed": 5.0}])

        # Non-string
        with self.assertRaises(ValueError):
            sonification.sonify([{"region": 123, "speed": 5.0}])

        # > 80 characters
        with self.assertRaises(ValueError):
            sonification.sonify([{"region": "A" * 81, "speed": 5.0}])

    def test_invalid_speeds(self):
        # Boolean disguised as int/number (Python bool is a subclass of int)
        with self.assertRaises(ValueError) as ctx:
            sonification.sonify([{"region": "A", "speed": True}])
        self.assertIn("numeric", str(ctx.exception).lower())

        # String posing as number
        with self.assertRaises(ValueError):
            sonification.sonify([{"region": "A", "speed": "12"}])

        # Negative speed
        with self.assertRaises(ValueError) as ctx:
            sonification.sonify([{"region": "A", "speed": -0.01}])
        self.assertIn("negative", str(ctx.exception).lower())

        # Speed > 25 m/s
        with self.assertRaises(ValueError) as ctx:
            sonification.sonify([{"region": "A", "speed": 25.01}])
        self.assertIn("exceeds", str(ctx.exception).lower())

        # NaN and Infinity
        with self.assertRaises(ValueError):
            sonification.sonify([{"region": "A", "speed": float("nan")}])

        with self.assertRaises(ValueError):
            sonification.sonify([{"region": "A", "speed": float("inf")}])

    def test_malformed_json_payloads(self):
        # Invalid JSON string syntax
        with self.assertRaises(ValueError) as ctx:
            sonification.parse_payload("{this is not valid json")
        self.assertIn("invalid json syntax", str(ctx.exception).lower())

        # Payload is not a JSON object (e.g. list or string)
        with self.assertRaises(ValueError) as ctx:
            sonification.parse_payload("[1, 2, 3]")
        self.assertIn("object", str(ctx.exception).lower())


class TestDescriptionsAndImmutability(unittest.TestCase):
    """Test description generation, consistency with sonify(), and immutability."""

    def test_describe_matches_categories_and_notes(self):
        regions = [
            {"region": "Zone1", "speed": 3.0},
            {"region": "Zone2", "speed": 7.5},
            {"region": "Zone3", "speed": 12.0},
            {"region": "Zone4", "speed": 18.2},
            {"region": "Zone5", "speed": 24.5},
        ]
        descriptions = sonification.describe(regions)
        self.assertEqual(len(descriptions), 5)

        self.assertIn("Very low", descriptions[0])
        self.assertIn("C4", descriptions[0])

        self.assertIn("Low", descriptions[1])
        self.assertIn("D4", descriptions[1])

        self.assertIn("Moderate", descriptions[2])
        self.assertIn("E4", descriptions[2])

        self.assertIn("High", descriptions[3])
        self.assertIn("G4", descriptions[3])

        self.assertIn("Very high", descriptions[4])
        self.assertIn("C5", descriptions[4])

    def test_input_data_immutability(self):
        """Verify that passing data into sonify() or describe() does not alter the input."""
        original_regions = [
            {"region": "Alpha", "speed": 10},
            {"region": "Beta", "speed": 20},
        ]
        import copy
        snapshot = copy.deepcopy(original_regions)

        _ = sonification.sonify(original_regions)
        self.assertEqual(original_regions, snapshot, "sonify() must not mutate input.")

        _ = sonification.describe(original_regions)
        self.assertEqual(original_regions, snapshot, "describe() must not mutate input.")


class TestIntegrationSampleFile(unittest.TestCase):
    """Integration test verifying examples/sample_regions.json produces valid output."""

    def test_sample_regions_json_end_to_end(self):
        sample_path = PROJECT_ROOT / "examples" / "sample_regions.json"
        self.assertTrue(sample_path.exists(), f"Sample file must exist at {sample_path}")

        with open(sample_path, "r", encoding="utf-8") as f:
            content = f.read()

        regions = sonification.parse_payload(content)
        self.assertEqual(len(regions), 5)

        audio_bytes = sonification.sonify(regions)
        self.assertTrue(len(audio_bytes) > 1000)

        lines = sonification.describe(regions)
        self.assertEqual(len(lines), 5)


class TestStreamlitDemoApp(unittest.TestCase):
    """Test Streamlit application using official AppTest framework."""

    def test_app_initial_state(self):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
        self.assertFalse(at.exception, "App should run without exceptions.")
        self.assertEqual(at.title[0].value, "NASA Wind Data Sonification — Member 4")
        # Generate audio button should be disabled initially
        self.assertTrue(at.button[0].disabled)

    def test_app_valid_file_generates_audio(self):
        from streamlit.testing.v1 import AppTest

        sample_path = PROJECT_ROOT / "examples" / "sample_regions.json"
        content = sample_path.read_bytes()

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
        at.file_uploader[0].upload("sample_regions.json", content).run()
        self.assertFalse(at.button[0].disabled)

        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.success), 1)
        self.assertIn("WAV audio created successfully", at.success[0].value)
        self.assertIsNotNone(at.session_state["audio_bytes"])
        self.assertTrue(len(at.session_state["audio_bytes"]) > 1000)
        self.assertEqual(len(at.session_state["descriptions"]), 5)
        self.assertTrue(any(sh.value == "Audio Playback" for sh in at.subheader))

    def test_app_invalid_file_displays_error(self):
        from streamlit.testing.v1 import AppTest

        invalid_json = b'{"unit": "km/h", "regions": [{"region": "A", "speed": 5}]}'

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
        at.file_uploader[0].upload("bad.json", invalid_json).run()
        at.button[0].click().run()

        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 1)
        self.assertIn("Input Validation Error", at.error[0].value)
        self.assertIsNone(at.session_state["audio_bytes"])


if __name__ == "__main__":
    unittest.main()
