"""NASA Earth Information Center — Earth Jukebox.

Member 5 Flask Application with robust Vercel Serverless Function compatibility.
"""

import base64
import os
import sys
import threading
from pathlib import Path

from flask import Flask, request, jsonify, redirect, Response


# Project base folder
BASE_DIR = Path(__file__).resolve().parent

# Ensure Member_5 directory is in Python search path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# Serve the existing frontend static assets
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "public"),
    static_url_path=""
)


# Vercel request size limit (4.5 MB payload limit)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024


# WSGI Middleware to restore clean PATH_INFO when Vercel rewrites requests
class VercelPathFixMiddleware:
    """WSGI middleware ensuring proper PATH_INFO routing on Vercel serverless."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_VERCEL_FORWARDED_PATH")
            or environ.get("RAW_URI")
            or environ.get("REQUEST_URI")
        )
        if matched_path:
            clean_path = matched_path.split("?")[0]
            current_path = environ.get("PATH_INFO", "")
            if current_path in (
                "/api/index.py",
                "/api/index",
                "/api/process.py",
                "/api/process",
                "/api/health.py",
                "/api/health",
                "/index.py",
            ):
                environ["PATH_INFO"] = clean_path

        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)


# Attach CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# Prevent simultaneous pipeline executions in the same serverless worker
pipeline_lock = threading.Lock()


# HOME PAGE (GET /) & POST FALLBACK
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Fallback in case a rewrite forwarded POST /api/process to /
        return process_image()
    if (BASE_DIR / "public" / "index.html").exists():
        return app.send_static_file("index.html")
    return redirect("/index.html")


# CHECK BACKEND CONNECTION (Supports multiple routing aliases)
@app.route("/api/health", methods=["GET", "POST", "OPTIONS"])
@app.route("/health", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/health.py", methods=["GET", "POST", "OPTIONS"])
def health():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if request.method == "POST":
        return jsonify({"error": "Method POST not allowed for health check."}), 405

    modules = {}
    for module in [
        "integration_adapter",
        "member4_adapter",
        "windspeed_mapper",
        "sonification",
        "nasa2py"
    ]:
        try:
            __import__(module)
            modules[module] = True
        except Exception:
            modules[module] = False

    return jsonify({
        "status": "running",
        "modules": modules
    })


# PROCESS UPLOADED NASA IMAGE (Supports multiple routing aliases)
@app.route("/api/process", methods=["GET", "POST", "OPTIONS"])
@app.route("/process", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/process.py", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/index.py", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/index", methods=["GET", "POST", "OPTIONS"])
def process_image():
    # CORS preflight response
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if request.method == "GET":
        return jsonify({
            "error": "Method GET not allowed for /api/process. Please send a POST request with a multipart image."
        }), 405

    if "image" not in request.files:
        return jsonify({
            "error": "Please upload an image."
        }), 400

    image = request.files["image"]

    if image.filename == "":
        return jsonify({
            "error": "No image selected."
        }), 400

    allowed_extensions = {"png", "jpg", "jpeg"}
    extension = image.filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        return jsonify({
            "error": "Only PNG and JPG images are supported."
        }), 400

    image_bytes = image.read()

    if not image_bytes:
        return jsonify({
            "error": "The uploaded image is empty."
        }), 400

    try:
        # Import backend integration
        import integration_adapter

        # Locate NASA scientific colour legend
        legend_candidates = [
            BASE_DIR / "nasa_legend.csv",
            Path(__file__).resolve().parent / "nasa_legend.csv",
            BASE_DIR.parent / "member_3" / "nasa_legend.csv",
            Path(os.getcwd()) / "nasa_legend.csv",
        ]
        legend_file = None
        for cand in legend_candidates:
            if cand.is_file():
                legend_file = cand
                break

        # Run team backend pipeline under concurrency lock
        with pipeline_lock:
            results = integration_adapter.run_full_pipeline(
                source_type="image",
                input_data=image_bytes,
                legend_path=legend_file,
                include_low_confidence=True,
                embed_metadata=True
            )

        # Get processed records and audio
        records = results["records"]
        wav_bytes = results["wav_bytes"]

        # Convert audio to Base64
        audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

        # Extract windspeed values
        values = [
            record["windspeed_mps"]
            for record in records
        ]

        return jsonify({
            "success": True,
            "audio": audio_base64,
            "values": values,
            "unit": "m/s",
            "description": "Windspeed values extracted from your NASA image.",
            "stats": results["stats"],
            "warnings": results["warnings"]
        })

    except Exception as error:
        app.logger.exception("Image processing failed")
        return jsonify({
            "error": f"Processing failed: {str(error)}"
        }), 500


# JSON ERROR HANDLERS (Ensures /api/ endpoints never return HTML on errors)
@app.errorhandler(400)
def handle_400(error):
    msg = getattr(error, "description", "Bad Request")
    return jsonify({"error": str(msg)}), 400


@app.errorhandler(404)
def handle_404(error):
    if request.path.startswith("/api") or request.path.endswith(".py"):
        return jsonify({"error": f"Endpoint not found: {request.path}"}), 404
    # For web browser frontend navigation, fallback to index.html if present
    if (BASE_DIR / "public" / "index.html").exists():
        return app.send_static_file("index.html")
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def handle_405(error):
    if request.path.startswith("/api") or request.path.endswith(".py"):
        return jsonify({"error": f"Method {request.method} not allowed for {request.path}"}), 405
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "Image is too large. Please upload an image smaller than 4 MB."
    }), 413


@app.errorhandler(500)
def handle_500(error):
    return jsonify({
        "error": "An internal server error occurred during processing."
    }), 500


# RUN LOCALLY
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
