"""Configuration for Face Authentication Attendance System."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
DB_PATH = DATA_DIR / "attendance.db"

# Face recognition settings
FACE_MATCH_THRESHOLD = 0.5  # Lower = stricter (default 0.6 in face_recognition)
NUM_JITTERS = 1  # More jitters = more accurate but slower
MODEL = "hog"  # "hog" (faster) or "cnn" (more accurate, needs GPU)

# Spoof prevention (blink requires multiple frames; single snapshot uses lighting only)
REQUIRE_BLINK = False
BLINK_EAR_THRESHOLD = 0.25  # Eye aspect ratio threshold for blink
BLINK_FRAMES_REQUIRED = 2
MIN_BRIGHTNESS = 30  # Reject too-dark frames
MAX_BRIGHTNESS = 220  # Reject overexposed

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
EMBEDDINGS_DIR.mkdir(exist_ok=True)
