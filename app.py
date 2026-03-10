import io
import logging
import os
import re
from pathlib import Path

import numpy as np
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from keras.models import load_model
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class Config:
    IMG_SIZE: tuple[int, int] = (128, 128)
    MODEL_DIR: Path = Path("models")
    MODEL_PATH: Path = MODEL_DIR / "my_model.keras"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS: set[str] = {"png", "jpg", "jpeg", "bmp", "tiff"}
    GOOGLE_DRIVE_FILE_ID: str = os.getenv("GOOGLE_DRIVE_FILE_ID", "")
    GOOGLE_DRIVE_URL: str = os.getenv(
        "GOOGLE_DRIVE_URL",
        "https://drive.google.com/file/d/1PxmX6EQD7jJ0GVOztBT9-RSAZJOJfoTR/view?usp=sharing",
    )
    DOWNLOAD_ON_STARTUP: bool = os.getenv("DOWNLOAD_ON_STARTUP", "true").lower() == "true"
    LABELS: dict[int, str] = {0: "Parasitized", 1: "Uninfected"}


_model = None


def _extract_file_id(url: str) -> str:
    if not url:
        return ""
    for pattern in (r"/file/d/([a-zA-Z0-9_-]+)", r"[?&]id=([a-zA-Z0-9_-]+)"):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def _download_from_google_drive(file_id: str, destination: Path) -> None:
    # Use the newer usercontent endpoint which handles large-file confirmation
    url = f"https://drive.usercontent.google.com/download"
    params = {"id": file_id, "export": "download", "confirm": "t"}
    session = requests.Session()

    logger.info("Requesting file %s from Google Drive …", file_id)
    response = session.get(url, params=params, stream=True, timeout=300)
    response.raise_for_status()

    # Check that we got a binary file, not an HTML error page
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        # Fallback: try the legacy endpoint with confirm token
        logger.warning("Got HTML response, trying legacy endpoint …")
        legacy_url = "https://docs.google.com/uc"
        legacy_params = {"export": "download", "id": file_id, "confirm": "t"}
        response = session.get(legacy_url, params=legacy_params, stream=True, timeout=300)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise RuntimeError(
                "Google Drive returned an HTML page instead of the model file. "
                "Verify the file is shared publicly (Anyone with the link)."
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(".part")
    downloaded = 0

    with open(temp_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded % (5 * 1024 * 1024) < 1024 * 1024 or downloaded == len(chunk):
                    logger.info("Downloaded %.1f MB …", downloaded / (1024 * 1024))

    min_model_size = 50 * 1024  # 50 KB minimum for a valid .keras file
    if downloaded < min_model_size:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Downloaded file is too small ({downloaded} bytes) — Google Drive "
            "may have returned an error page. Verify the file is shared publicly."
        )

    temp_path.replace(destination)
    logger.info("Model saved → %s (%.1f MB)", destination, downloaded / (1024 * 1024))


def _ensure_model() -> None:
    if Config.MODEL_PATH.exists():
        return

    file_id = Config.GOOGLE_DRIVE_FILE_ID or _extract_file_id(Config.GOOGLE_DRIVE_URL)
    if not file_id:
        raise RuntimeError(
            "Model not found and no Google Drive source configured. "
            "Set GOOGLE_DRIVE_FILE_ID or GOOGLE_DRIVE_URL env var."
        )

    logger.info("Model not found locally — downloading from Google Drive …")
    _download_from_google_drive(file_id, Config.MODEL_PATH)


def _get_model():
    global _model
    if _model is None:
        _ensure_model()
        _model = load_model(Config.MODEL_PATH)
        logger.info("Model loaded successfully")
    return _model


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def _preprocess(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(Config.IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    CORS(app)

    if Config.DOWNLOAD_ON_STARTUP:
        # Ensure model file exists on first run before any request arrives.
        _ensure_model()

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "model_loaded": _model is not None,
            "model_on_disk": Config.MODEL_PATH.exists(),
        })

    @app.post("/predict")
    def predict():
        if "file" not in request.files:
            return jsonify({"error": "Missing 'file' in form-data"}), 400

        file = request.files["file"]
        if not file or file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not _allowed_file(file.filename):
            allowed = ", ".join(sorted(Config.ALLOWED_EXTENSIONS))
            return jsonify({"error": f"File type not allowed. Accepted: {allowed}"}), 400

        image_bytes = file.read()
        if not image_bytes:
            return jsonify({"error": "Uploaded file is empty"}), 400

        try:
            model = _get_model()
            arr = _preprocess(image_bytes)
            score = float(model.predict(arr, verbose=0)[0][0])

            is_parasitized = score < 0.5
            label = Config.LABELS[0] if is_parasitized else Config.LABELS[1]
            confidence = (1.0 - score) if is_parasitized else score

            return jsonify({
                "label": label,
                "confidence": round(confidence, 6),
                "parasitized_probability": round(1.0 - score, 6),
                "uninfected_probability": round(score, 6),
            })
        except Exception as exc:
            logger.exception("Prediction failed")
            return jsonify({"error": str(exc)}), 500

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
