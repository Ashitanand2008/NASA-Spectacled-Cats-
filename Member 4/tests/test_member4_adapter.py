"""Unit and integration tests for Member 4 Extended Adapter.

Tests extended musical pitch mappings (25 to 40 m/s), FFT dominant frequencies,
Member 2/3 CSV/JSON ingestion, timing calculations, RIFF metadata embedding,
and export schema compliance.
"""

from __future__ import annotations

import io
import math
import sys
from pathlib import Path
import unittest
import wave

import numpy as np
import scipy.io.wavfile

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import member4_adapter
import sonification


class TestExtendedPitchMapping(unittest.TestCase):
    """Test boundary mappings for both base (0-25 m/s) and extended (25-40 m/s) scales."""

    def test_base_scale_boundaries_preserved(self):
        """Verify original Member 4 0-25 m/s mappings remain identical."""
        # C4: 0 <= speed < 5
        self.assertEqual(member4_adapter.map_speed_to_note_extended(0.0)[:2], ("C4", 261.63))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(4.999)[:2], ("C4", 261.63))

        # D4: 5 <= speed < 10
        self.assertEqual(member4_adapter.map_speed_to_note_extended(5.0)[:2], ("D4", 293.66))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(9.999)[:2], ("D4", 293.66))

        # E4: 10 <= speed < 15
        self.assertEqual(member4_adapter.map_speed_to_note_extended(10.0)[:2], ("E4", 329.63))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(14.999)[:2], ("E4", 329.63))

        # G4: 15 <= speed < 20
        self.assertEqual(member4_adapter.map_speed_to_note_extended(15.0)[:2], ("G4", 392.00))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(19.999)[:2], ("G4", 392.00))

        # C5: 20 <= speed <= 25
        self.assertEqual(member4_adapter.map_speed_to_note_extended(20.0)[:2], ("C5", 523.25))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(25.0)[:2], ("C5", 523.25))

    def test_extended_scale_boundaries(self):
        """Verify extended prototype tiers: D5 (25-30), E5 (30-35), G5 (35-40)."""
        # D5: 25 < speed < 30
        self.assertEqual(member4_adapter.map_speed_to_note_extended(25.001)[:2], ("D5", 587.33))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(26.5)[:2], ("D5", 587.33))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(29.999)[:2], ("D5", 587.33))

        # E5: 30 <= speed < 35
        self.assertEqual(member4_adapter.map_speed_to_note_extended(30.0)[:2], ("E5", 659.25))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(32.0)[:2], ("E5", 659.25))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(34.999)[:2], ("E5", 659.25))

        # G5: 35 <= speed <= 40
        self.assertEqual(member4_adapter.map_speed_to_note_extended(35.0)[:2], ("G5", 783.99))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(38.0)[:2], ("G5", 783.99))
        self.assertEqual(member4_adapter.map_speed_to_note_extended(40.0)[:2], ("G5", 783.99))

    def test_out_of_range_rejections(self):
        """Verify speeds < 0 or > 40 m/s and non-numerics are rejected."""
        with self.assertRaises(ValueError):
            member4_adapter.map_speed_to_note_extended(-0.1)

        with self.assertRaises(ValueError):
            member4_adapter.map_speed_to_note_extended(40.01)

        with self.assertRaises(ValueError):
            member4_adapter.map_speed_to_note_extended(float("nan"))

        with self.assertRaises(ValueError):
            member4_adapter.map_speed_to_note_extended(float("inf"))

        with self.assertRaises(ValueError):
            member4_adapter.map_speed_to_note_extended(True)


class TestFFTDominantFrequencyExtended(unittest.TestCase):
    """Verify that synthesized extended notes actually have the expected dominant frequencies via FFT."""

    def test_extended_pitches_dominant_frequency(self):
        test_cases = [
            ("D5", 26.5, 587.33),
            ("E5", 32.0, 659.25),
            ("G5", 38.0, 783.99),
        ]
        for note_name, speed, expected_freq in test_cases:
            records = [{"region_id": f"R_{note_name}", "speed": speed}]
            parsed = member4_adapter.parse_windspeed_records(records)
            wav_bytes, _ = member4_adapter.sonify_records(parsed, embed_metadata=False)

            rate, pcm = scipy.io.wavfile.read(io.BytesIO(wav_bytes))
            self.assertEqual(rate, 44100)

            # Analyze steady-state core (ignore 10ms fades)
            fade_samples = int(round(0.01 * rate))
            steady_state = pcm[fade_samples : len(pcm) - fade_samples].astype(float)

            n_fft = 88200
            fft_magnitudes = np.abs(np.fft.rfft(steady_state, n=n_fft))
            freqs = np.fft.rfftfreq(n_fft, d=1.0 / rate)

            dominant_freq = freqs[np.argmax(fft_magnitudes)]
            self.assertAlmostEqual(
                dominant_freq,
                expected_freq,
                delta=2.0,
                msg=f"Expected {note_name} dominant at {expected_freq} Hz, measured {dominant_freq} Hz.",
            )


class TestMultiFormatIngestion(unittest.TestCase):
    """Test ingestion of Member 2/3 CSV, Member 2/3 JSON, and Member 4 JSON formats."""

    def test_ingest_sample_member3_export_csv(self):
        csv_path = PROJECT_ROOT / "examples" / "sample_member3_export.csv"
        records = member4_adapter.parse_windspeed_records(csv_path)

        self.assertEqual(len(records), 7)
        self.assertEqual(records[0]["region_id"], "CELL_01")
        self.assertEqual(records[0]["windspeed_mps"], 2.5)
        self.assertEqual(records[0]["note"], "C4")
        self.assertEqual(records[0]["grid_row"], 0)
        self.assertEqual(records[0]["grid_col"], 0)

        # Check extended item (CELL_21 with 38.0 m/s)
        rec21 = next(r for r in records if r["region_id"] == "CELL_21")
        self.assertEqual(rec21["windspeed_mps"], 38.0)
        self.assertEqual(rec21["note"], "G5")
        self.assertEqual(rec21["frequency_hz"], 783.99)
        self.assertIn("Land/Cloud", rec21["confidence"])

    def test_ingest_sample_member3_mapped_json(self):
        json_path = PROJECT_ROOT / "examples" / "sample_member3_mapped.json"
        records = member4_adapter.parse_windspeed_records(json_path)

        self.assertEqual(len(records), 5)
        self.assertEqual(records[0]["region_id"], "CELL_01")
        self.assertEqual(records[3]["windspeed_mps"], 26.5)
        self.assertEqual(records[3]["note"], "D5")
        self.assertEqual(records[4]["windspeed_mps"], 38.0)
        self.assertEqual(records[4]["note"], "G5")

    def test_ingest_legacy_member4_json(self):
        json_path = PROJECT_ROOT / "examples" / "sample_regions.json"
        records = member4_adapter.parse_windspeed_records(json_path)

        self.assertEqual(len(records), 5)
        self.assertEqual(records[0]["region_name"], "A")
        self.assertEqual(records[0]["windspeed_mps"], 3.0)
        self.assertEqual(records[0]["note"], "C4")


class TestAudioPropertiesAndMetadata(unittest.TestCase):
    """Test audio synthesis duration, format, and RIFF comment chunk embedding/extraction."""

    def test_wav_format_and_duration_formula(self):
        records = [
            {"region_id": "R1", "speed": 4.0},
            {"region_id": "R2", "speed": 12.0},
            {"region_id": "R3", "speed": 38.0},
        ]
        parsed = member4_adapter.parse_windspeed_records(records)
        wav_bytes, synced = member4_adapter.sonify_records(parsed, embed_metadata=True)

        # 3 tones of 0.45s + 2 gaps of 0.08s = 1.35 + 0.16 = 1.51s
        expected_samples = 3 * int(round(0.45 * 44100)) + 2 * int(round(0.08 * 44100))
        expected_duration = expected_samples / 44100.0

        with wave.open(io.BytesIO(wav_bytes), "rb") as w:
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getsampwidth(), 2)  # 16-bit
            self.assertEqual(w.getframerate(), 44100)
            self.assertEqual(w.getnframes(), expected_samples)

        # Verify start times
        self.assertEqual(synced[0]["tone_start_seconds"], 0.0)
        self.assertEqual(synced[1]["tone_start_seconds"], round(0.45 + 0.08, 4))
        self.assertEqual(synced[2]["tone_start_seconds"], round(2 * (0.45 + 0.08), 4))

    def test_riff_metadata_embedding_and_recovery(self):
        records = member4_adapter.parse_windspeed_records(
            [{"region_id": "META_TEST", "speed": 22.0}]
        )
        wav_bytes, _ = member4_adapter.sonify_records(records, embed_metadata=True)

        comment = member4_adapter.extract_riff_comment(wav_bytes)
        self.assertIsNotNone(comment)
        self.assertIn("META_TEST", comment)
        self.assertIn("C5", comment)

        # Standard reader must read file without issue
        rate, pcm = scipy.io.wavfile.read(io.BytesIO(wav_bytes))
        self.assertEqual(rate, 44100)
        self.assertTrue(len(pcm) > 0)


class TestExportFiles(unittest.TestCase):
    """Test CSV and JSON export functions meet contract."""

    def test_csv_export_schema(self):
        records = member4_adapter.parse_windspeed_records(
            [
                {"region_id": "EXP_01", "region_name": "Test Zone", "speed": 26.5, "row": 1, "col": 2, "confidence": "High Confidence"}
            ]
        )
        _, synced = member4_adapter.sonify_records(records)
        out_csv = PROJECT_ROOT / "outputs" / "test_export.csv"
        member4_adapter.export_records_csv(synced, out_csv)

        self.assertTrue(out_csv.exists())
        text = out_csv.read_text(encoding="utf-8")
        lines = text.strip().splitlines()
        self.assertEqual(len(lines), 2)  # header + 1 record
        header = lines[0].split(",")
        self.assertIn("record_index", header)
        self.assertIn("windspeed_mps", header)
        self.assertIn("note", header)
        self.assertIn("frequency_hz", header)
        self.assertIn("confidence", header)

        # Cleanup
        out_csv.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
