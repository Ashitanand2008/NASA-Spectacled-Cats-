"""Automated local verification test for NASA Earth Information Jukebox (Member 5).

Runs comprehensive checks on the Vercel serverless entrypoint, Flask routes,
static asset serving, API health, and NASA image-to-audio sonification.
"""

import base64
import io
import sys
import unittest
import wave
from pathlib import Path
from PIL import Image

# Ensure current folder and api are on sys.path
MEMBER5_DIR = Path(__file__).resolve().parent
if str(MEMBER5_DIR) not in sys.path:
    sys.path.insert(0, str(MEMBER5_DIR))

API_DIR = MEMBER5_DIR / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import index


class TestVercelAppReadiness(unittest.TestCase):
    """Test suite verifying Vercel readiness of the Member 5 Flask application."""

    def setUp(self):
        self.client = index.app.test_client()

    def test_01_serverless_entrypoint_exists(self):
        """Verify api.index exports a valid WSGI Flask application."""
        self.assertIsNotNone(index.app)
        self.assertEqual(index.app.name, "app")

    def test_02_homepage_serves_html(self):
        """Verify GET / returns HTTP 200 with HTML frontend content."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Earth Jukebox", res.data)
        self.assertIn(b"cssN.css", res.data)

    def test_03_static_assets_exist_and_serve(self):
        """Verify stylesheet and React/JS bundles are accessible."""
        res_css = self.client.get("/cssN.css")
        self.assertEqual(res_css.status_code, 200)
        self.assertTrue(len(res_css.data) > 10000)

        res_js = self.client.get("/javaN.js")
        self.assertEqual(res_js.status_code, 200)
        self.assertTrue(len(res_js.data) > 10000)

    def test_04_api_health_check(self):
        """Verify GET /api/health loads all 5 required member modules."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "running")
        modules = data.get("modules", {})
        for mod_name in ["integration_adapter", "member4_adapter", "nasa2py", "sonification", "windspeed_mapper"]:
            self.assertTrue(modules.get(mod_name), f"Module {mod_name} failed to load.")

    def test_05_image_processing_and_audio_synthesis(self):
        """Verify POST /api/process processes an image and generates playable WAV audio."""
        # Create a synthetic 100x100 RGB image with NASA Cyan color (7.0 m/s)
        img = Image.new("RGB", (100, 100), color=(40, 180, 220))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        res = self.client.post(
            "/api/process",
            data={"image": (buf, "satellite_wind.png")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(len(data.get("values", [])), 25)

        # Decode base64 audio and verify WAV container properties
        audio_b64 = data.get("audio", "")
        self.assertTrue(len(audio_b64) > 1000)
        wav_bytes = base64.b64decode(audio_b64)

        with wave.open(io.BytesIO(wav_bytes), "rb") as w:
            self.assertEqual(w.getnchannels(), 1)      # Mono
            self.assertEqual(w.getsampwidth(), 2)     # 16-bit
            self.assertEqual(w.getframerate(), 44100) # 44.1 kHz
            self.assertTrue(w.getnframes() > 0)

    def test_06_error_handling_missing_image(self):
        """Verify POST /api/process rejects requests without an image."""
        res = self.client.post("/api/process", data={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
