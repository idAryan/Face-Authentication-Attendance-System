"""Identify a face from camera frame against registered users."""
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import face_recognition
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FACE_MATCH_THRESHOLD, NUM_JITTERS, MODEL
from .face_registry import FaceRegistry
from .spoof_detection import SpoofDetector


class FaceIdentifier:
    """Identify faces in a frame against the registered user database."""

    def __init__(
        self,
        registry: Optional[FaceRegistry] = None,
        spoof_detector: Optional[SpoofDetector] = None,
        match_threshold: float = FACE_MATCH_THRESHOLD,
    ):
        self.registry = registry or FaceRegistry()
        self.spoof = spoof_detector or SpoofDetector()
        self.match_threshold = match_threshold
        self._encodings: List[np.ndarray] = []
        self._user_ids: List[str] = []
        self._names: List[str] = []
        self._refresh_encodings()

    def _refresh_encodings(self) -> None:
        """Reload encodings from registry."""
        self._encodings, self._user_ids, self._names = self.registry.get_all_encodings()

    def identify(
        self,
        frame_bgr: np.ndarray,
        run_spoof_check: bool = True,
        require_liveness: bool = True,
    ) -> Tuple[Optional[str], Optional[str], str, Optional[Tuple]]:
        """
        Identify the face in frame (BGR from OpenCV).
        Returns (user_id, name, message, face_box).
        face_box = (top, right, bottom, left) or None.
        """
        self._refresh_encodings()
        if not self._encodings:
            return None, None, "No users registered. Please register first.", None

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(
            rgb, model=MODEL, number_of_times_to_upsample=1
        )
        if not face_locations:
            return None, None, "No face detected. Look at the camera.", None

        if len(face_locations) > 1:
            return None, None, "Only one person should be in frame.", None

        face_loc = face_locations[0]
        face_landmarks_list = face_recognition.face_landmarks(rgb, face_locations)
        face_landmarks = face_landmarks_list[0] if face_landmarks_list else None

        if run_spoof_check:
            if require_liveness:
                self.spoof.reset_blink_state()
            passed, msg = self.spoof.verify_frame(frame_bgr, face_loc, face_landmarks)
            if not passed and require_liveness and self.spoof.require_blink:
                passed, msg = self.spoof.verify_frame(frame_bgr, face_loc, face_landmarks)
            if not passed:
                return None, None, msg, face_loc

        encodings = face_recognition.face_encodings(
            rgb, face_locations, num_jitters=NUM_JITTERS, model="small"
        )
        if not encodings:
            return None, None, "Could not encode face.", face_loc

        encoding = encodings[0]
        distances = face_recognition.face_distance(self._encodings, encoding)
        best_idx = int(np.argmin(distances))
        best_dist = float(distances[best_idx])

        if best_dist > self.match_threshold:
            return None, None, f"No match (distance {best_dist:.2f}). Register or try again.", face_loc

        return (
            self._user_ids[best_idx],
            self._names[best_idx],
            "Match found.",
            face_loc,
        )

    def identify_without_spoof(self, frame_bgr: np.ndarray) -> Tuple[Optional[str], Optional[str], str, Optional[Tuple]]:
        """Identify without spoof/liveness check (e.g. for demo or relaxed mode)."""
        return self.identify(frame_bgr, run_spoof_check=False, require_liveness=False)
